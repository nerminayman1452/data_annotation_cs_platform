from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qualification_test.filters.exam import ExamFilter
from apps.qualification_test.models.exam import Exam
from apps.qualification_test.serializers.exam import ExamSerializer, QuestionBankUploadSerializer


class ExamViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'exam_id'
    filter_backends = [DjangoFilterBackend]
    filterset_class = ExamFilter

    def get_queryset(self):
        #todo profile
        try:
            profile = Profile.objects.get(user_id=self.request.user.id)
            return Exam.objects.filter(owner=profile)
        except Exception:
            return Exam.objects.none()

    def perform_create(self, serializer):
        #todo profile
        profile = Profile.objects.get(user_id=self.request.user.id)
        serializer.save(owner=profile)




class QuestionBankUploadView(APIView):
    # permission_classes = [permissions.IsAdminUser]  # Admin-only access
    @extend_schema(
        request=QuestionBankUploadSerializer,
        description="Upload a CSV, XLSX, or JSON file containing questions for question bank.",
    )
    def post(self, request, *args, **kwargs):
        serializer = QuestionBankUploadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        result = serializer.save()

        return Response(
            {"message": "Question bank uploaded successfully", "data": result},
            status=status.HTTP_201_CREATED
        )
