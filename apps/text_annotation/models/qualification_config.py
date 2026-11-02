from django.db import models

# from apps.user_management.models import UserProfile


class QualificationConfig(models.Model):
    TASK_TYPES = [
        ('Labelling', 'Text Labelling'),
        ('Summarization', 'Text Summarization'),
        ('Validation', 'Text Validation'),
        ('Segmentation', 'Text Segmentation'),
    ]
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    passing_score = models.IntegerField(default=70)
    retry_allowed = models.BooleanField(default=False)
    max_retries = models.IntegerField(default=1)
    #how long (in minutes) a worker must wait before retaking a qualification test if they fail
    retry_cooldown_minutes = models.IntegerField(default=0)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class QualificationTest(models.Model):
    qualification = models.ForeignKey(QualificationConfig, on_delete=models.CASCADE)
    question = models.TextField()
    file = models.FileField(upload_to='tests/', null=True, blank=True)
    correct_answer = models.TextField()
    score_weight = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.question}'

class WorkerQualification(models.Model):
    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("submitted", "Submitted"),
        ("passed", "Passed"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
    ]
    # annotator = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    annotator = models.IntegerField(null=True, blank=True)

    qualification_test = models.ForeignKey(QualificationTest, on_delete=models.CASCADE)
    response = models.TextField(null=True)
    passed = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='in_progress')
    granted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.qualification_test} - {self.annotator} - {self.status}'


