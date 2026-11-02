from rest_framework import serializers

from apps.qualification_test.models.exam import ExamBatchMembers


class ExamBatchMembersSerializer(serializers.ModelSerializer):
    # profile = ProfileSerializer(read_only=True)
    can_open_exam = serializers.BooleanField(read_only=True)

    class Meta:
        model = ExamBatchMembers
        fields = '__all__'
