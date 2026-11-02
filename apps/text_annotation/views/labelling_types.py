from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser


# from apps.text_annotation.models.plan_text_labelling import TextLabelType, TextSentenceType, TextErrorType
# from apps.text_annotation.serializers.plan_text_labelling import LabellingTypeSerializer, SentenceTypeSerializer, \
#     ErrorTypeSerializer

class TextLabelTypeView(generics.ListCreateAPIView):
    # serializer_class=LabellingTypeSerializer
    permission_classes = [IsAuthenticated,IsAdminUser]
    # query_set=TextLabelType.objects.all()

class TextSentenceTypeView(generics.ListCreateAPIView):
    # serializer_class=SentenceTypeSerializer
    permission_classes = [IsAuthenticated,IsAdminUser]
    # query_set=TextSentenceType.objects.all()

class TextErrorTypeView(generics.ListCreateAPIView):
    # serializer_class=ErrorTypeSerializer
    permission_classes = [IsAuthenticated,IsAdminUser]
    # query_set=TextErrorType.objects.all()
