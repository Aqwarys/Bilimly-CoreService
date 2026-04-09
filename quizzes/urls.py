from django.urls import path

from .views import (
    QuestionCreateView,
    QuestionDeleteView,
    QuestionUpdateView,
    QuizCheckView,
    QuizCreateView,
    QuizDeleteView,
    QuizEditRetrieveView,
    QuizFullUpdateView,
    QuizRetrieveView,
    QuizUpdateView,
)

app_name = "quizzes"

urlpatterns = [
    path("", QuizCreateView.as_view(), name="quiz-create"),
    path("<int:pk>/full-update/", QuizFullUpdateView.as_view(), name="quiz-full-update"),
    path("<int:pk>/edit/", QuizEditRetrieveView.as_view(), name="quiz-edit"),
    path("<int:pk>/check/", QuizCheckView.as_view(), name="quiz-check"),
    path("<int:pk>/", QuizRetrieveView.as_view(), name="quiz-retrieve"),
    path("<int:pk>/", QuizUpdateView.as_view(), name="quiz-update"),
    path("<int:pk>/delete/", QuizDeleteView.as_view(), name="quiz-delete-legacy"),
    path("<int:quiz_id>/questions/", QuestionCreateView.as_view(), name="question-create"),
    path("questions/<int:pk>/", QuestionUpdateView.as_view(), name="question-update"),
    path("questions/<int:pk>/delete/", QuestionDeleteView.as_view(), name="question-delete-legacy"),
    path("<int:pk>/", QuizDeleteView.as_view(), name="quiz-delete"),
    path("questions/<int:pk>/", QuestionDeleteView.as_view(), name="question-delete"),
]