from apps.dashboard.models.batch_join import BatchJoinRequest
from rest_framework import serializers
# from apps.project_management.models.batch import Batchfrom apps.dashboard.models.batch_join import BatchJoinRequest

class BatchJoinRequestSerializer(serializers.ModelSerializer):
    batch_name = serializers.CharField(source="batch.batch_name", read_only=True)
    # email = serializers.EmailField(source="email", read_only=True)
    # first_name = serializers.CharField(source="first_name", read_only=True)
    # last_name = serializers.CharField(source="last_name", read_only=True)
    
    class Meta:
        model = BatchJoinRequest
        fields = ["id", "batch", "batch_name", "status", "created_at", "updated_at", "email", "first_name", "last_name"]

