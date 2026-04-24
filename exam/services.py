from __future__ import annotations

import random
from typing import Any

from django.db.models import Prefetch, QuerySet
from rest_framework.exceptions import ValidationError

from .models import Module, Problem, Subject


def distribute_questions(total_questions: int, module_count: int) -> list[int]:
    if total_questions <= 0:
        raise ValidationError("Total questions must be greater than 0.")
    if module_count <= 0:
        raise ValidationError("Subject must have at least one module.")

    base = total_questions // module_count
    remainder = total_questions % module_count
    return [base + 1 if index < remainder else base for index in range(module_count)]


def shuffle_questions(problems: list[Problem]) -> list[Problem]:
    random.shuffle(problems)
    return problems


def _get_subjects_for_exam(subject: Subject) -> QuerySet[Subject]:
    if subject.type == Subject.SubjectType.PROFILE:
        return (
            Subject.objects.filter(id=subject.id)
            | Subject.objects.filter(type=Subject.SubjectType.MANDATORY)
        ).distinct()
    return Subject.objects.filter(id=subject.id)


def build_exam(subject: Subject) -> dict[str, Any]:
    subjects = (
        _get_subjects_for_exam(subject)
        .prefetch_related(
            Prefetch(
                "modules",
                queryset=Module.objects.prefetch_related(
                    Prefetch(
                        "problems",
                        queryset=Problem.objects.only(
                            "id",
                            "type",
                            "content",
                            "image",
                            "audio",
                            "options",
                            "correct",
                            "explanation",
                            "module_id",
                        ),
                    )
                ),
            )
        )
        .all()
    )

    response_subjects: list[dict[str, Any]] = []
    total_duration_sec = 0
    total_problem_count = 0
    total_score_sum = 0

    for exam_subject in subjects:
        modules = list(exam_subject.modules.all())
        if not modules:
            raise ValidationError(
                f"Subject '{exam_subject.name}' must have at least one module."
            )

        allocations = distribute_questions(exam_subject.max_score, len(modules))

        selected_problem_ids: list[int] = []
        for module, allocation in zip(modules, allocations):
            module_problem_ids = [problem.id for problem in module.problems.all()]
            if not module_problem_ids:
                raise ValidationError(
                    f"Module '{module.title}' in subject '{exam_subject.name}' has no problems."
                )
            if allocation > len(module_problem_ids):
                raise ValidationError(
                    f"Module '{module.title}' in subject '{exam_subject.name}' has insufficient problems."
                )
            selected_problem_ids.extend(random.sample(module_problem_ids, allocation))

        problems = list(
            Problem.objects.filter(id__in=selected_problem_ids).only(
                "id",
                "type",
                "content",
                "image",
                "audio",
                "options",
                "module_id",
            )
        )
        problems = shuffle_questions(problems)

        response_subjects.append(
            {
                "name": exam_subject.name,
                "total_problem": len(problems),
                "max_score": exam_subject.max_score,
                "problems": problems,
            }
        )

        total_duration_sec += exam_subject.duration_sec
        total_problem_count += len(problems)
        total_score_sum += exam_subject.max_score

    return {
        "total_duration_sec": total_duration_sec,
        "total_problem_count": total_problem_count,
        "total_score_sum": total_score_sum,
        "subjects": response_subjects,
    }


def _normalize_selected(selected: list[int] | None) -> list[int]:
    if selected is None:
        return []
    if not isinstance(selected, list) or not all(isinstance(v, int) for v in selected):
        raise ValidationError(
            "Each 'selected' value must be an array of integer indexes."
        )
    if len(selected) != len(set(selected)):
        raise ValidationError("Duplicate selected indexes are not allowed.")
    return selected


def check_exam_answers(payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not payload:
        raise ValidationError("Payload cannot be empty.")

    seen_subject_names: set[str] = set()
    all_problem_ids: list[int] = []

    for subject_payload in payload:
        subject_name = subject_payload.get("name")
        if subject_name in seen_subject_names:
            raise ValidationError("Duplicate subject names are not allowed.")
        seen_subject_names.add(subject_name)

        for problem_payload in subject_payload.get("problems", []):
            all_problem_ids.append(problem_payload.get("id"))

    if len(all_problem_ids) != len(set(all_problem_ids)):
        raise ValidationError("Duplicate problem ids are not allowed.")

    problems = (
        Problem.objects.select_related("module__subject")
        .filter(id__in=all_problem_ids)
        .only(
            "id",
            "type",
            "options",
            "correct",
            "explanation",
            "module__subject__name",
            "module__subject__id",
        )
    )
    problems_map = {problem.id: problem for problem in problems}

    missing_ids = [
        problem_id for problem_id in all_problem_ids if problem_id not in problems_map
    ]
    if missing_ids:
        raise ValidationError({"problems": f"Invalid problem ids: {missing_ids}."})

    response_subjects: list[dict[str, Any]] = []

    for subject_payload in payload:
        subject_name = subject_payload.get("name")
        subject_total_score = 0
        subject_problem_results: list[dict[str, Any]] = []

        for problem_payload in subject_payload.get("problems", []):
            problem_id = problem_payload.get("id")
            selected = _normalize_selected(problem_payload.get("selected"))

            problem = problems_map.get(problem_id)
            if problem is None:
                raise ValidationError(
                    {"problems": f"Problem with id={problem_id} not found."}
                )

            if problem.module.subject.name != subject_name:
                raise ValidationError(
                    {
                        "subjects": f"Problem id={problem_id} does not belong to subject '{subject_name}'."
                    }
                )

            if any(i < 0 or i >= len(problem.options) for i in selected):
                raise ValidationError(
                    {
                        "selected": f"Selected indexes must exist in options for problem id={problem_id}."
                    }
                )

            if problem.type == Problem.ProblemType.SINGLE:
                is_correct = selected == problem.correct
            elif problem.type == Problem.ProblemType.MULTIPLE:
                is_correct = set(selected) == set(problem.correct)
            else:
                is_correct = selected == problem.correct

            subject_problem_results.append(
                {
                    "id": problem.id,
                    "correct": problem.correct,
                    "selected": selected,
                    "explanation": problem.explanation,
                    "is_correct": is_correct,
                }
            )
            if is_correct:
                subject_total_score += problem.score

        response_subjects.append(
            {
                "name": subject_name,
                "total_score_get": subject_total_score,
                "problems": subject_problem_results,
            }
        )

    return response_subjects


def calculate_scores(subject_results: list[dict[str, Any]]) -> dict[str, Any]:
    total_get_score = sum(subject["total_score_get"] for subject in subject_results)

    subject_names = [subject["name"] for subject in subject_results]
    subject_score_map = {
        subject.name: subject.max_score
        for subject in Subject.objects.filter(name__in=subject_names)
    }
    total_score_sum = sum(subject_score_map.get(name, 0) for name in subject_names)

    return {
        "total_get_score": total_get_score,
        "total_score_sum": total_score_sum,
        "subjects": subject_results,
    }
