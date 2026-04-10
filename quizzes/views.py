from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Quiz
from .permissions import IsAdminUserOnly
from .serializers import (
    QuestionBulkCreateSerializer,
    QuestionCRUDSerializer,
    QuestionFilterSerializer,
    QuizCheckResultSerializer,
    QuizCheckSerializer,
    QuizDetailSerializer,
    QuizEditSerializer,
    QuizSerializer,
)
from .services import (
    bulk_create_questions,
    check_quiz_answers,
    get_filtered_questions,
    update_quiz_with_questions,
)


class QuizAccessMixin:
    queryset = Quiz.objects.prefetch_related("questions").all()

    def get_quiz(self, quiz_id: int) -> Quiz:
        return get_object_or_404(self.queryset, id=quiz_id)

    def ensure_pass_access(self, request, quiz: Quiz) -> None:
        if quiz.is_free:
            return
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication credentials were not provided.")
        if not hasattr(request.user, "subscription") or not request.user.subscription.is_active:
            raise PermissionDenied("Active subscription required to access this quiz.")


@extend_schema(
    tags=["Quizzes"],
    summary="Create quiz",
    description="Creates a new quiz. Only admin users can create quizzes.",
    request=QuizSerializer,
    responses={
        201: OpenApiResponse(
            response=QuizSerializer,
            description="Quiz created successfully.",
            examples=[
                OpenApiExample(
                    "Quiz Creation",
                    value={
                        "id": 1,
                        "course": 1,
                        "lesson": None,
                        "title": "Python Basics Quiz",
                        "description": "Final quiz for Python basics module.",
                        "is_free": False,
                        "cost": "9.99",
                        "image": None,
                    },
                )
            ],
        ),
        400: OpenApiResponse(description="Bad Request"),
        401: OpenApiResponse(description="Unauthorized"),
        403: OpenApiResponse(description="Forbidden"),
    },
)
class QuizCreateView(APIView):
    permission_classes = [IsAdminUserOnly]

    def post(self, request):
        serializer = QuizSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quiz = serializer.save()
        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Quizzes"],
    summary="Get quiz for passing",
    description=(
        "Returns quiz data for passing. If quiz is paid, authentication and active "
        "subscription are required. Response excludes `correct` and `explanation` fields."
    ),
    parameters=[
        OpenApiParameter(
            name="id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description="Quiz ID",
            required=True,
        )
    ],
    responses={
        200: OpenApiResponse(
            response=QuizDetailSerializer,
            description="Quiz details for passing.",
            examples=[
                OpenApiExample(
                    "Quiz Passing",
                    value={
                        "id": 1,
                        "course": 1,
                        "lesson": None,
                        "title": "Python Basics Quiz",
                        "description": "Answer questions to complete module.",
                        "is_free": True,
                        "cost": None,
                        "image": None,
                        "questions": [
                            {
                                "id": 10,
                                "type": "single",
                                "content": {"type": "doc", "content": []},
                                "image": None,
                                "options": ["A", "B", "C"],
                                "score": 1,
                            }
                        ],
                    },
                )
            ],
        ),
        401: OpenApiResponse(description="Unauthorized"),
        403: OpenApiResponse(description="Forbidden"),
        404: OpenApiResponse(description="Not Found"),
    },
)
class QuizDetailView(QuizAccessMixin, APIView):
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAdminUserOnly()]
        return super().get_permissions()

    def get(self, request, id):
        quiz = self.get_quiz(id)
        self.ensure_pass_access(request, quiz)
        return Response(QuizDetailSerializer(quiz).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Quizzes"],
        summary="Delete quiz",
        description="Deletes a quiz and all its questions. Only admin users can delete quizzes.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="Quiz ID",
                required=True,
            )
        ],
        responses={
            204: OpenApiResponse(description="Quiz deleted successfully."),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def delete(self, request, id):
        quiz = self.get_quiz(id)
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Quizzes"],
    summary="Get quiz for editing",
    description=(
        "Returns complete quiz payload for editing by admin users, including "
        "question `correct` answers and `explanation`."
    ),
    parameters=[
        OpenApiParameter(
            name="id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description="Quiz ID",
            required=True,
        )
    ],
    responses={
        200: OpenApiResponse(response=QuizEditSerializer, description="Editable quiz payload."),
        401: OpenApiResponse(description="Unauthorized"),
        403: OpenApiResponse(description="Forbidden"),
        404: OpenApiResponse(description="Not Found"),
    },
)
class QuizEditView(QuizAccessMixin, APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request, id):
        quiz = self.get_quiz(id)
        return Response(QuizEditSerializer(quiz).data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Quizzes"],
    summary="Full update quiz with questions",
    description=(
        "Updates quiz fields and synchronizes nested questions in one transaction:\n"
        "- Updates existing questions by `id`\n"
        "- Creates new questions without `id`\n"
        "- Deletes removed questions"
    ),
    parameters=[
        OpenApiParameter(
            name="id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description="Quiz ID",
            required=True,
        )
    ],
    request=QuizEditSerializer,
    responses={
        200: OpenApiResponse(
            response=QuizEditSerializer,
            description="Quiz and questions updated successfully.",
            examples=[
                OpenApiExample(
                    "Quiz Full Update",
                    value={
                        "id": 1,
                        "course": 1,
                        "lesson": None,
                        "title": "Python Basics Quiz (Updated)",
                        "description": "Updated quiz content.",
                        "is_free": False,
                        "cost": "7.99",
                        "image": None,
                        "questions": [
                            {
                                "id": 1,
                                "type": "single",
                                "content": {"type": "doc", "content": []},
                                "image": None,
                                "options": ["A", "B", "C"],
                                "correct": [1],
                                "score": 2,
                                "explanation": "B is correct because ...",
                            },
                            {
                                "type": "multiple",
                                "content": {"type": "doc", "content": []},
                                "image": None,
                                "options": ["X", "Y", "Z"],
                                "correct": [0, 2],
                                "score": 3,
                                "explanation": "X and Z are correct.",
                            },
                        ],
                    },
                )
            ],
        ),
        400: OpenApiResponse(description="Bad Request"),
        401: OpenApiResponse(description="Unauthorized"),
        403: OpenApiResponse(description="Forbidden"),
        404: OpenApiResponse(description="Not Found"),
    },
)
class QuizFullUpdateView(QuizAccessMixin, APIView):
    permission_classes = [IsAdminUserOnly]

    def put(self, request, id):
        quiz = self.get_quiz(id)
        serializer = QuizEditSerializer(instance=quiz, data=request.data)
        serializer.is_valid(raise_exception=True)
        quiz = update_quiz_with_questions(quiz=quiz, validated_data=serializer.validated_data)
        return Response(QuizEditSerializer(quiz).data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Quizzes"],
    summary="Check quiz answers",
    description=(
        "Checks submitted answers and returns per-question grading details. "
        "Public for free quizzes, otherwise requires authentication and active subscription."
    ),
    parameters=[
        OpenApiParameter(
            name="id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description="Quiz ID",
            required=True,
        )
    ],
    request=QuizCheckSerializer,
    responses={
        200: OpenApiResponse(
            response=QuizCheckResultSerializer(many=True),
            description="Per-question grading result.",
            examples=[
                OpenApiExample(
                    "Quiz Check",
                    value=[
                        {
                            "question_id": 42,
                            "is_correct": True,
                            "score": 1,
                            "explanation": "Option B is the correct one.",
                            "correct_answer": [1],
                        }
                    ],
                )
            ],
        ),
        400: OpenApiResponse(description="Bad Request"),
        401: OpenApiResponse(description="Unauthorized"),
        403: OpenApiResponse(description="Forbidden"),
        404: OpenApiResponse(description="Not Found"),
    },
)
class QuizCheckView(QuizAccessMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, id):
        quiz = self.get_quiz(id)
        self.ensure_pass_access(request, quiz)

        serializer = QuizCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = check_quiz_answers(quiz=quiz, answers=serializer.validated_data["answers"])
        return Response(result, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Quizzes"],
    summary="List questions with filters",
    description=(
        "Returns all questions with optional filters. "
        "Use query params to filter by quiz, question type, and score range."
    ),
    parameters=[
        OpenApiParameter("quiz_id", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Filter by quiz ID"),
        OpenApiParameter(
            "type",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Filter by question type: single, multiple, ordering",
        ),
        OpenApiParameter("min_score", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Minimum score (1-5)"),
        OpenApiParameter("max_score", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Maximum score (1-5)"),
    ],
    responses={
        200: OpenApiResponse(
            response=QuestionCRUDSerializer(many=True),
            description="Filtered question list.",
            examples=[
                OpenApiExample(
                    "Questions List",
                    value=[
                        {
                            "id": 12,
                            "quiz": 1,
                            "type": "single",
                            "content": {"type": "doc", "content": []},
                            "image": None,
                            "options": ["A", "B", "C"],
                            "correct": [1],
                            "score": 2,
                            "explanation": "B is the correct answer.",
                        }
                    ],
                )
            ],
        ),
        400: OpenApiResponse(description="Bad Request"),
    },
)
class QuestionListView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        filters = QuestionFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        data = filters.validated_data
        queryset = get_filtered_questions(
            quiz_id=data.get("quiz_id"),
            question_type=data.get("type"),
            min_score=data.get("min_score"),
            max_score=data.get("max_score"),
        )
        return Response(QuestionCRUDSerializer(queryset, many=True).data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Quizzes"],
    summary="Create multiple questions",
    description=(
        "Creates several questions in a single request for a specific quiz. "
        "Only admin users can create questions."
    ),
    request=QuestionBulkCreateSerializer,
    responses={
        201: OpenApiResponse(
            response=QuestionCRUDSerializer(many=True),
            description="Questions created successfully.",
            examples=[
                OpenApiExample(
                    "Bulk Create Questions",
                    value=[
                        {
                            "id": 50,
                            "quiz": 1,
                            "type": "single",
                            "content": {"type": "doc", "content": []},
                            "image": None,
                            "options": ["A", "B", "C"],
                            "correct": [1],
                            "score": 2,
                            "explanation": "B is correct.",
                        },
                        {
                            "id": 51,
                            "quiz": 1,
                            "type": "multiple",
                            "content": {"type": "doc", "content": []},
                            "image": None,
                            "options": ["X", "Y", "Z"],
                            "correct": [0, 2],
                            "score": 3,
                            "explanation": "X and Z are correct.",
                        },
                    ],
                )
            ],
        ),
        400: OpenApiResponse(description="Bad Request"),
        401: OpenApiResponse(description="Unauthorized"),
        403: OpenApiResponse(description="Forbidden"),
    },
)
class QuestionBulkCreateView(APIView):
    permission_classes = [IsAdminUserOnly]

    def post(self, request):
        serializer = QuestionBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quiz = serializer.validated_data["quiz"]
        questions_data = serializer.validated_data["questions"]

        created = bulk_create_questions(quiz=quiz, questions_data=questions_data)
        return Response(QuestionCRUDSerializer(created, many=True).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Quizzes"],
    summary="Get question",
    description="Returns one question by ID. Admin only.",
    parameters=[
        OpenApiParameter("id", OpenApiTypes.INT, OpenApiParameter.PATH, description="Question ID", required=True)
    ],
    responses={
        200: OpenApiResponse(response=QuestionCRUDSerializer, description="Question details."),
        401: OpenApiResponse(description="Unauthorized"),
        403: OpenApiResponse(description="Forbidden"),
        404: OpenApiResponse(description="Not Found"),
    },
)
class QuestionDetailView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get_object(self, question_id):
        from .models import Question

        return get_object_or_404(Question.objects.select_related("quiz"), id=question_id)

    def get(self, request, id):
        question = self.get_object(id)
        return Response(QuestionCRUDSerializer(question).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Quizzes"],
        summary="Update question",
        description="Updates an existing question by ID. Admin only.",
        request=QuestionCRUDSerializer,
        responses={
            200: OpenApiResponse(response=QuestionCRUDSerializer, description="Question updated successfully."),
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def put(self, request, id):
        question = self.get_object(id)
        serializer = QuestionCRUDSerializer(question, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Quizzes"],
        summary="Delete question",
        description="Deletes an existing question by ID. Admin only.",
        responses={
            204: OpenApiResponse(description="Question deleted successfully."),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def delete(self, request, id):
        question = self.get_object(id)
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
