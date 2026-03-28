from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
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
        help_text="Course this lesson belongs to."
    )
    title = models.CharField(
        max_length=256,
        help_text="Lesson title."
    )
    content = models.JSONField(
        default=dict,
        help_text="Lesson content in TipTap editor format (JSON)."
    )
    image = models.ImageField(
        upload_to="lessons/",
        null=True,
        blank=True,
        help_text="Main lesson image."
    )
    is_draft = models.BooleanField(
        default=True,
        help_text="Whether the lesson is in draft state."
    )
    auto_test = models.BooleanField(
        default=False,
        help_text="Whether the lesson has auto-testing enabled."
    )
    priority = models.IntegerField(
        default=1,
        help_text="Order of the lesson within the course."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this lesson was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this lesson was last updated."
    )

    class Meta:
        ordering = ["priority"]
        indexes = [
            models.Index(fields=["course", "priority"]),
            models.Index(fields=["is_draft"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "priority"],
                name="unique_lesson_priority_per_course"
            )
        ]

    def __str__(self):
        return f"{self.course.name} - {self.title}"

    def clean(self):
        # Validation: Lesson must belong to a course
        if not self.course:
            raise ValidationError("Lesson must belong to a course.")

        # Validation: Cannot publish without content
        if not self.is_draft and not self.content:
            raise ValidationError("Cannot publish lesson without content.")

        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()  # Run validation

        # Auto-increment priority if not set or creating new lesson
        if not self.pk or self.priority is None:
            max_priority = Lesson.objects.filter(course=self.course).aggregate(
                models.Max('priority')
            )['priority__max'] or 0
            self.priority = max_priority + 1

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
        help_text="Lesson this image belongs to."
    )
    image = models.ImageField(
        upload_to="lesson_images/",
        help_text="Image file for the lesson."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this image was uploaded."
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["lesson"]),
        ]

    def __str__(self):
        return f"Image for {self.lesson.title}"