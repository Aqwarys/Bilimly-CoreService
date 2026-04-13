from django.urls import path

from .views import UserAttemptedQuizzesView, UserStatisticsView


urlpatterns = [
    path("me/", UserStatisticsView.as_view(), name="statistics-me"),
    path("my-quizzes/", UserAttemptedQuizzesView.as_view(), name="statistics-my-quizzes"),
]
