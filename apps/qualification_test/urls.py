from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.qualification_test.views.exam import ExamViewSet, QuestionBankUploadView
from apps.qualification_test.views.exam_assignment import InitialAssignExamTasksAPIView
from apps.qualification_test.views.exam_batch_members import ExamReviewBatchMembersViewSet
from apps.qualification_test.views.exam_evaluation import ExamSubmissionAndEvaluationView
from apps.qualification_test.views.exam_question import AnnotatorExamTaskListView
from apps.qualification_test.views.exam_review import PendingExamTaskReviewListView
from apps.qualification_test.views.exam_review_assignment import AssignExamReviewerAPIView
from apps.qualification_test.views.exam_review_decision import SubmitExamTaskReviewAPIView
from apps.qualification_test.views.exam_task import SubmitExamTaskAPIView

router = DefaultRouter()
router.register(r'exam', ExamViewSet, basename='review-exam')
router.register(r'exam-members', ExamReviewBatchMembersViewSet, basename='exam-members')
urlpatterns = [
    path("question-bank/upload/", QuestionBankUploadView.as_view(), name="question-bank-upload"),
    path("batch-members/exam-task/", InitialAssignExamTasksAPIView.as_view(), name="exam-task"),
    path('exam/questions/', AnnotatorExamTaskListView.as_view(), name='annotator-exam-questions'),
    path('exam/<int:exam_task_id>/result/', SubmitExamTaskAPIView.as_view(), name='exam-task-result'),
    path("exams/<int:exam_id>/submit/", ExamSubmissionAndEvaluationView.as_view(), name="submit-exam"),
    path("exam/assign-reviewer/", AssignExamReviewerAPIView.as_view(), name="exam-reviewer"),
    path("exam/reviews/", PendingExamTaskReviewListView.as_view(), name="pending-exam-task-reviews"),
    path("exam/reviews/<int:review_id>/submit/", SubmitExamTaskReviewAPIView.as_view(),
         name="submit_exam_task_review"),
    path('', include(router.urls)),

]
