from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser


# from apps.text_annotation.models.plan_text_validation import TextValidationType
# from apps.text_annotation.serializers.plan_text_validation import ValidationTypeSerializer


class TextValidationTypeView(generics.ListCreateAPIView):
    # serializer_class=ValidationTypeSerializer
    serializer_class = None
    permission_classes = [IsAuthenticated,IsAdminUser]
    # query_set=TextValidationType.objects.all()

