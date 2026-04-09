from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from subscription.models import user_has_active_subscription
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.generics import DestroyAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Question, Quiz
from .permissions import IsAdminUserOnly
from .serializers import (
    FullQuizUpdateSerializer,
    QuestionSerializer,
    QuizCheckRequestSerializer,
    QuizCheckResultSerializer,
    QuizEditSerializer,
    QuizPassSerializer,
    QuizSerializer,
)
from .services import check_quiz_answers, update_quiz_with_questions


class QuizCreateView(APIView):
    permission_classes = [IsAdminUserOnly]
    serializer_class = QuizSerializer

    def post(self, request, *args, **kwargs):
        serializer = QuizSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuizRetrieveView(APIView):
    queryset = Quiz.objects.prefetch_related("questions")

    @extend_schema(
        tags=["Quizzes"],
        summary="Get quiz for passing",
        description=(
            "Returns quiz for passing without correct answers and explanations. "
            "If quiz is paid (is_free=false), authenticated user with active subscription is required."
        ),
        responses={
            200: OpenApiResponse(response=QuizPassSerializer, description="Quiz for passing"),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(description="Active subscription is required for paid quiz."),
            404: OpenApiResponse(description="Quiz not found."),
        },
        examples=[
            OpenApiExample(
                "Success response",
                value={
                    "id": 7,
                    "course": 1,
                    "lesson": None,
                    "title": "Basics Quiz",
                    "description": "Quiz description",
                    "is_free": True,
                    "cost": None,
                    "image": None,
                    "questions": [
                        {
                            "id": 42,
                            "type": "single",
                            "content": ["What is 2+2?"],
                            "image": None,
                            "options": ["3", "4", "5"],
                            "score": 1,
                        }
                    ],
                },
                response_only=True,
            )
        ],
    )
    def get(self, request, pk, *args, **kwargs):
        quiz = get_object_or_404(self.queryset, pk=pk)
        if not quiz.is_free:
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {"detail": "Authentication credentials were not provided."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            if not user_has_active_subscription(request.user):
                return Response(
                    {"detail": "Active subscription is required for paid quiz."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = QuizPassSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_200_OK)


class QuizEditRetrieveView(APIView):
    permission_classes = [IsAdminUserOnly]
    queryset = Quiz.objects.prefetch_related("questions")

    @extend_schema(
        tags=["Quizzes"],
        summary="Get quiz for editing",
        description="Returns full quiz data including correct answers and explanations. Admin only.",
        responses={
            200: OpenApiResponse(response=QuizEditSerializer, description="Quiz full data for editing"),
            403: OpenApiResponse(description="You do not have permission to perform this action."),
            404: OpenApiResponse(description="Quiz not found."),
        },
        examples=[
            OpenApiExample(
                "Success response",
                value={
                    "id": 7,
                    "course": 1,
                    "lesson": None,
                    "title": "Basics Quiz",
                    "description": "Quiz description",
                    "is_free": True,
                    "cost": None,
                    "image": None,
                    "questions": [
                        {
                            "id": 42,
                            "type": "single",
                            "content": ["What is 2+2?"],
                            "image": None,
                            "options": ["3", "4", "5"],
                            "correct": [1],
                            "score": 1,
                            "explanation": "2+2 is 4",
                        }
                    ],
                },
                response_only=True,
            )
        ],
    )
    def get(self, request, pk, *args, **kwargs):
        quiz = get_object_or_404(self.queryset, pk=pk)
        serializer = QuizEditSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_200_OK)


class QuizFullUpdateView(APIView):
    permission_classes = [IsAdminUserOnly]
    queryset = Quiz.objects.prefetch_related("questions")

    @extend_schema(
        tags=["Quizzes"],
        summary="Full update quiz with questions",
        description=(
            "Updates quiz fields and synchronizes questions: "
            "updates existing, creates new, and deletes removed questions."
        ),
        request=FullQuizUpdateSerializer,
        responses={
            200: OpenApiResponse(response=QuizEditSerializer, description="Updated quiz with full questions data"),
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(description="You do not have permission to perform this action."),
            404: OpenApiResponse(description="Quiz not found."),
        },
        examples=[
            OpenApiExample(
                "Request example",
                value={
                    "title": "Updated Quiz",
                    "description": "Updated description",
                    "questions": [
                        {
                            "id": 1,
                            "type": "single",
                            "content": ["Question content"],
                            "options": ["A", "B"],
                            "correct": [1],
                            "score": 2,
                            "explanation": "Because B is right",
                        },
                        {
                            "type": "multiple",
                            "content": ["New question"],
                            "options": ["A", "B", "C"],
                            "correct": [0, 2],
                            "score": 3,
                            "explanation": "A and C are right",
                        },
                    ],
                },
                request_only=True,
            )
        ],
    )
    def put(self, request, pk, *args, **kwargs):
        quiz = get_object_or_404(self.queryset, pk=pk)
        serializer = FullQuizUpdateSerializer(instance=quiz, data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        questions_data = validated_data.pop("questions", [])
        update_quiz_with_questions(quiz=quiz, quiz_data=validated_data, questions_data=questions_data)

        quiz.refresh_from_db()
        quiz = Quiz.objects.prefetch_related("questions").get(pk=quiz.pk)
        response_serializer = QuizEditSerializer(quiz)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class QuizCheckView(APIView):
    permission_classes = [IsAuthenticated]
    queryset = Quiz.objects.prefetch_related("questions")

    @extend_schema(
        tags=["Quizzes"],
        summary="Check quiz answers",
        description=(
            "Checks submitted answers. Logic: single -> exact match, multiple -> set equality, "
            "ordering -> exact order."
        ),
        request=QuizCheckRequestSerializer,
        responses={
            200: OpenApiResponse(response=QuizCheckResultSerializer(many=True), description="Per-question check results"),
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(description="Quiz not found."),
        },
        examples=[
            OpenApiExample(
                "Request example",
                value={"answers": [{"question_id": 42, "selected": [1]}]},
                request_only=True,
            ),
            OpenApiExample(
                "Response example",
                value=[
                    {
                        "question_id": 42,
                        "is_correct": True,
                        "score": 1,
                        "explanation": "Correct explanation",
                        "correct_answer": [1],
                    }
                ],
                response_only=True,
            ),
        ],
    )
    def post(self, request, pk, *args, **kwargs):
        quiz = get_object_or_404(self.queryset, pk=pk)
        serializer = QuizCheckRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        results = check_quiz_answers(quiz=quiz, answers=serializer.validated_data["answers"])
        output_serializer = QuizCheckResultSerializer(results, many=True)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class QuizUpdateView(UpdateAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAdminUserOnly]
    http_method_names = ["put"]


class QuizDeleteView(DestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAdminUserOnly]
    http_method_names = ["delete"]


class QuestionCreateView(APIView):
    permission_classes = [IsAdminUserOnly]
    serializer_class = QuestionSerializer

    def post(self, request, quiz_id, *args, **kwargs):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        payload = request.data.copy()
        payload["quiz"] = quiz.id

        serializer = QuestionSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuestionUpdateView(UpdateAPIView):
    queryset = Question.objects.select_related("quiz").all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminUserOnly]
    http_method_names = ["put"]


class QuestionDeleteView(DestroyAPIView):
    queryset = Question.objects.select_related("quiz").all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminUserOnly]
    http_method_names = ["delete"]
