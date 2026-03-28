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
from .permissions import IsAuthenticated


class LessonCreateView(APIView):
    """
    Create a new draft lesson.

    Creates an empty draft lesson for a course and returns its ID.
    """
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]

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
