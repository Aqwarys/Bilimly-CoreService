from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subject
from .serializers import (
    ExamCheckResponseSerializer,
    ExamCheckSubjectInputSerializer,
    ExamResponseSerializer,
    SubjectGroupedSerializer,
    SubjectSerializer,
)
from .services import build_exam, calculate_scores, check_exam_answers


@extend_schema(
    tags=["Exam"],
    summary="Get subjects grouped by type",
    description=(
        "Returns subjects grouped by their type. Useful for building exam selection UI.\n\n"
        "Edge cases:\n"
        "- Returns empty arrays if no subjects exist"
    ),
    responses={
        200: OpenApiResponse(
            response=SubjectGroupedSerializer(many=True),
            description="Subjects grouped by type.",
            examples=[
                OpenApiExample(
                    "Grouped Subjects",
                    value=[
                        {
                            "type": "MANDATORY",
                            "subjects": [
                                {
                                    "id": 1,
                                    "name": "Math",
                                    "slug": "math",
                                    "description": "Core math",
                                    "type": "MANDATORY",
                                    "duration_sec": 3600,
                                    "max_score": 50,
                                }
                            ],
                        },
                        {
                            "type": "PROFILE",
                            "subjects": [],
                        },
                    ],
                )
            ],
        )
    },
)
class SubjectGroupedListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        subjects = Subject.objects.all().order_by("name")
        mandatory = subjects.filter(type=Subject.SubjectType.MANDATORY)
        profile = subjects.filter(type=Subject.SubjectType.PROFILE)

        payload = [
            {
                "type": Subject.SubjectType.MANDATORY,
                "subjects": SubjectSerializer(mandatory, many=True).data,
            },
            {
                "type": Subject.SubjectType.PROFILE,
                "subjects": SubjectSerializer(profile, many=True).data,
            },
        ]
        return Response(payload)


@extend_schema(
    tags=["Exam"],
    summary="Build exam by subject",
    description=(
        "Builds a randomized exam for a given subject.\n\n"
        "Rules:\n"
        "- If subject type is PROFILE: includes selected PROFILE subject + all MANDATORY subjects\n"
        "- If subject type is MANDATORY: includes only that subject\n"
        "- Distributes questions evenly across modules\n"
        "- Randomizes questions per request\n\n"
        "Edge cases:\n"
        "- Subject not found -> 404\n"
        "- Subject without modules -> 400\n"
        "- Module without problems -> 400\n"
        "- Insufficient problems to satisfy max_score -> 400"
    ),
    parameters=[
        OpenApiParameter(
            name="subject",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Subject slug",
            required=True,
        )
    ],
    responses={
        200: OpenApiResponse(
            response=ExamResponseSerializer,
            description="Exam payload",
            examples=[
                OpenApiExample(
                    "Exam Response",
                    value={
                        "total_duration_sec": 5400,
                        "total_problem_count": 80,
                        "total_score_sum": 80,
                        "subjects": [
                            {
                                "name": "Math",
                                "total_problem": 50,
                                "max_score": 50,
                                "problems": [
                                    {
                                        "id": 1,
                                        "type": "single",
                                        "content": {"type": "doc", "content": []},
                                        "image": None,
                                        "audio": None,
                                        "options": ["A", "B", "C"],
                                    }
                                ],
                            }
                        ],
                    },
                )
            ],
        ),
        404: OpenApiResponse(description="Subject not found"),
        400: OpenApiResponse(description="Invalid subject configuration"),
    },
)
class ExamBuildView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        slug = request.query_params.get("subject")
        subject = get_object_or_404(Subject, slug=slug)
        payload = build_exam(subject)
        return Response(payload)


@extend_schema(
    tags=["Exam"],
    summary="Check exam answers",
    description=(
        "Validates answers and returns per-problem correctness and scoring.\n\n"
        "Rules:\n"
        "- Validates all problem IDs\n"
        "- Rejects duplicate problem IDs\n"
        "- Allows selected = null\n\n"
        "Scoring:\n"
        "- single: exact match\n"
        "- multiple: set match\n"
        "- ordering: exact order\n\n"
        "Edge cases:\n"
        "- Invalid problem ID -> 400\n"
        "- Duplicate problem IDs -> 400\n"
        "- Invalid selected values -> 400"
    ),
    request=ExamCheckSubjectInputSerializer(many=True),
    examples=[
        OpenApiExample(
            "Check Request",
            request_only=True,
            value=[
                {
                    "name": "English",
                    "problems": [
                        {"id": 3, "selected": [0]},
                        {"id": 4, "selected": [0]},
                    ],
                },
                {
                    "name": "Mathematics",
                    "problems": [
                        {"id": 1, "selected": [1]},
                        {"id": 2, "selected": [0, 3]},
                    ],
                },
                {
                    "name": "TGO",
                    "problems": [
                        {"id": 6, "selected": [0]},
                    ],
                },
            ],
        )
    ],
    responses={
        200: OpenApiResponse(
            response=ExamCheckResponseSerializer,
            description="Exam checking result",
            examples=[
                OpenApiExample(
                    "Check Response",
                    value={
                        "total_get_score": 120,
                        "total_score_sum": 150,
                        "subjects": [
                            {
                                "name": "Math",
                                "total_score_get": 30,
                                "problems": [
                                    {
                                        "id": 1,
                                        "correct": [2],
                                        "selected": [2],
                                        "explanation": "Use quadratic formula.",
                                        "is_correct": True,
                                    }
                                ],
                            }
                        ],
                    },
                )
            ],
        ),
        400: OpenApiResponse(description="Invalid input"),
    },
)
class ExamCheckView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ExamCheckSubjectInputSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        subject_results = check_exam_answers(serializer.validated_data)
        payload = calculate_scores(subject_results)
        return Response(payload)
