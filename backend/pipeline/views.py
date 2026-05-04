from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db import transaction
from django.db.models import Count, Q, OuterRef, Subquery, Prefetch, Sum
from django.utils import timezone

from .models import Job, Stage, LogEvent
from .serializers import JobCreateSerializer, JobListSerializer, LogEventSerializer
from .permissions import IsOperator, IsViewer

import threading
import time

class JobListView(APIView):
    permission_classes = [IsViewer]

    def get(self, request):
        queryset = Job.objects.annotate(
            stage_count=Count('stages'),
            error_count=Count('stages__logs', filter=Q(stages__logs__level='error')),
            current_stage=Subquery(
                Stage.objects.filter(job=OuterRef('pk'), status='running')
                .values('name')[:1]
            )
        )

        serializer = JobListSerializer(queryset, many=True)
        return Response(serializer.data)


class JobCreateView(APIView):
    permission_classes = [IsOperator]

    @transaction.atomic
    def post(self, request):
        serializer = JobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = Job.objects.create(
            name=serializer.validated_data['name'],
            created_by=request.user
        )

        for stage in serializer.validated_data['stages']:
            Stage.objects.create(
                job=job,
                name=stage['name'],
                order=stage['order']
            )

        return Response({"id": job.id}, status=201)


class JobTriggerView(APIView):
    permission_classes = [IsOperator]

    @transaction.atomic
    def post(self, request, pk):
        job = Job.objects.select_for_update().get(pk=pk)

        if job.status not in ['queued', 'failed']:
            return Response({"error": "Invalid state"}, status=400)

        if job.status == 'failed':
            job.retry_count += 1

        job.status = 'running'
        job.started_at = timezone.now()
        job.save()

        first_stage = job.stages.order_by('order').first()
        if not first_stage:
            return Response({"error": "Job has no stages"}, status=400)

        first_stage.status = 'running'
        first_stage.save()
        import threading
        threading.Thread(target=simulate_pipeline, args=(job.id,)).start()

        return Response({"status": "triggered"})


class JobStagesView(APIView):
    permission_classes = [IsViewer]

    def get(self, request, pk):
        job = Job.objects.get(pk=pk)

        latest_logs = LogEvent.objects.filter(
            stage=OuterRef('pk')
        ).order_by('-timestamp').values('pk')[:3]

        stages = Stage.objects.filter(job=job).prefetch_related(
            Prefetch(
                'logs',
                queryset=LogEvent.objects.filter(
                    pk__in=Subquery(latest_logs)
                ).order_by('-timestamp')
            )
        )

        data = []
        for stage in stages:
            data.append({
                "id": stage.id,
                "name": stage.name,
                "status": stage.status,
                "logs": LogEventSerializer(stage.logs.all(), many=True).data
            })

        return Response(data)


class StageLogCreateView(APIView):
    permission_classes = [IsOperator]

    @transaction.atomic
    def post(self, request, pk):
        stage = Stage.objects.select_related('job').get(pk=pk)

        level = request.data.get('level')
        message = request.data.get('message')

        LogEvent.objects.create(
            stage=stage,
            level=level,
            message=message
        )

        job = stage.job

        if level == 'error':
            stage.status = 'failed'
            stage.save()

            job.status = job.compute_status()
            job.save()

        elif level == 'info':
            if stage.status == 'pending':
                stage.status = 'running'
                stage.save()

                job.status = job.compute_status()
                job.save()

            elif stage.status == 'running':
                stage.status = 'done'
                stage.save()

                next_stage = Stage.objects.filter(
                    job=job,
                    order__gt=stage.order
                ).order_by('order').first()

                if next_stage:
                    next_stage.status = 'running'
                    next_stage.save()
                else:
                    job.status = 'completed'
                    job.save()

        return Response({"status": "log created"})


class JobSummaryView(APIView):
    permission_classes = [IsViewer]

    def get(self, request, pk):
        job = Job.objects.get(pk=pk)

        stages = Stage.objects.filter(job=job)

        total_duration = stages.aggregate(total=Sum('duration_ms'))['total']

        error_count = LogEvent.objects.filter(
            stage__job=job,
            level='error'
        ).count()

        total_logs = LogEvent.objects.filter(stage__job=job).count()

        error_rate = (error_count / total_logs) if total_logs else 0

        return Response({
            "total_duration": total_duration,
            "error_rate": error_rate
        })


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = "operator" if request.user.username == "operator@test.com" else "viewer"
        return Response({
            "username": request.user.username,
            "role": role
        })

def simulate_pipeline(job_id):
    from .models import Job, Stage, LogEvent

    job = Job.objects.get(pk=job_id)
    stages = job.stages.order_by('order')

    for stage in stages:
        stage.status = 'running'
        stage.save()

        for i in range(3):
            LogEvent.objects.create(
                stage=stage,
                level="info",
                message=f"{stage.name} step {i+1}"
            )
            time.sleep(2)

        if stage.name.lower() == "validate":
            LogEvent.objects.create(
                stage=stage,
                level="error",
                message="Validation failed"
            )

            stage.status = 'failed'
            stage.save()

            job.status = job.compute_status()
            job.save()
            return

        stage.status = 'done'
        stage.save()

    job.status = 'completed'
    job.save()