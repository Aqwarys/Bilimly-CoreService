"""
Views module for lessons app.

Contains API views for lesson management including creation, image upload, and publishing.
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
    OpenApiParameter
)
from drf_spectacular.types import OpenApiTypes

from .models import Lesson, LessonImage
from .serializers import LessonCreateSerializer, LessonSerializer, LessonImageSerializer
from .services import cleanup_unused_images
from .permissions import IsAuthenticated, IsAdminUserOnly


class LessonCreateView(APIView):
    """
    Create a new draft lesson.

    Creates an empty draft lesson for a course and returns its ID.
    """
    permission_classes = [IsAdminUserOnly]

    @extend_schema(
        summary="Create draft lesson",
        description="Creates an empty draft lesson and returns its ID.",
        request=LessonCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=LessonCreateSerializer,
                description="Draft lesson created successfully",
                examples=[
                    OpenApiExample(
                        "Success Response",
                        summary="Draft lesson created",
                        value={
                            "id": 10,
                            "is_draft": True
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Bad Request",
                examples=[
                    OpenApiExample(
                        "Invalid Course ID",
                        summary="Course not found",
                        value={"course_id": ["Invalid pk \"999\" - object does not exist."]}
                    )
                ]
            ),
            401: OpenApiResponse(description="Unauthorized")
        }
    )
    def post(self, request):
        serializer = LessonCreateSerializer(data=request.data)
        if serializer.is_valid():
            lesson = serializer.save()
            return Response(
                {"id": lesson.id, "is_draft": lesson.is_draft},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LessonImageView(APIView):
    """
    Upload image for lesson editor.

    Uploads an image file and attaches it to a lesson.
    Returns the image URL to be used in the TipTap editor.
    """
    permission_classes = [IsAdminUserOnly]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Upload image for lesson editor",
        description="Uploads image and attaches it to lesson. Returns URL to be used inside TipTap editor.",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'image': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Image file to upload'
                    }
                }
            }
        },
        responses={
            201: OpenApiResponse(
                response=LessonImageSerializer,
                description="Image uploaded successfully",
                examples=[
                    OpenApiExample(
                        "Success Response",
                        summary="Image uploaded",
                        value={
                            "id": 5,
                            "image": "/media/lesson_images/image.png",
                            "created_at": "2023-12-01T10:30:00Z"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Bad Request",
                examples=[
                    OpenApiExample(
                        "Missing Image",
                        summary="No image file provided",
                        value={"image": ["No file was submitted."]}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Not Found",
                examples=[
                    OpenApiExample(
                        "Lesson Not Found",
                        summary="Lesson does not exist",
                        value={"detail": "Not found."}
                    )
                ]
            ),
            401: OpenApiResponse(description="Unauthorized")
        }
    )
    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Check if user has permission to edit this lesson
        # In a real application, you might want to check course ownership
        # For now, we'll just check authentication

        serializer = LessonImageSerializer(data=request.data)
        if serializer.is_valid():
            lesson_image = serializer.save(lesson=lesson)
            return Response(
                {"image_url": lesson_image.image.url},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LessonPublishView(APIView):
    """
    Publish a lesson.

    Marks a lesson as published and removes any unused images.
    """
    permission_classes = [IsAdminUserOnly]

    @extend_schema(
        summary="Publish lesson",
        description="Marks lesson as published and removes unused images.",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Lesson published successfully",
                examples=[
                    OpenApiExample(
                        "Success Response",
                        summary="Lesson published",
                        value={
                            "status": "published",
                            "deleted_images": 2
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Bad Request",
                examples=[
                    OpenApiExample(
                        "No Content",
                        summary="Cannot publish lesson without content",
                        value={"detail": "Cannot publish lesson without content."}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Not Found",
                examples=[
                    OpenApiExample(
                        "Lesson Not Found",
                        summary="Lesson does not exist",
                        value={"detail": "Not found."}
                    )
                ]
            ),
            401: OpenApiResponse(description="Unauthorized")
        }
    )
    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Check if lesson has content
        if not lesson.content:
            return Response(
                {"detail": "Cannot publish lesson without content."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Remove unused images
        deleted_count = cleanup_unused_images(lesson)

        # Mark as published
        lesson.is_draft = False
        lesson.save()

        return Response({
            "status": "published",
            "deleted_images": deleted_count
        }, status=status.HTTP_200_OK)


class LessonUpdateView(APIView):
    """
    Update lesson details.

    Supports both full update (PUT) and partial update (PATCH).
    Only admin users can update lessons.
    """
    permission_classes = [IsAdminUserOnly]

    @extend_schema(
        summary="Update lesson",
        description="Updates lesson fields except course_id and id.",
        tags=["lessons"],
        request=LessonSerializer,
        responses={
            200: OpenApiResponse(
                response=LessonSerializer,
                description="Lesson updated successfully",
                examples=[
                    OpenApiExample(
                        "Success Response",
                        summary="Lesson updated",
                        value={
                            "id": 10,
                            "course": 1,
                            "course_name": "Python Basics",
                            "title": "Updated lesson",
                            "content": {},
                            "is_draft": True,
                            "priority": 2
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Bad Request",
                examples=[
                    OpenApiExample(
                        "Invalid Course ID",
                        summary="Course cannot be updated",
                        value={"detail": "course_id cannot be updated"}
                    ),
                    OpenApiExample(
                        "Invalid Priority",
                        summary="Priority must be positive",
                        value={"priority": ["Priority must be a positive integer."]},
                    ),
                    OpenApiExample(
                        "No Content for Published Lesson",
                        summary="Cannot publish without content",
                        value={"detail": "Cannot publish lesson without content."}
                    )
                ]
            ),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found")
        }
    )
    def put(self, request, lesson_id):
        """Full update of lesson (replaces all fields)."""
        return self._update_lesson(request, lesson_id, partial=False)

    def patch(self, request, lesson_id):
        """Partial update of lesson (updates only provided fields)."""
        return self._update_lesson(request, lesson_id, partial=True)

    def _update_lesson(self, request, lesson_id, partial=False):
        """Helper method for both PUT and PATCH operations."""
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Check if course_id is being updated (not allowed)
        if 'course_id' in request.data or 'course' in request.data:
            return Response(
                {"detail": "course_id cannot be updated"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate priority if provided
        if 'priority' in request.data:
            try:
                priority = int(request.data['priority'])
                if priority <= 0:
                    return Response(
                        {"priority": ["Priority must be a positive integer."]},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return Response(
                    {"priority": ["Priority must be a positive integer."]},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = LessonSerializer(lesson, data=request.data, partial=partial)
        if serializer.is_valid():
            # Check content validation for published lessons
            if not serializer.validated_data.get('is_draft', lesson.is_draft):
                content = serializer.validated_data.get('content', lesson.content)
                if not content or content == {} or content == []:
                    return Response(
                        {"detail": "Cannot publish lesson without content."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Handle priority uniqueness validation manually to exclude current lesson
            priority = serializer.validated_data.get('priority', lesson.priority)
            course = lesson.course

            # Check if another lesson with the same priority exists in this course
            existing_lesson = Lesson.objects.filter(
                course=course,
                priority=priority
            ).exclude(id=lesson_id).first()

            if existing_lesson:
                return Response(
                    {"priority": [f"Lesson with priority {priority} already exists in this course."]},
                    status=status.HTTP_400_BAD_REQUEST
                )

            lesson = serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
