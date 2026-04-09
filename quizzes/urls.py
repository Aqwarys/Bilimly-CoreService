from django.urls import path

from .views import (
    QuestionBulkCreateView,
    QuestionDetailView,
    QuestionListView,
    QuizCheckView,
    QuizCreateView,
    QuizDetailView,
    QuizEditView,
    QuizFullUpdateView,
)

urlpatterns = [
    path("", QuizCreateView.as_view(), name="quiz-create"),
    path("<int:id>/", QuizDetailView.as_view(), name="quiz-detail"),
    path("<int:id>/edit/", QuizEditView.as_view(), name="quiz-edit"),
    path("<int:id>/full-update/", QuizFullUpdateView.as_view(), name="quiz-full-update"),
    path("<int:id>/check/", QuizCheckView.as_view(), name="quiz-check"),
    path("questions/", QuestionListView.as_view(), name="question-list"),
    path("questions/bulk-create/", QuestionBulkCreateView.as_view(), name="question-bulk-create"),
    path("questions/<int:id>/", QuestionDetailView.as_view(), name="question-detail"),
]
