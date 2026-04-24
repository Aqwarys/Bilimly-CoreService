from django.urls import path

from .views import ExamBuildView, ExamCheckView, SubjectGroupedListView

urlpatterns = [
    path("subjects/", SubjectGroupedListView.as_view(), name="exam-subjects"),
    path("exam/", ExamBuildView.as_view(), name="exam-build"),
    path("exam/check/", ExamCheckView.as_view(), name="exam-check"),
]
