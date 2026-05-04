from rest_framework import serializers
from .models import Job, Stage, LogEvent


class StageCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    order = serializers.IntegerField()


class JobCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    stages = StageCreateSerializer(many=True)


class JobListSerializer(serializers.ModelSerializer):
    stage_count = serializers.IntegerField()
    error_count = serializers.IntegerField()
    current_stage = serializers.CharField(allow_null=True)
    retry_count = serializers.IntegerField()

    class Meta:
        model = Job
        fields = [
            'id',
            'name',
            'status',
            'stage_count',
            'error_count',
            'current_stage',
            'retry_count',
        ]


class LogEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEvent
        fields = '__all__'