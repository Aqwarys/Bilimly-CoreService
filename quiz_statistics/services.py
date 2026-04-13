from django.db import transaction
from django.db.models import QuerySet, Sum
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound

from quizzes.models import Quiz

from .models import UserAnswer, UserAttempt


def calculate_score(results: list[dict]) -> int:
    return sum(item["score"] for item in results if item.get("is_correct"))


@transaction.atomic
def create_attempt(*, user, quiz: Quiz, answers: list[dict], results: list[dict]) -> UserAttempt:
    score = calculate_score(results)
    attempt = UserAttempt.objects.create(
        user=user,
        quiz=quiz,
        score=score,
        is_completed=True,
    )

    question_to_selected = {item["question_id"]: item.get("selected", []) for item in answers}
    answers_payload = [
        UserAnswer(
            attempt=attempt,
            question_id=result["question_id"],
            selected_options=question_to_selected.get(result["question_id"], []),
            is_correct=result["is_correct"],
        )
        for result in results
    ]
    UserAnswer.objects.bulk_create(answers_payload, batch_size=500)
    return attempt


def get_user_attempt(*, user, quiz: Quiz) -> UserAttempt | None:
    return (
        UserAttempt.objects.filter(user=user, quiz=quiz, is_completed=True)
        .select_related("quiz", "user")
        .prefetch_related("answers__question")
        .order_by("-created_at")
        .first()
    )


@transaction.atomic
def delete_user_attempt(*, user, quiz_id: int) -> int:
    deleted_count, _ = UserAttempt.objects.filter(user=user, quiz_id=quiz_id).delete()
    if deleted_count == 0:
        raise NotFound("No attempts found for this quiz.")
    return deleted_count


def get_user_statistics(*, user) -> dict:
    attempts_qs: QuerySet[UserAttempt] = (
        UserAttempt.objects.filter(user=user, is_completed=True)
        .select_related("quiz", "user")
        .prefetch_related("answers", "answers__question")
        .order_by("-created_at")
    )
    aggregates = attempts_qs.aggregate(total_score=Sum("score"))
    total_score = aggregates["total_score"] or 0
    total_quizzes_passed = attempts_qs.values("quiz_id").distinct().count()
    return {
        "total_score": total_score,
        "total_quizzes_passed": total_quizzes_passed,
        "attempts": list(attempts_qs),
    }


def get_user_attempted_quizzes(*, user) -> QuerySet[Quiz]:
    return (
        Quiz.objects.filter(attempts__user=user)
        .select_related("course", "lesson")
        .prefetch_related("questions")
        .distinct()
        .order_by("id")
    )


def get_quiz_by_course_id(*, course_id: int) -> Quiz:
    return get_object_or_404(
        Quiz.objects.select_related("course", "lesson").prefetch_related("questions"),
        course_id=course_id,
    )


def get_quiz_by_lesson_id(*, lesson_id: int) -> Quiz:
    return get_object_or_404(
        Quiz.objects.select_related("course", "lesson").prefetch_related("questions"),
        lesson_id=lesson_id,
    )
