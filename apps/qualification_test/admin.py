from django.contrib import admin

from apps.qualification_test.models import Exam, ExamTask, Question, QuestionCategory, DifficultyLevel, ExamTaskReview, \
    ExamBatchMembers

# Register your models here.
admin.site.register(Exam)
admin.site.register(ExamTask)
admin.site.register(Question)
admin.site.register(QuestionCategory)
admin.site.register(DifficultyLevel)
admin.site.register(ExamTaskReview)
admin.site.register(ExamBatchMembers)

