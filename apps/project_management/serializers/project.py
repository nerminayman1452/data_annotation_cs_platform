from rest_framework import serializers

from apps.project_management.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    """
    Read-Only Serializer for Listing & Details.
    Flattens the 'estimates' and 'actuals' proxies into JSON fields.
    """
    # Organization Info
    organization_title = serializers.CharField(source='organization.name', read_only=True)

    # --- Financials (Estimates) ---
    total_cost = serializers.DecimalField(source='estimates.total_cost', max_digits=15, decimal_places=3,
                                          read_only=True, allow_null=True)
    total_units = serializers.IntegerField(source='estimates.total_units', read_only=True, allow_null=True)
    total_efforts = serializers.DecimalField(source='estimates.total_efforts', max_digits=10, decimal_places=2,
                                             read_only=True, allow_null=True)

    # --- Execution (Actuals) ---
    actual_cost = serializers.DecimalField(source='actuals.total_cost', max_digits=15, decimal_places=3, read_only=True, allow_null=True)
    actual_units = serializers.IntegerField(source='actuals.total_units', read_only=True, allow_null=True)
    progress = serializers.FloatField(source='actuals.progress', read_only=True, allow_null=True)
    quality = serializers.FloatField(source='actuals.quality', read_only=True, allow_null=True)
    time_elapsed_percentage = serializers.FloatField(source='actuals.time_elapsed_percent', read_only=True, allow_null=True)

    # --- Counts ---
    actual_plans_count = serializers.IntegerField(source='estimates.total_plans_count', read_only=True)
    actual_members = serializers.IntegerField(source='actuals.total_members', read_only=True)
    actual_plans_types = serializers.ListField(source='actuals.total_plans_types', read_only=True)

    # --- Dates ---
    start_date = serializers.DateField(source='estimates.start_date', read_only=True)
    end_date = serializers.DateField(source='estimates.end_date', read_only=True)
    duration_days = serializers.IntegerField(source='estimates.duration_days', read_only=True)
    duration_weeks = serializers.FloatField(source='estimates.duration_weeks', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'project_name', 'project_description',
            'organization', 'organization_title',
            'created_by', 'is_archived', 'created_at', 'updated_at',
            # Flattened Fields
            'total_cost', 'total_units', 'total_efforts', 'actual_members',
            'actual_plans_types', 'actual_plans_count',
            'actual_cost', 'actual_units', 'progress', 'quality',
            'start_date', 'end_date',
            'duration_days','duration_weeks', 'time_elapsed_percentage'
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user
        organization = attrs.get('organization')
        project_name = attrs.get('project_name')

        # 1. Ownership Check
        # DRF automatically converts the ID to an Organization instance
        if organization.created_by != int(user.id):
            raise serializers.ValidationError(
                {"organization": "You are not authorized to create projects in this organization."})

        # 2. Duplicate Name Check (creation only)
        if self.instance is None:
            if Project.objects.filter(organization=organization, project_name=project_name).exists():
                raise serializers.ValidationError(
                    {"project_name": "Project with this name already exists in this organization."})

        print("attrs", attrs)

        return attrs

    def create(self, validated_data):
        user_id = self.context['request'].user.id
        validated_data['created_by'] = int(user_id)
        return super().create(validated_data)
