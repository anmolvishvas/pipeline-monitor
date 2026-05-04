from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.db import transaction
from django.db.models import Count, Q, OuterRef, Subquery, Prefetch, Sum

from django.utils import timezone

from .models import Job, Stage, LogEvent
from .serializers import (
    JobCreateSerializer,
    JobListSerializer,
    LogEventSerializer
)

from .permissions import IsOperator, IsViewer

class JobListView(APIView):

    permission_classes = [IsViewer]

    def get(self, request):
        queryset = Job.objects.annotate(
            stage_count=Count('stages'),

            error_count=Count(
                'stages__logs',
                filter=Q(stages__logs__level='error')
            ),

            current_stage=Subquery(
                Stage.objects.filter(
                    job=OuterRef('pk'),
                    status='running'
                ).values('name')[:1]
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

        stages_data = serializer.validated_data['stages']

        for stage in stages_data:
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

        if job.status != 'queued':
            return Response(
                {"error": "Job not in queued state"},
                status=400
            )

        job.status = 'running'
        job.started_at = timezone.now()
        job.save()

        first_stage = job.stages.order_by('order').first()
        first_stage.status = 'running'
        first_stage.save()

        return Response({"status": "triggered"})
    
class JobStagesView(APIView):

    permission_classes = [IsViewer]

    def get(self, request, pk):
        job = Job.objects.get(pk=pk)

        latest_logs_subquery = LogEvent.objects.filter(
            stage=OuterRef('pk')
        ).order_by('-timestamp').values('pk')[:3]

        stages = Stage.objects.filter(job=job).prefetch_related(
            Prefetch(
                'logs',
                queryset=LogEvent.objects.filter(
                    pk__in=Subquery(latest_logs_subquery)
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
    def post(self, request, stage_id):
        stage = Stage.objects.select_for_update().get(pk=stage_id)

        log = LogEvent.objects.create(
            stage=stage,
            level=request.data.get('level'),
            message=request.data.get('message')
        )

        if log.level == 'error':
            stage.status = 'failed'
            stage.save()

            job = stage.job
            job.status = job.compute_status()
            job.save()

        return Response({"id": log.id}, status=201)
    

class JobSummaryView(APIView):

    permission_classes = [IsViewer]

    def get(self, request, pk):
        job = Job.objects.get(pk=pk)

        stages = Stage.objects.filter(job=job)

        total_duration = stages.aggregate(
            total=Sum('duration_ms')
        )['total']

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