# from rest_framework import serializers

# from apps.project_management.models import BatchMembers, Batch
# from services.auth_service.client import get_user_info
# # from apps.user_management.models import UserProfile
# # from apps.user_management.serializers.profile import ProfileSerializer


# class BatchMembersSerializer(serializers.ModelSerializer):
#     # profile = ProfileSerializer(read_only=True)
#     # profile_id = serializers.PrimaryKeyRelatedField(
#     #     queryset=UserProfile.objects.all(),
#     #     source='profile',
#     #     write_only=True
#     # )
#     # profile = serializers.ListField(
#     #     child=serializers.IntegerField(),
#     #     allow_empty=False
#     # )
#     role = serializers.ChoiceField(choices=[("Annotator", "Annotator"), ("Reviewer", "Reviewer")])

#     class Meta:
#         model = BatchMembers
#         fields = ['id', 'batch', 'profile', 'role']
#         extra_kwargs = {
#             'batch': {'read_only': True},
#             'user_role': {'required': True},
#         }

#     def validate(self, attrs):
#         request = self.context.get('request')
#         batch = self.context.get('batch')

#         # If batch not in context (like in update), get it from instance
#         if not batch and self.instance:
#             batch = self.instance.batch

#         if not batch:
#             raise serializers.ValidationError("Batch cannot be empty.")

#         if isinstance(batch, int):
#             if not Batch.objects.filter(id=batch).exists():
#                 raise serializers.ValidationError("There's no batch with this ID!")
#             batch = Batch.objects.get(id=batch)

#         user = request.user
#         profile = attrs.get('profile', getattr(self.instance, 'profile', None))
#         token = request.headers.get("Authorization", "").split(" ")[-1]

#         if not Batch.objects.filter(id=batch.id).exists():
#             raise serializers.ValidationError("There's no batch with this ID!")

#         if batch.created_by != int(user.id):
#             raise serializers.ValidationError("You are not authorized to assign members in this batch.")

#         user_info = get_user_info(profile, token)
#         if user_info is None:
#             raise serializers.ValidationError("This user does not exist or is not accessible.")

#         attrs['batch'] = batch  # inject batch
#         return attrs


#     def create(self, validated_data):
#         return BatchMembers.objects.create(**validated_data)

#     def update(self, instance, validated_data):
#         user = self.context['request'].user

#         if instance.batch.created_by != int(user.id):
#             raise serializers.ValidationError("You are not authorized to update this member.")

#         # Only allow changing the user_role
#         instance.user_role = validated_data.get('user_role', instance.user_role)
#         instance.save()
#         return instance