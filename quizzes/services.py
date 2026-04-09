from typing import Any

from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import Question, Quiz


@transaction.atomic
def update_quiz_with_questions(*, quiz: Quiz, quiz_data: dict[str, Any], questions_data: list[dict[str, Any]]) -> Quiz:
    quiz_serializer_fields = ["title", "description", "is_free", "cost", "course", "lesson", "image"]
    for field in quiz_serializer_fields:
        if field in quiz_data:
            setattr(quiz, field, quiz_data[field])
    quiz.save()

    existing_questions = {question.id: question for question in quiz.questions.all()}
    incoming_ids: set[int] = set()

    for question_payload in questions_data:
        question_id = question_payload.get("id")

        if question_id is not None:
            if question_id not in existing_questions:
                raise ValidationError({"questions": [f"Question id={question_id} does not belong to this quiz."]})

            incoming_ids.add(question_id)
            question = existing_questions[question_id]
            for field in ["type", "content", "image", "options", "correct", "score", "explanation"]:
                if field in question_payload:
                    setattr(question, field, question_payload[field])
            question.save()
        else:
            Question.objects.create(
                quiz=quiz,
                type=question_payload["type"],
                content=question_payload["content"],
                image=question_payload.get("image"),
                options=question_payload["options"],
                correct=question_payload["correct"],
                score=question_payload.get("score", 1),
                explanation=question_payload["explanation"],
            )

    to_delete = [q_id for q_id in existing_questions if q_id not in incoming_ids]
    if to_delete:
        Question.objects.filter(id__in=to_delete, quiz=quiz).delete()

    return quiz


def check_quiz_answers(*, quiz: Quiz, answers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    answers_map = {item["question_id"]: item.get("selected", []) for item in answers}
    question_map = {question.id: question for question in quiz.questions.all()}

    unknown_question_ids = [q_id for q_id in answers_map if q_id not in question_map]
    if unknown_question_ids:
        raise ValidationError({"answers": [f"Unknown question_id(s): {unknown_question_ids}"]})

    results: list[dict[str, Any]] = []
    for question in quiz.questions.all():
        if question.id not in answers_map:
            continue

        selected = answers_map[question.id]
        correct = question.correct

        if question.type == Question.TYPE_SINGLE:
            is_correct = selected == correct
        elif question.type == Question.TYPE_MULTIPLE:
            is_correct = set(selected) == set(correct)
        elif question.type == Question.TYPE_ORDERING:
            is_correct = selected == correct
        else:
            is_correct = False

        results.append(
            {
                "question_id": question.id,
                "is_correct": is_correct,
                "score": question.score if is_correct else 0,
                "explanation": question.explanation,
                "correct_answer": question.correct,
            }
        )

    return results
