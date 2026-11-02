from rest_framework import serializers

class InitialAssignSerializer(serializers.Serializer):
    batch_id = serializers.IntegerField()