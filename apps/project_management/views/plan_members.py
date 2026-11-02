from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema

from apps.project_management.models.plan_members import PlanMember
from apps.project_management.serializers.plan_members import PlanMembersSerializer, PlanMembersBulkSerializer
from services.auth_service.client import get_user_info

# --- Abstract Base View ---

class BasePlanMemberView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    
    # Must be set by Child Class
    plan_model = None 

    def get_plan(self):
        """
        Fetch the specific TextPlan or ImagePlan based on URL kwargs.
        """
        return get_object_or_404(
            self.plan_model,
            id=int(self.kwargs["plan_id"])
            # You can add project ownership check here if needed
        )

    def get_queryset(self):
        """
        Filter PlanMembers by the specific ContentType and Object ID.
        """
        plan_id = int(self.kwargs["plan_id"])
        role = self.request.query_params.get("role")
        
        # Get ContentType for the specific model (TextPlan or ImagePlan)
        ct = ContentType.objects.get_for_model(self.plan_model)
        
        queryset = PlanMember.objects.filter(content_type=ct, object_id=plan_id)
        
        if role:
            queryset = queryset.filter(role=role)
            
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['plan'] = self.get_plan()
        return context

    # --- LIST (Optimized with Bulk User Info) ---
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        token = request.headers.get("Authorization", "").split(" ")[-1]
        
        # 1. Fetch all members from DB
        members = list(queryset)
        
        # 2. OPTIONAL: Optimize by fetching unique profile IDs first
        # profile_ids = list(set(m.profile for m in members))
        # user_map = fetch_bulk_users(profile_ids, token) # If Auth Service supports bulk
        
        # 3. Attach info manually (Standard loop approach)
        results = []
        for member in members:
            # Note: This loop calls Auth Service N times. 
            # If N is large, implement bulk endpoint in Auth Service.
            try:
                info = get_user_info(member.profile, token)
            except:
                info = {}
            
            results.append({
                "id": member.id,
                "profile": member.profile,
                "role": member.role,
                "user_info": info
            })

        return Response({
            "plan_id": int(self.kwargs["plan_id"]),
            "members": results
        })

    # --- CREATE (Bulk Add) ---
    def create(self, request, *args, **kwargs):
        plan = self.get_plan()
        
        # 1. Check Ownership
        if hasattr(plan, 'created_by') and plan.created_by != int(request.user.id):
             return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

        # 2. Validate Input
        serializer = PlanMembersBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        profiles = serializer.validated_data['profiles']
        role = serializer.validated_data['role']
        
        # 3. Filter Duplicates
        ct = ContentType.objects.get_for_model(self.plan_model)
        existing_ids = set(PlanMember.objects.filter(
            content_type=ct, 
            object_id=plan.id, 
            profile__in=profiles
        ).values_list('profile', flat=True))
        
        new_profiles = [p for p in profiles if p not in existing_ids]

        if not new_profiles:
            return Response({"detail": "All users are already in this plan."}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Bulk Create
        members_to_create = [
            PlanMember(plan=plan, profile=pid, role=role)
            for pid in new_profiles
        ]
        PlanMember.objects.bulk_create(members_to_create)

        return Response({
            "message": f"Added {len(members_to_create)} members.",
            "added_profiles": new_profiles
        }, status=status.HTTP_201_CREATED)

    @extend_schema(request=PlanMembersBulkSerializer)
    def post(self, request, *args, **kwargs):
        """HTTP POST wrapper that forwards to create() so drf-spectacular sees the schema."""
        return self.create(request, *args, **kwargs)


class BasePlanMemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PlanMembersSerializer
    plan_model = None # Set in child

    def get_queryset(self):
        plan_id = int(self.kwargs["plan_id"])
        ct = ContentType.objects.get_for_model(self.plan_model)
        return PlanMember.objects.filter(content_type=ct, object_id=plan_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # We manually fetch plan for context if needed for validation
        context['plan'] = get_object_or_404(self.plan_model, id=self.kwargs["plan_id"])
        return context


# --- Concrete Implementations ---

from apps.project_management.models.text_plan import TextPlan
from apps.project_management.models.image_plan import ImagePlan

# 1. Text Plan Members

@extend_schema(
    tags=['Text Plans'],
    description='List all members of a text plan or add new members',
    responses={
        200: PlanMembersSerializer(many=True),
        201: PlanMembersSerializer()
    }
)
class TextPlanMembersView(BasePlanMemberView):
    plan_model = TextPlan

@extend_schema(
    tags=['Text Plans'],
    description='Get, update, or delete a specific text plan member',
    responses={
        200: PlanMembersSerializer(),
        201: PlanMembersSerializer()
    }
)
class TextPlanMemberDetailView(BasePlanMemberDetailView):
    plan_model = TextPlan


# 2. Image Plan Members

@extend_schema(
    tags=['Image Plans'],
    description='List all members of an image plan or add new members',
    responses={
        200: PlanMembersSerializer(many=True),
        201: PlanMembersSerializer()
    }
)
class ImagePlanMembersView(BasePlanMemberView):
    plan_model = ImagePlan

@extend_schema(
    tags=['Image Plans'],
    description='Get, update, or delete a specific image plan member',
    responses={
        200: PlanMembersSerializer(),
        201: PlanMembersSerializer()
    }
)
class ImagePlanMemberDetailView(BasePlanMemberDetailView):
    plan_model = ImagePlan