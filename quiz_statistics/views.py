from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from quizzes.serializers import QuizDetailSerializer

from .serializers import UserAttemptSerializer, UserStatisticsSerializer
from .services import get_user_attempted_quizzes, get_user_statistics


@extend_schema(
    tags=["Statistics"],
    summary="Get my statistics",
    description="Returns user total score, total quizzes passed, and detailed attempts.",
    responses={
        200: OpenApiResponse(
            response=UserStatisticsSerializer,
            description="User statistics retrieved successfully.",
            examples=[
                OpenApiExample(
                    "Statistics Response",
                    value={
                        "total_score": 120,
                        "total_quizzes_passed": 10,
                        "attempts": [
                            {
                                "id": 3,
                                "quiz": 1,
                                "score": 10,
                                "is_completed": True,
                                "created_at": "2026-04-10T10:00:00Z",
                                "updated_at": "2026-04-10T10:00:00Z",
                                "answers": [],
                            }
                        ],
                    },
                )
            ],
        ),
        401: OpenApiResponse(description="Unauthorized"),
    },
)
class UserStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = get_user_statistics(user=request.user)
        serializer = UserStatisticsSerializer(data)
        return Response(serializer.data)


@extend_schema(
    tags=["Statistics"],
    summary="Get my attempted quizzes",
    description="Returns all quizzes that were attempted by the authenticated user.",
    responses={
        200: OpenApiResponse(
            response=QuizDetailSerializer(many=True),
            description="List of attempted quizzes.",
            examples=[
                OpenApiExample(
                    "My Quizzes Response",
                    value=[
                        {
                            "id": 1,
                            "course": 2,
                            "lesson": None,
                            "title": "Python Basics Quiz",
                            "description": "Answer questions to complete module.",
                            "is_free": True,
                            "cost": None,
                            "image": None,
                            "questions": [],
                        }
                    ],
                )
            ],
        ),
        401: OpenApiResponse(description="Unauthorized"),
    },
)
class UserAttemptedQuizzesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        quizzes = get_user_attempted_quizzes(user=request.user)
        return Response(QuizDetailSerializer(quizzes, many=True).data)


class UserAttemptPayloadMixin:
    def get_conditional_quiz_response(self, *, request, quiz):
        payload = {"quiz": QuizDetailSerializer(quiz).data}
        if request.user and request.user.is_authenticated:
            from .services import get_user_attempt

            attempt = get_user_attempt(user=request.user, quiz=quiz)
            if attempt is not None:
                payload["user_attempt"] = UserAttemptSerializer(attempt).data
        return payload
