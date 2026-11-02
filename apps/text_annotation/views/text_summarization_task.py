from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.project_management.models.plan_members import PlanMember
from unused_scripts.text_task_generator import BaseTaskGenerator
# from apps.text_annotation.models.plan_text_summarization import PlanSummarizationConfig
from apps.text_annotation.models.task_text_summarization import TextSummarizationTaskResult
from apps.text_annotation.serializers.text_summarization_task import GenerateTextSummarizationTaskSerializer


class TextSummarizationTasksAPIView(ListCreateAPIView):
    serializer_class=GenerateTextSummarizationTaskSerializer
    permission_classes = [IsAuthenticated]
    queryset=TextSummarizationTaskResult.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = GenerateTextSummarizationTaskSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        batch = serializer.validated_data['batch']
        plan_summarization = serializer.validated_data['plan']

        plan_config = PlanSummarizationConfig.objects.get(id=plan_summarization.plan_labelling_conf_id.id)
        annotators = PlanMember.objects.filter(batch=batch.id, user_role='Annotator')
        batch_data_list = BatchData.objects.filter(batch=batch.id, plan_labelling=plan_summarization.id)

        generator = BaseTaskGenerator(
            batch=batch,
            plan=plan_summarization,
            plan_config=plan_config,
            annotators=annotators,
            model_refs={"task_model": TextSummarizationTaskResult}
        )
        created_tasks = generator.generate_tasks(batch_data_list)

        tasks_serializer = GenerateTextSummarizationTaskSerializer(created_tasks, many=True)

        return Response(
            {
                "message": f"Successfully created {len(created_tasks)} tasks.",
                "tasks": tasks_serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    def get(self, request, *args, **kwargs):
        batch_id = kwargs.get('batch_id')
        plan_id = kwargs.get('plan_id')

        if not batch_id or not plan_id:
            return Response({"detail": "batch_id and plan_id are required in the URL."},
                            status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(
            batch_data__batch_id=batch_id,
            plan_id=plan_id
        )
        if not queryset.exists():
            return Response(
                {"message":"There's no Tasks generated yet!"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



