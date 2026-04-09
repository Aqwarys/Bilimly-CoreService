from typing import Any

from django.db import transaction
from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError

from .models import Question, Quiz


def validate_quiz_data(data: dict[str, Any]) -> None:
    course = data.get("course")
    lesson = data.get("lesson")
    is_free = data.get("is_free", True)
    cost = data.get("cost")

    if bool(course) == bool(lesson):
        raise ValidationError("Exactly one of 'course' or 'lesson' must be provided.")

    if is_free is False and cost is None:
        raise ValidationError({"cost": "Cost is required when quiz is not free."})


@transaction.atomic
def update_quiz_with_questions(quiz: Quiz, validated_data: dict[str, Any]) -> Quiz:
    questions_data = validated_data.pop("questions", None)

    for field, value in validated_data.items():
        setattr(quiz, field, value)
    quiz.full_clean()
    quiz.save()

    if questions_data is None:
        return quiz

    incoming_ids = set()
    for question_payload in questions_data:
        question_id = question_payload.pop("id", None)
        if question_id is not None:
            incoming_ids.add(question_id)
            try:
                question = quiz.questions.get(id=question_id)
            except Question.DoesNotExist as exc:
                raise ValidationError(
                    {"questions": [f"Question with id={question_id} does not belong to this quiz."]}
                ) from exc

            for field, value in question_payload.items():
                setattr(question, field, value)
            question.full_clean()
            question.save()
        else:
            question = Question(quiz=quiz, **question_payload)
            question.full_clean()
            question.save()
            incoming_ids.add(question.id)

    quiz.questions.exclude(id__in=incoming_ids).delete()
    return quiz


def _normalize_selected(selected: list[int]) -> list[int]:
    if not isinstance(selected, list) or not all(isinstance(v, int) for v in selected):
        raise ValidationError("Each 'selected' value must be an array of integer indexes.")
    return selected


def check_quiz_answers(quiz: Quiz, answers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    questions_map = {question.id: question for question in quiz.questions.all()}
    response: list[dict[str, Any]] = []

    for answer in answers:
        question_id = answer.get("question_id")
        selected = _normalize_selected(answer.get("selected", []))

        question = questions_map.get(question_id)
        if question is None:
            raise ValidationError({"answers": [f"Question with id={question_id} was not found in this quiz."]})

        if question.type == Question.QuestionType.SINGLE:
            is_correct = selected == question.correct
        elif question.type == Question.QuestionType.MULTIPLE:
            is_correct = set(selected) == set(question.correct)
        else:
            is_correct = selected == question.correct

        response.append(
            {
                "question_id": question.id,
                "is_correct": is_correct,
                "score": question.score if is_correct else 0,
                "explanation": question.explanation,
                "correct_answer": question.correct,
            }
        )

    return response


@transaction.atomic
def bulk_create_questions(quiz: Quiz, questions_data: list[dict[str, Any]]) -> list[Question]:
    created_questions: list[Question] = []
    for payload in questions_data:
        question = Question(quiz=quiz, **payload)
        question.full_clean()
        question.save()
        created_questions.append(question)
    return created_questions


def get_filtered_questions(
    *,
    quiz_id: int | None = None,
    question_type: str | None = None,
    min_score: int | None = None,
    max_score: int | None = None,
) -> QuerySet[Question]:
    queryset = Question.objects.select_related("quiz").all()

    if quiz_id is not None:
        queryset = queryset.filter(quiz_id=quiz_id)
    if question_type:
        queryset = queryset.filter(type=question_type)
    if min_score is not None:
        queryset = queryset.filter(score__gte=min_score)
    if max_score is not None:
        queryset = queryset.filter(score__lte=max_score)

    return queryset.order_by("quiz_id", "id")
