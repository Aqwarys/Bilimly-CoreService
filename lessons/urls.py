"""
URL configuration for lessons app.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from .views import LessonCreateView, LessonImageView, LessonPublishView, LessonQuizView, LessonUpdateView

app_name = 'lessons'

urlpatterns = [
    # Create draft lesson
    path('', LessonCreateView.as_view(), name='lesson-create'),
    path('<int:id>/quiz/', LessonQuizView.as_view(), name='lesson-quiz'),

    # Upload image for lesson
    path('<int:lesson_id>/upload-image/', LessonImageView.as_view(), name='lesson-upload-image'),

    # Publish lesson
    path('<int:lesson_id>/publish/', LessonPublishView.as_view(), name='lesson-publish'),

    # Update lesson (PUT and PATCH)
    path('<int:lesson_id>/', LessonUpdateView.as_view(), name='lesson-update'),
]
