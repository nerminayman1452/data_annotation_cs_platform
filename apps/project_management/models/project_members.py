from django.db import models

from apps.profile.models.profile import Role
from apps.project_management.models.project import Project

class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="members")
    profile = models.IntegerField(null=True, blank=True)
    # profile = models.ForeignKey("Profile", on_delete=models.CASCADE, related_name="project_memberships")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MANAGER)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("project", "profile")
        indexes = [
            models.Index(fields=["project", "role"]),
        ]

    def __str__(self):
        return f"{self.project.project_name} - {self.profile} ({self.role})"

