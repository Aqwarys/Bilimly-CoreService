"""
Services module for lessons app.

Contains business logic functions that can be reused across views.
"""

import json
import logging
from typing import Any

import requests
from django.conf import settings
from django.db import transaction


def cleanup_unused_images(lesson):
    """
    Remove unused LessonImage records for a lesson.

    Compares images in Lesson.content with LessonImage records
    and deletes any LessonImage records that are not referenced
    in the content.

    Args:
        lesson (Lesson): The lesson instance to clean up images for.

    Returns:
        int: Number of images deleted.
    """
    from django.core.files.storage import default_storage

    # Get all image URLs referenced in the lesson content
    used_image_urls = set()

    if lesson.content:
        # Extract image URLs from TipTap JSON content
        # TipTap stores images as nodes with type "image" and src attribute
        used_image_urls = _extract_image_urls_from_content(lesson.content)

    # Get all LessonImage records for this lesson
    existing_images = lesson.images.all()

    deleted_count = 0

    # Delete LessonImage records that are not referenced in content
    for lesson_image in existing_images:
        # Construct the URL that would be used in content
        image_url = lesson_image.image.url

        if image_url not in used_image_urls:
            # Delete the file from storage
            if default_storage.exists(lesson_image.image.name):
                default_storage.delete(lesson_image.image.name)

            # Delete the LessonImage record
            lesson_image.delete()
            deleted_count += 1

    return deleted_count


def _extract_image_urls_from_content(content):
    """
    Extract image URLs from TipTap editor JSON content.

    TipTap stores images as nodes with type "image" and src attribute.
    This function recursively traverses the JSON structure to find all image URLs.

    Args:
        content (dict): TipTap editor content in JSON format.

    Returns:
        set: Set of image URLs found in the content.
    """
    image_urls = set()

    def traverse_node(node):
        if isinstance(node, dict):
            # Check if this is an image node
            if node.get("type") == "image" and "attrs" in node:
                src = node["attrs"].get("src")
                if src:
                    image_urls.add(src)

            # Recursively traverse children
            for key, value in node.items():
                if key != "attrs":  # Skip attrs as we've already processed it
                    traverse_node(value)

        elif isinstance(node, list):
            # Traverse array items
            for item in node:
                traverse_node(item)

    # Start traversal from the root content
    if isinstance(content, dict) and "content" in content:
        traverse_node(content["content"])
    elif isinstance(content, list):
        for item in content:
            traverse_node(item)

    return image_urls


logger = logging.getLogger(__name__)


def _truncate_for_log(value: Any, max_len: int = 2000) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=True)
    else:
        text = str(value)
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}...<truncated>"


def call_llm_service(payload: dict[str, Any]) -> dict[str, Any] | None:
    base_url = getattr(settings, "LLM_SERVICE_URL", None)
    if not base_url:
        logger.warning("LLM_SERVICE_URL is not configured")
        return None

    endpoint = f"{base_url.rstrip('/')}/quizzes/questions/generate/1"

    for attempt in range(2):
        try:
            response = requests.post(endpoint, json=payload, timeout=20)
            if response.status_code >= 400:
                logger.warning(
                    "LLM service returned status=%s on attempt=%s",
                    response.status_code,
                    attempt + 1,
                )
                logger.info(
                    "LLM error response body=%s",
                    _truncate_for_log(response.text),
                )
                continue
            data = response.json()
            if not isinstance(data, dict):
                logger.warning("LLM service returned non-object JSON")
                return None
            logger.info("LLM response payload=%s", _truncate_for_log(data))
            return data
        except requests.RequestException:
            logger.exception("LLM service request failed on attempt=%s", attempt + 1)
        except ValueError:
            logger.exception(
                "LLM service returned invalid JSON on attempt=%s", attempt + 1
            )

    return None


def validate_llm_question(data: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    required_fields = {"type", "content", "options", "correct", "explanation"}
    if not isinstance(data, dict) or not required_fields.issubset(data.keys()):
        return None, "missing required fields"

    q_type = data.get("type")
    if q_type not in {"single", "multiple", "ordering"}:
        return None, "invalid type"

    content = data.get("content")
    if not isinstance(content, (list, dict)):
        return None, "invalid content"

    options = data.get("options")
    if not isinstance(options, list) or len(options) == 0 or len(options) > 15:
        return None, "invalid options"

    correct = data.get("correct")
    if isinstance(correct, int):
        correct = [correct]
    if not isinstance(correct, list) or not all(isinstance(i, int) for i in correct):
        return None, "invalid correct"

    if any(i < 0 or i >= len(options) for i in correct):
        return None, "correct index out of range"

    if q_type == "single" and len(correct) != 1:
        return None, "single question must have one correct"
    if q_type == "multiple" and len(correct) < 1:
        return None, "multiple question must have at least one correct"
    if q_type == "ordering" and correct != list(range(len(options))):
        return None, "ordering correct must match full order"

    explanation = data.get("explanation")
    if (
        not isinstance(explanation, str)
        or len(explanation) == 0
        or len(explanation) > 256
    ):
        return None, "invalid explanation"

    payload: dict[str, Any] = {
        "type": q_type,
        "content": content,
        "options": options,
        "correct": correct,
        "explanation": explanation,
    }

    score = data.get("score", 1)
    if isinstance(score, int) and 1 <= score <= 5:
        payload["score"] = score

    return payload, "ok"


@transaction.atomic
def save_questions_to_quiz(quiz, questions: list[dict[str, Any]]) -> int:
    from quizzes.models import Question

    created_count = 0
    for payload in questions:
        question = Question(quiz=quiz, **payload)
        question.full_clean()
        question.save()
        created_count += 1
    return created_count


def generate_quiz_from_lesson(lesson) -> None:
    from quizzes.models import Quiz

    quiz = Quiz(
        lesson=lesson,
        title=f"{lesson.title} Quiz {lesson.id}",
        description=f"Auto-generated quiz for {lesson.title}",
        is_free=True,
    )
    quiz.full_clean()
    quiz.save()

    payload = {
        "lesson_text": lesson.content,
        "questions_count": lesson.generated_questions_count or 3,
        "title_hint": lesson.title,
    }

    response = call_llm_service(payload)
    if not response:
        logger.warning("LLM response missing; deleting quiz_id=%s", quiz.id)
        quiz.delete()
        return

    questions = response.get("questions")
    if not isinstance(questions, list):
        logger.warning(
            "LLM response has invalid questions payload; deleting quiz_id=%s", quiz.id
        )
        quiz.delete()
        return

    valid_questions: list[dict[str, Any]] = []
    for idx, question_data in enumerate(questions, start=1):
        cleaned, reason = validate_llm_question(question_data)
        if cleaned is None:
            logger.warning(
                "Skipping invalid LLM question index=%s for quiz_id=%s reason=%s data=%s",
                idx,
                quiz.id,
                reason,
                _truncate_for_log(question_data),
            )
            continue
        valid_questions.append(cleaned)

    if not valid_questions:
        logger.warning("No valid questions generated; deleting quiz_id=%s", quiz.id)
        quiz.delete()
        return

    try:
        save_questions_to_quiz(quiz, valid_questions)
    except Exception:
        logger.exception("Failed saving questions for quiz_id=%s", quiz.id)
        quiz.delete()
