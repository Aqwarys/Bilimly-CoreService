from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes
from .models import Category, Course
from .serializers import CategorySerializer, CourseDetailSerializer, BaseLessonSerializer
from .permissions import HasActiveSubscription
from .pagination import CategoryPagination
from lessons.models import Lesson
from quizzes.serializers import QuizDetailWithAttemptSerializer
from quizzes.views import QuizAccessMixin
from quiz_statistics.services import get_quiz_by_course_id
from quiz_statistics.views import UserAttemptPayloadMixin


@extend_schema(
    tags=["Courses"],
    summary="Get categories with courses",
    description=(
        "Returns a paginated list of categories with their nested courses.\n\n"
        "Accessible by both authenticated and unauthenticated users.\n\n"
        "**Pagination Parameters:**\n"
        "- `page`: Page number (default: 1)\n"
        "- `page_size`: Number of categories per page (default: 10, max: 100)\n\n"
        "**Example:** `/api/categories/?page=1&page_size=5`"
    ),
    parameters=[
        OpenApiParameter(
            name="page",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Page number",
            required=False,
            default=1,
        ),
        OpenApiParameter(
            name="page_size",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Number of categories returned per page",
            required=False,
            default=10,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=CategorySerializer,
            description="List of categories with nested courses",
            examples=[
                OpenApiExample(
                    "Category List Response",
                    summary="Example category list response",
                    description="Paginated response with categories and courses",
                    value={
                        "total_category": 10,
                        "result": [
                            {
                                "code": "B017",
                                "name": "Педагогика",
                                "description": "Description of Pedagogy category",
                                "image": "/media/categories/pedagogy.jpg",
                                "courses": [
                                    {
                                        "slug": "python-basics",
                                        "name": "Python Basics",
                                        "description": "Learn Python from scratch",
                                        "image": "/media/courses/python.png",
                                        "is_free": True,
                                        "cost": None,
                                    }
                                ],
                            }
                        ],
                    },
                )
            ],
        )
    },
)
class CategoryListView(ListAPIView):
    """
    API view for listing categories with nested courses.
    Public endpoint, paginated.
    """

    queryset = Category.objects.prefetch_related("courses").all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = CategoryPagination


@extend_schema(
    tags=["Courses"],
    summary="Get course details",
    description=(
        "Returns detailed information about a specific course.\n\n"
        "**Access Rules:**\n"
        "- If `is_free` is `true`: accessible by everyone\n"
        "- If `is_free` is `false`: requires authentication and active subscription\n\n"
        "**Path Parameter:**\n"
        "- `slug`: Unique slug of the course"
    ),
    parameters=[
        OpenApiParameter(
            name="slug",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="Unique slug of the course",
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=CourseDetailSerializer,
            description="Course details",
            examples=[
                OpenApiExample(
                    "Course Detail Response",
                    summary="Example course detail response",
                    description="Detailed course information",
                    value={
                        "category": "Педагогика",
                        "slug": "python-basics",
                        "name": "Python Basics",
                        "description": "Learn Python from scratch",
                        "image": "/media/courses/python.png",
                        "is_free": False,
                        "cost": "9.99",
                    },
                )
            ],
        ),
        401: OpenApiResponse(
            description="Authentication credentials were not provided",
            examples=[
                OpenApiExample(
                    "Unauthorized",
                    summary="Authentication required",
                    description="User is not authenticated",
                    value={"detail": "Authentication credentials were not provided."},
                )
            ],
        ),
        403: OpenApiResponse(
            description="Active subscription required to access this course",
            examples=[
                OpenApiExample(
                    "Forbidden",
                    summary="Subscription required",
                    description="User does not have active subscription",
                    value={"detail": "Active subscription required to access this course"},
                )
            ],
        ),
        404: OpenApiResponse(
            description="Course not found",
            examples=[
                OpenApiExample(
                    "Not Found",
                    summary="Course does not exist",
                    description="Course with given slug not found",
                    value={"detail": "Course not found"},
                )
            ],
        ),
    },
)
class CourseDetailView(RetrieveAPIView):
    """
    API view for course detail.
    Requires authentication and active subscription if not free.
    """

    queryset = Course.objects.select_related("category").all()
    serializer_class = CourseDetailSerializer
    permission_classes = [HasActiveSubscription]
    lookup_field = "slug"

    def get_object(self):
        slug = self.kwargs.get("slug")
        return get_object_or_404(Course, slug=slug)


@extend_schema(
    tags=["Courses"],
    summary="Get lessons by course",
    description="Returns all lessons for a specific course, ordered by priority.",
    parameters=[
        OpenApiParameter(
            name="slug",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="Unique slug of the course"
        )
    ],
    responses={
        200: OpenApiResponse(
            response=BaseLessonSerializer(many=True),
            description="Lessons retrieved successfully",
            examples=[
                OpenApiExample(
                    "Success Response",
                    summary="Lessons list",
                    value=[
                        {
                            "id": 10,
                            "course": 1,
                            "course_name": "Python Programming",
                            "title": "Introduction to Python",
                            "content": {},
                            "image": None,
                            "is_draft": False,
                            "auto_test": False,
                            "priority": 1,
                            "created_at": "2023-12-01T10:00:00Z",
                            "updated_at": "2023-12-01T10:30:00Z"
                        },
                        {
                            "id": 11,
                            "course": 1,
                            "course_name": "Python Programming",
                            "title": "Variables and Data Types",
                            "content": {},
                            "image": None,
                            "is_draft": True,
                            "auto_test": False,
                            "priority": 2,
                            "created_at": "2023-12-01T10:15:00Z",
                            "updated_at": "2023-12-01T10:15:00Z"
                        }
                    ]
                )
            ]
        ),
        404: OpenApiResponse(
            description="Not Found",
            examples=[
                OpenApiExample(
                    "Course Not Found",
                    summary="Course does not exist",
                    value={"detail": "Not found."}
                )
            ]
        ),
        401: OpenApiResponse(description="Unauthorized")
    }
)
class CourseLessonsListView(ListAPIView):
    """
    Get lessons by course.

    Returns all lessons for a specific course, ordered by priority.
    """
    serializer_class = BaseLessonSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        course_slug = self.kwargs['slug']
        course = get_object_or_404(Course, slug=course_slug)
        return Lesson.objects.filter(course=course).select_related('course').order_by('priority')


@extend_schema(
    tags=["Courses"],
    summary="Get quiz by course ID",
    description=(
        "Returns quiz attached to the course ID. Conditional response: always returns `quiz`, "
        "and also returns `user_attempt` if authenticated user has previous attempts."
    ),
    parameters=[
        OpenApiParameter(
            name="id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description="Course ID",
            required=True,
        )
    ],
    responses={
        200: OpenApiResponse(
            response=QuizDetailWithAttemptSerializer,
            description="Quiz retrieved successfully.",
            examples=[
                OpenApiExample(
                    "Course Quiz Response",
                    value={
                        "quiz": {
                            "id": 1,
                            "course": 2,
                            "lesson": None,
                            "title": "Python Basics Quiz",
                            "description": "Module check",
                            "is_free": True,
                            "cost": None,
                            "image": None,
                            "questions": [],
                        }
                    },
                )
            ],
        ),
        404: OpenApiResponse(description="Quiz not found for this course."),
    },
)
class CourseQuizView(UserAttemptPayloadMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        quiz = get_quiz_by_course_id(course_id=id)
        QuizAccessMixin().ensure_pass_access(request, quiz)
        payload = self.get_conditional_quiz_response(request=request, quiz=quiz)
        return Response(payload, status=200)
