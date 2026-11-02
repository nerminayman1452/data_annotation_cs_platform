from rest_framework import generics, status
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from apps.profile.models.profile import Profile
from rest_framework.exceptions import ValidationError

# Import plan-specific models/serializers for unified handling
from apps.project_management.models.image_plan import ImagePlan, ImagePlanRawData as ImagePlanRawDataModel
from apps.project_management.models.text_plan import TextPlan, TextPlanRawData as TextPlanRawDataModel
from apps.project_management.serializers.image_plan import ImagePlanRawDataSerializer as ImagePlanRawDataSerializer
from apps.project_management.serializers.text_plan import TextPlanRawDataSerializer as TextPlanRawDataSerializer
from apps.project_management.serializers.image_plan import ImagePlanRawDataQualitySerializer
from apps.project_management.serializers.text_plan import TextPlanRawDataQualitySerializer
from apps.project_management.utils.zip_handler import extract_zip_file

class BasePlanRawDataListCreateView(generics.ListCreateAPIView):
    """
    Abstract Base for listing and uploading raw files to a batch.
    Supports MULTIPLE file uploads.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] 

    # Define these in your subclass
    plan_model = None       
    data_model = None        
    serializer_class = None  

    def get_plan(self):
        return get_object_or_404(
            self.plan_model,
            id=int(self.kwargs["plan_id"]),
            created_by=int(self.request.user.id)
        )

    def get_queryset(self):
        self.get_plan() # Ensure permissions
        return self.data_model.objects.filter(
            plan_id=int(self.kwargs["plan_id"])
        ).order_by('-created_at')

    @extend_schema(
        summary="Upload Multiple Files",
        description="Upload multiple raw files to the specified batch.",
        # FIX: Define the request body explicitly for Swagger UI
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'array',          # <--- Critical: Array type
                        'items': {
                            'type': 'string',
                            'format': 'binary'    # <--- Critical: Binary format
                        }
                    }
                },
                'required': ['file']
            }
        },
        # FIX: Do NOT use 'serializer_class' here as it is None in the Base Class.
        # Removing 'responses' allows drf-spectacular to introspect the Child Class later.
    )
    def create(self, request, *args, **kwargs):
        """
        Overriding create to customize the response for multiple files.
        """
        # 1. Get the list of files (support multiple files and ZIP archives)
        # Note: 'file' must match the key used in Postman/Frontend
        raw_files = request.FILES.getlist('file')

        if not raw_files:
            return Response({"detail": "No files provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Expand ZIP files into individual uploaded file objects
        files = []
        for uploaded in raw_files:
            name = getattr(uploaded, 'name', '') or ''
            if name.lower().endswith('.zip'):
                try:
                    extracted = extract_zip_file(uploaded)
                    for _, ef in extracted.items():
                        files.append(ef)
                except Exception:
                    # If ZIP extraction fails, skip that file and continue
                    continue
            else:
                files.append(uploaded)

        # 2. Get the Plan
        plan = self.get_plan()

        # 3. Update Plan Status (Optional: Mark as in_progress)
        if hasattr(plan, 'status') and plan.status == 'pending':
             plan.status = 'in_progress'
             plan.save()

        # 4. Prepare data for Serializer validation
        # We pass the list of files directly because we defined `file` as ListField in Serializer
        data = {'file': files}
        
        # We will validate & create files one-by-one so we can return per-file
        # success and error details (ZIPs may contain mixed valid/invalid files).
        created_serialized, error_list = self.perform_create(plan, files)

        detail = f"Successfully uploaded {len(created_serialized)} files."
        payload = {"detail": detail, "uploaded": created_serialized}
        if error_list:
            payload["errors"] = error_list

        return Response(payload, status=status.HTTP_201_CREATED)

    def perform_create(self, plan, files):
        """
        Validate and create each file individually. Return (serialized_created_list, errors).
        """
        created_instances = []
        errors = []

        for f in files:
            # Validate each file using the serializer's validation logic
            temp_serializer = self.get_serializer(data={'file': [f]})
            if not temp_serializer.is_valid():
                # collect readable errors
                file_errors = temp_serializer.errors.get('file', temp_serializer.errors)
                errors.append(file_errors)
                continue

            # Create instance directly using model to handle multiple creations cleanly
            try:
                instance = self.data_model.objects.create(plan=plan, file=f, file_name=f.name)
                created_instances.append(instance)
            except Exception as e:
                errors.append(str(e))

        # Serialize created instances for response
        if created_instances:
            read_serializer = self.serializer_class(created_instances, many=True)
            return read_serializer.data, errors

        return [], errors


class BasePlanRawDataQualityUpdateView(generics.UpdateAPIView):
    """
    Abstract Base for updating quality of raw data files.
    Allows partial updates to the quality field.
    """
    permission_classes = [IsAuthenticated]
    
    # Define these in your subclass
    plan_model = None       
    data_model = None        
    serializer_class = None  

    def get_plan(self):
        return get_object_or_404(
            self.plan_model,
            # id=int(self.kwargs["plan_id"]),
            created_by=int(self.request.user.id)
        )

    def get_object(self):
        # Get user's profile_auth_id from Profile model
        try:
            profile = Profile.objects.get(user_id=int(self.request.user.id))
            profile_auth_id = profile.profile_auth_id
        except Profile.DoesNotExist:
            # If no profile found, user cannot access
            return None
            
        # Ensure user has permission to access the plan (creator or member)
        queryset = self.data_model.objects.filter(
            id=int(self.kwargs["pk"]),
            # plan_id=int(self.kwargs["plan_id"])
        ).filter(
            Q(plan__created_by=int(self.request.user.id)) | Q(plan__members__profile=profile_auth_id)
        )
        return get_object_or_404(queryset)

    @extend_schema(
        summary="Update Raw Data Quality",
        description="Update the quality status of a specific raw data file (good/bad).",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'quality': {
                        'type': 'string',
                        'enum': ['good', 'bad'],
                        'description': 'Quality status of the file'
                    }
                },
                'required': ['quality']
            }
        }
    )
    def patch(self, request, *args, **kwargs):
        """
        Handle PATCH requests for partial updates.
        """
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Update Raw Data Quality",
        description="Update the quality status of a specific raw data file (good/bad).",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'quality': {
                        'type': 'string',
                        'enum': ['good', 'bad'],
                        'description': 'Quality status of the file'
                    }
                },
                'required': ['quality']
            }
        }
    )
    def put(self, request, *args, **kwargs):
        """
        Handle PUT requests for full updates.
        """
        return super().put(request, *args, **kwargs)


@extend_schema(
    tags=["Plan Raw Data"],
    summary="Unified Upload Raw Data",
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'array',
                    'items': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            },
            'required': ['file']
    }
    },
    description="Upload raw files for a plan given its `plan_type` (e.g. 'image' or 'text').",
)
class UnifiedPlanRawDataUploadView(BasePlanRawDataListCreateView):
    """
    Unified upload endpoint that delegates to the appropriate plan model/serializer
    based on the `plan_type` path parameter. Supported types: 'image', 'text'.
    URL example: /.../plan/image/123/raw-data/
    """
    # Mapping of supported plan types to models/serializers
    _mapping = {
        'image': {
            'plan_model': ImagePlan,
            'data_model': ImagePlanRawDataModel,
            'serializer': ImagePlanRawDataSerializer
        },
        'text': {
            'plan_model': TextPlan,
            'data_model': TextPlanRawDataModel,
            'serializer': TextPlanRawDataSerializer
        }
    }

    def initial(self, request, *args, **kwargs):
        plan_type = str(self.kwargs.get('plan_type', '')).lower()
        if plan_type not in self._mapping:
            raise ValidationError({'plan_type': f"Unsupported plan type '{plan_type}'. Supported: {', '.join(self._mapping.keys())}"})

        cfg = self._mapping[plan_type]
        self.plan_model = cfg['plan_model']
        self.data_model = cfg['data_model']
        self.serializer_class = cfg['serializer']

        return super().initial(request, *args, **kwargs)


@extend_schema(
    tags=["Plan Raw Data"],
    summary="Unified Update Raw Data Quality",
    description="Update quality for a raw data item by `plan_type` (e.g. 'image' or 'text').",
)
class UnifiedPlanRawDataQualityUpdateView(BasePlanRawDataQualityUpdateView):
    """
    Unified endpoint to update raw-data quality for different plan types.
    URL example: /.../plan/image/raw-data/123/quality/ or /plan/text/raw-data/123/quality/
    """
    _mapping = {
        'image': {
            'plan_model': ImagePlan,
            'data_model': ImagePlanRawDataModel,
            'serializer': ImagePlanRawDataQualitySerializer
        },
        'text': {
            'plan_model': TextPlan,
            'data_model': TextPlanRawDataModel,
            'serializer': TextPlanRawDataQualitySerializer
        }
    }

    def initial(self, request, *args, **kwargs):
        plan_type = str(self.kwargs.get('plan_type', '')).lower()
        if plan_type not in self._mapping:
            raise ValidationError({'plan_type': f"Unsupported plan type '{plan_type}'. Supported: {', '.join(self._mapping.keys())}"})

        cfg = self._mapping[plan_type]
        self.plan_model = cfg['plan_model']
        self.data_model = cfg['data_model']
        self.serializer_class = cfg['serializer']

        return super().initial(request, *args, **kwargs)