from rest_framework import serializers

from apps.project_management.models.batch import BatchStatusHistory


class BatchStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchStatusHistory
        fields = ['id', 'batch', 'status', 'started_at', 'ended_at',]
