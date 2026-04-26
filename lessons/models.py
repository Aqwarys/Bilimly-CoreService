import logging

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from courses.models import Course


class Lesson(models.Model):
    """
    Model representing a lesson within a course.

    Lessons are ordered by priority within a course.
    Supports draft creation and publishing workflow.
    """

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        help_text="Course this lesson belongs to.",
    )
    title = models.CharField(max_length=256, help_text="Lesson title.")
    content = models.JSONField(
        default=dict,
        blank=True,
        help_text="Lesson content in TipTap editor format (JSON).",
    )
    image = models.ImageField(
        upload_to="lessons/", null=True, blank=True, help_text="Main lesson image."
    )
    is_draft = models.BooleanField(
        default=True, help_text="Whether the lesson is in draft state."
    )
    auto_test = models.BooleanField(
        default=False, help_text="Whether the lesson has auto-testing enabled."
    )
    auto_generate_quiz = models.BooleanField(
        default=False,
        help_text="Whether to auto-generate quiz questions for this lesson.",
    )
    generated_questions_count = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Number of questions to request from the LLM (1-5).",
    )
    priority = models.IntegerField(
        default=1, help_text="Order of the lesson within the course."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="When this lesson was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="When this lesson was last updated."
    )

    class Meta:
        ordering = ["priority"]
        indexes = [
            models.Index(fields=["course", "priority"]),
            models.Index(fields=["is_draft"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "priority"], name="unique_lesson_priority_per_course"
            )
        ]

    def __str__(self):
        return f"{self.course.name} - {self.title}"

    def clean(self):
        # Validation: Lesson must belong to a course
        if not self.course:
            raise ValidationError("Lesson must belong to a course.")

        # Validation: Cannot publish without content
        # Only validate content when publishing (is_draft=False)
        # Allow empty content for drafts
        if not self.is_draft and (
            self.content is None or self.content == {} or self.content == []
        ):
            raise ValidationError("Cannot publish lesson without content.")

        super().clean()

    def save(self, *args, **kwargs):
        # Auto-increment priority if not set or creating new lesson
        if not self.pk or self.priority is None:
            # Get the highest priority for this course and add 1
            existing_priorities = set(
                Lesson.objects.filter(course=self.course).values_list(
                    "priority", flat=True
                )
            )
            # Find the next available priority starting from 1
            next_priority = 1
            while next_priority in existing_priorities:
                next_priority += 1
            self.priority = next_priority

        self.full_clean()  # Run validation after setting priority
        super().save(*args, **kwargs)


class LessonImage(models.Model):
    """
    Model representing images uploaded for a lesson.

    Used for TipTap editor image management.
    """

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="images",
        help_text="Lesson this image belongs to.",
    )
    image = models.ImageField(
        upload_to="lesson_images/", help_text="Image file for the lesson."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="When this image was uploaded."
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["lesson"]),
        ]

    def __str__(self):
        return f"Image for {self.lesson.title}"


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Lesson)
def generate_quiz_on_create(sender, instance, created, **kwargs):
    if not created or not instance.auto_generate_quiz:
        return

    try:
        from .services import generate_quiz_from_lesson

        generate_quiz_from_lesson(instance)
    except Exception:
        logger.exception("Auto quiz generation failed for lesson_id=%s", instance.id)
