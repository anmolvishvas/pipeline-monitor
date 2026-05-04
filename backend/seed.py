from django.contrib.auth.models import User
from pipeline.models import Job, Stage, LogEvent

LogEvent.objects.all().delete()
Stage.objects.all().delete()
Job.objects.all().delete()

user = User.objects.first()

def create_job(name, scenario):
    job = Job.objects.create(name=name, created_by=user)

    s1 = Stage.objects.create(job=job, name="Ingest", order=1, status="pending")
    s2 = Stage.objects.create(job=job, name="Validate", order=2, status="pending")
    s3 = Stage.objects.create(job=job, name="Export", order=3, status="pending")

    if scenario == "queued":
        job.status = "queued"

    elif scenario == "running":
        job.status = "running"
        s1.status = "done"
        s1.save()
        LogEvent.objects.create(stage=s1, level="info", message="Ingest done")

        s2.status = "running"
        s2.save()
        LogEvent.objects.create(stage=s2, level="info", message="Validation running")

    elif scenario == "completed":
        job.status = "completed"
        for s in [s1, s2, s3]:
            s.status = "done"
            s.save()
            LogEvent.objects.create(stage=s, level="info", message=f"{s.name} done")

    elif scenario == "failed":
        job.status = "failed"
        s1.status = "done"
        s1.save()
        LogEvent.objects.create(stage=s1, level="info", message="Ingest done")

        s2.status = "failed"
        s2.save()
        LogEvent.objects.create(stage=s2, level="error", message="Validation failed")

    job.save()


create_job("Payment Processing", "queued")
create_job("User Import Pipeline", "running")
create_job("Data Warehouse Load", "completed")
create_job("Email Campaign Sync", "failed")
create_job("Analytics ETL", "queued")

for j in Job.objects.all():
    print(j.name, j.stages.count())