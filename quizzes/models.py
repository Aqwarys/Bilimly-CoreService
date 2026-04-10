from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from courses.models import Course
from lessons.models import Lesson


class Quiz(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["is_free"]),
            models.Index(fields=["course"]),
            models.Index(fields=["lesson"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(course__isnull=False) & Q(lesson__isnull=True))
                    | (Q(course__isnull=True) & Q(lesson__isnull=False))
                ),
                name="quiz_exactly_one_target",
            ),
            models.CheckConstraint(
                condition=Q(is_free=True) | Q(cost__isnull=False),
                name="quiz_cost_required_when_paid",
            ),
        ]

    course = models.ForeignKey(
        Course,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="quizzes",
    )
    lesson = models.ForeignKey(
        Lesson,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="quizzes",
    )
    title = models.CharField(max_length=256, unique=True)
    description = models.CharField(max_length=512)
    is_free = models.BooleanField(default=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to="quizzes/", null=True, blank=True)

    def __str__(self):
        return self.title

    def clean(self):
        if (self.course is None and self.lesson is None) or (
            self.course is not None and self.lesson is not None
        ):
            raise ValidationError("Exactly one of 'course' or 'lesson' must be set.")

        if not self.is_free and self.cost is None:
            raise ValidationError({"cost": "Cost is required for paid quizzes."})

        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Question(models.Model):
    class QuestionType(models.TextChoices):
        SINGLE = "single", "Single"
        MULTIPLE = "multiple", "Multiple"
        ORDERING = "ordering", "Ordering"

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    type = models.CharField(max_length=16, choices=QuestionType.choices)
    content = models.JSONField(default=dict)
    image = models.ImageField(upload_to="questions/", null=True, blank=True)
    options = models.JSONField(default=list)
    correct = models.JSONField(default=list)
    score = models.IntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    explanation = models.CharField(max_length=256)

    class Meta:
        indexes = [
            models.Index(fields=["quiz"]),
            models.Index(fields=["type"]),
        ]

    def __str__(self):
        return f"Question #{self.pk} ({self.type})"

    def clean(self):
        if not isinstance(self.options, list):
            raise ValidationError({"options": "Options must be a list."})
        if len(self.options) > 15:
            raise ValidationError({"options": "Options length must be less than or equal to 15."})

        if not isinstance(self.correct, list):
            raise ValidationError({"correct": "Correct must be a list of indexes."})
        if not all(isinstance(i, int) for i in self.correct):
            raise ValidationError({"correct": "All correct indexes must be integers."})

        option_count = len(self.options)
        if any(i < 0 or i >= option_count for i in self.correct):
            raise ValidationError({"correct": "Correct indexes must exist in options."})

        if self.type == self.QuestionType.SINGLE and len(self.correct) != 1:
            raise ValidationError({"correct": "Single question must have exactly one correct index."})

        if self.type == self.QuestionType.MULTIPLE and len(self.correct) < 1:
            raise ValidationError({"correct": "Multiple question must have at least one correct index."})

        if self.type == self.QuestionType.ORDERING:
            expected = list(range(option_count))
            if self.correct != expected:
                raise ValidationError(
                    {"correct": "Ordering question must contain all option indexes in exact order."}
                )

        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
