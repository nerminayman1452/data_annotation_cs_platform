from django.db import models

from apps.project_management.models.text_plan import TextPlan

# from apps.project_management.refactored_models.profile import Profile
from apps.profile.models.profile import Profile


class Exam(models.Model):
    #todo base class for media types
    MEDIA_TYPES = [
        ("TEXT", "Text"),
        ("IMAGE", "Image"),
        ("AUDIO", "Audio"),
    ]
    name = models.CharField(
        max_length=255,
        verbose_name="Exam Name",
        help_text="Name of the exam",
    )
    # owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="owned_exams")
    owner = models.IntegerField(null=True, blank=True)

    description = models.TextField(null=True, blank=True)
    total_questions = models.IntegerField(default=1)
    duration = models.IntegerField(default=15)
    category = models.JSONField(default=dict, help_text="Category distribution e.g. {'Idiom': 30%, 'Proverb': 70%}")
    difficulty = models.JSONField(default=dict, help_text="Category distribution e.g. {'Hard': 30%, 'Medium': 70%}")
    question_type = models.JSONField(default=dict,
                                     help_text="Question type distribution e.g. {'MCQ': 50%, 'TRUE_FALSE': 50%}")
    passing_score = models.FloatField(default=0, help_text="Minimum score to pass the exam")
    # media_type = models.CharField(max_length=16, choices=MEDIA_TYPES, default="TEXT",
    #                               help_text="The primary media type for this exam.")
    annotation_type = models.CharField(max_length=16, choices=TextPlan.ANNOTATION_TYPES)
    config = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class QuestionCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g., Idiom, Proverb, Terminology")

    def __str__(self):
        return self.name


class DifficultyLevel(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="e.g., Easy, Medium, Hard")

    def __str__(self):
        return self.name


class Question(models.Model):
    class QuestionType(models.TextChoices):
        DIRECT_EDIT = 'DIRECT_EDIT', 'Direct Edit'
        MCQ = 'MCQ', 'Multiple Choice'
        TRUE_FALSE = 'TRUE_FALSE', 'True/False'

    source_text = models.TextField(null=True, blank=True, help_text="The original text to be translated.")
    image_file = models.ImageField(upload_to='exam_images/', null=True, blank=True,
                                   help_text="Upload image if this is an image task.")
    audio_file = models.FileField(upload_to='exam_audio/', null=True, blank=True,
                                  help_text="Upload audio if this is an audio task.")
    #todo help answer for the question
    machine_answer = models.TextField(null=True, blank=True,
                                           help_text="The machine translation output to be edited.")
    question_body = models.TextField(null=True, blank=True, help_text="The body of the question.")
    correct_answer = models.JSONField(default=dict, help_text="The perfect, human-approved correct answer.", null=True,
                                      blank=True)

    category = models.ForeignKey(QuestionCategory, null=True, on_delete=models.CASCADE, related_name="questions")
    difficulty = models.ForeignKey(DifficultyLevel, on_delete=models.CASCADE, related_name="questions")
    question_type = models.CharField(max_length=32, choices=QuestionType.choices)
    # annotation_type = models.CharField(max_length=16, choices=Exam.ANNOTATION_TYPES)

    options = models.JSONField(default=dict,
                               help_text="e.g., {'choices': ['Cat', 'Dog', 'Bird']}")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}-{self.source_text[:80]}"


class ExamBatchMembers(models.Model):
    # profile = models.ForeignKey(
    #     Profile, on_delete=models.CASCADE, related_name='batch_exam_assignments'
    # )
    profile = models.IntegerField(null=True, blank=True)
    batch = models.ForeignKey(TextPlan, on_delete=models.CASCADE, related_name='exam_attempts', null=True,
                              blank=True)
    exam = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name='exam_members', null=True, blank=True
    )
    score = models.FloatField(default=0)
    is_passed = models.BooleanField(default=False)
    submitted = models.BooleanField(default=False)

    @property
    def can_open_exam(self):
        return not self.submitted


class ExamTask(models.Model):
    STATUS_CHOICES = [
        ("ASSIGNED", "Assigned"),
        ("SUBMITTED", "Submitted"),
        ("CORRECT_EXAM_ANSWER", "Model Answer Matched"),
        ("WRONG_EXAM_ANSWER", "Model Answer Mismatched"),
        ("REVIEWER_PENDING", "Pending Review by Reviewer"),
        ("UNDER_REVIEW", "Under Review"),
    ]

    annotator = models.ForeignKey(ExamBatchMembers, on_delete=models.CASCADE, related_name="review_annotations")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="exam_tasks")

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="exam_task")
    answer = models.JSONField(default=dict)
    answer_file = models.FileField(
        upload_to="exam_answers/",
        null=True, blank=True,
        help_text="Used if the task requires uploading a file (e.g., audio recording)."
    )
    status = models.CharField(
        choices=STATUS_CHOICES, default="ASSIGNED", max_length=32)
    time_spent = models.IntegerField(default=0, help_text="Time spent in seconds")
    # changes = models.IntegerField(default=0, help_text="number of changes in sentence")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ExamTaskReview(models.Model):
    DECISION_CHOICES = [
        ("PENDING", "Pending"),
        ("ACCEPTED", "Accepted"),
        ("REJECTED", "Rejected"),
    ]
    task = models.OneToOneField(ExamTask, on_delete=models.CASCADE, related_name="review")
    # reviewer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="reviewer")
    reviewer =models.IntegerField(null=True, blank=True)
    decision = models.CharField(max_length=32, choices=DECISION_CHOICES, default="PENDING")
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
