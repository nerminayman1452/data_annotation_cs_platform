from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.project_management.models.plan_members import PlanMember
from apps.project_management.models.text_plan import TextPlanRawData
from unused_scripts.text_task_generator import BaseTaskGenerator
# from apps.text_annotation.models.plan_text_validation import PlanValidationConfig
from apps.text_annotation.models.task_text_validation import TextValidationTaskResult
from apps.text_annotation.serializers.text_validation_task import GenerateTextValidationTaskSerializer


class TextValidationTasksAPIView(ListCreateAPIView):
    serializer_class=GenerateTextValidationTaskSerializer
    permission_classes = [IsAuthenticated]
    queryset=TextValidationTaskResult.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = GenerateTextValidationTaskSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        batch = serializer.validated_data['batch']
        plan_validation = serializer.validated_data['plan']

        plan_config = PlanValidationConfig.objects.get(id=plan_validation.plan_validation_conf_id.id)
        annotators = PlanMember.objects.filter(batch=batch.id, user_role='Annotator')
        batch_data_list = TextPlanRawData.objects.filter(batch=batch.id, plan_validation=plan_validation.id)

        generator = BaseTaskGenerator(
            batch=batch,
            plan=plan_validation,
            plan_config=plan_config,
            annotators=annotators,
            model_refs={"task_model": TextValidationTaskResult}
        )
        created_tasks = generator.generate_tasks(batch_data_list)

        tasks_serializer = GenerateTextValidationTaskSerializer(created_tasks, many=True)

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



