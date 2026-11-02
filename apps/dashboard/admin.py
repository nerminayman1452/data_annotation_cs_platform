from django.contrib import admin
from apps.dashboard.models.batch_join import BatchJoinRequest
# from apps.project_management.models.batch_members import BatchMembers
from django.utils.html import format_html

@admin.register(BatchJoinRequest)
class BatchJoinRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "batch", "annotator","first_name", "last_name","email","status", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("batch__batch_name", "first_name", "last_name", "email", "annotator")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    actions = ["approve_requests", "reject_requests"]

    @admin.action(description="✅ Approve selected join requests")
    def approve_requests(self, request, queryset):
        from apps.project_management.models.plan_members import PlanMember

        for req in queryset:
            if req.status != "approved":
                req.status = "approved"
                req.save()
                # Automatically add to batch members
                PlanMember.objects.get_or_create(batch=req.plan, profile=req.annotator)

        self.message_user(request, "Selected join requests approved and members added successfully.")

    @admin.action(description="❌ Reject selected join requests")
    def reject_requests(self, request, queryset):
        updated = queryset.update(status="rejected")
        self.message_user(request, f"{updated} join requests rejected successfully.")

@admin.display(description="Status")
def colored_status(self, obj):
    color = {
        "pending": "orange",
        "approved": "green",
        "rejected": "red"
    }.get(obj.status, "gray")
    return format_html(f'<b style="color:{color};">{obj.status.capitalize()}</b>')