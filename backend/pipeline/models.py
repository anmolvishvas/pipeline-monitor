import uuid
from django.db import models
from django.contrib.auth.models import User


class Job(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    retry_count = models.IntegerField(default=0)

    def compute_status(self):
        stages = self.stages.all()

        if any(s.status == 'failed' for s in stages):
            return 'failed'

        if all(s.status == 'done' for s in stages):
            return 'completed'

        if any(s.status == 'running' for s in stages):
            return 'running'

        return 'queued'


class Stage(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='stages')

    name = models.CharField(max_length=255)
    order = models.IntegerField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    duration_ms = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('job', 'order')
        ordering = ['order']

class LogEvent(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name='logs')

    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    message = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']