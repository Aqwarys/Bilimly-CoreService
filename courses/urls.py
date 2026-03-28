from django.urls import path
from .views import CategoryListView, CourseDetailView, CourseLessonsListView

app_name = "courses"

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("<slug:slug>/", CourseDetailView.as_view(), name="course-detail"),
    path("<slug:slug>/lessons/", CourseLessonsListView.as_view(), name="course-lessons-list"),
]
