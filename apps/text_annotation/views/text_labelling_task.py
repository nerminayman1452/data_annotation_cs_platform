from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.project_management.models.plan_members import PlanMember
from apps.project_management.models.text_plan import TextPlanRawData
# from apps.text_annotation.services.task_generator import BaseTaskGenerator
# from apps.text_annotation.models.plan_text_labelling import TextLabellingPlan, PlanLabellingConfig
from apps.text_annotation.models.task_text_labelling import TextLabellingTaskResult
from apps.text_annotation.serializers.text_labelling_task import GenerateTextLabellingTaskSerializer

class TextLabelingTasksAPIView(ListCreateAPIView):
    serializer_class=GenerateTextLabellingTaskSerializer
    permission_classes = [IsAuthenticated]
    queryset=TextLabellingTaskResult.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = GenerateTextLabellingTaskSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        #batch, plan instances
        batch = serializer.validated_data['batch']
        plan_labelling = serializer.validated_data['plan']
        # created_tasks = generate_text_labelling_tasks(batch_id=batch.id, plan_id=plan_labelling.id)

        plan_config = PlanLabellingConfig.objects.get(id=plan_labelling.plan_labelling_conf_id.id)
        annotators = PlanMember.objects.filter(batch=batch.id, user_role='Annotator')
        batch_data_list = TextPlanRawData.objects.filter(batch=batch.id, plan_labelling=plan_labelling.id)

        generator = BaseTaskGenerator(
            batch=batch,
            plan=plan_labelling,
            plan_config=plan_config,
            annotators=annotators,
            model_refs={"task_model": TextLabellingTaskResult}
        )
        created_tasks = generator.generate_tasks(batch_data_list)

        tasks_serializer = GenerateTextLabellingTaskSerializer(created_tasks, many=True)

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
                            status=status.HTTP_404_NOT_FOUND)

        if not TextLabellingPlan.objects.filter(id=plan_id, batch=batch_id).exists():
            return Response({"detail": "The plan ID is not exist."},
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



