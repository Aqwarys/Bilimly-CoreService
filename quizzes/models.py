from django.core.exceptions import ValidationError
from django.db import models

from courses.models import Course
from lessons.models import Lesson


class Quiz(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="quizzes",
        null=True,
        blank=True,
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="quizzes",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=256, unique=True)
    description = models.CharField(max_length=512)
    is_free = models.BooleanField(default=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to="quizzes/", null=True, blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def clean(self):
        if bool(self.course) == bool(self.lesson):
            raise ValidationError("Exactly one of course or lesson must be set.")

        if not self.is_free and self.cost is None:
            raise ValidationError("Cost is required when quiz is not free.")

        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Question(models.Model):
    TYPE_SINGLE = "single"
    TYPE_MULTIPLE = "multiple"
    TYPE_ORDERING = "ordering"

    TYPE_CHOICES = (
        (TYPE_SINGLE, "single"),
        (TYPE_MULTIPLE, "multiple"),
        (TYPE_ORDERING, "ordering"),
    )

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    content = models.JSONField()
    image = models.ImageField(upload_to="questions/", null=True, blank=True)
    options = models.JSONField()
    correct = models.JSONField()
    score = models.IntegerField(default=1)
    explanation = models.CharField(max_length=256)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Question #{self.pk or 'new'} ({self.type})"

    def clean(self):
        if not isinstance(self.options, list):
            raise ValidationError({"options": "Options must be a list."})

        if len(self.options) > 15:
            raise ValidationError({"options": "Options length must be less than or equal to 15."})

        if not isinstance(self.correct, list):
            raise ValidationError({"correct": "Correct must be a list of indexes."})

        if any(not isinstance(index, int) for index in self.correct):
            raise ValidationError({"correct": "Correct indexes must be integers."})

        if any(index < 0 or index >= len(self.options) for index in self.correct):
            raise ValidationError({"correct": "Correct indexes must reference existing options."})

        if self.score < 1 or self.score > 5:
            raise ValidationError({"score": "Score must be between 1 and 5."})

        if self.type == self.TYPE_SINGLE and len(self.correct) != 1:
            raise ValidationError({"correct": "Single type must contain exactly one correct index."})

        if self.type == self.TYPE_MULTIPLE and len(self.correct) < 1:
            raise ValidationError({"correct": "Multiple type must contain at least one correct index."})

        if self.type == self.TYPE_ORDERING:
            expected = list(range(len(self.options)))
            if sorted(self.correct) != expected or len(self.correct) != len(self.options):
                raise ValidationError(
                    {"correct": "Ordering type requires full order of all option indexes."}
                )

        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
