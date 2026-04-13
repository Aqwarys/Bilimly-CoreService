from django.urls import path
from .views import CategoryListView, CourseDetailView, CourseLessonsListView, CourseQuizView

app_name = "courses"

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("<int:id>/quiz/", CourseQuizView.as_view(), name="course-quiz"),
    path("<slug:slug>/", CourseDetailView.as_view(), name="course-detail"),
    path("<slug:slug>/lessons/", CourseLessonsListView.as_view(), name="course-lessons-list"),
]
