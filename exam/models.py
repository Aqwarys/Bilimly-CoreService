from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.text import slugify


class Subject(models.Model):
    class SubjectType(models.TextChoices):
        MANDATORY = "MANDATORY", "Mandatory"
        PROFILE = "PROFILE", "Profile"

    name = models.CharField(max_length=256, unique=True, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.CharField(max_length=256, null=True, blank=True)
    type = models.CharField(max_length=16, choices=SubjectType.choices)
    duration_sec = models.IntegerField(validators=[MinValueValidator(1)])
    max_score = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["type"]),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self):
        if self.duration_sec is None:
            raise ValidationError({"duration_sec": "Duration is required."})
        if self.duration_sec <= 0:
            raise ValidationError({"duration_sec": "Duration must be greater than 0."})
        if self.max_score is None:
            raise ValidationError({"max_score": "Max score is required."})
        if self.max_score <= 0:
            raise ValidationError({"max_score": "Max score must be greater than 0."})
        super().clean()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()
        return super().save(*args, **kwargs)


class Module(models.Model):
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="modules"
    )
    title = models.CharField(max_length=256)

    class Meta:
        ordering = ["title"]
        indexes = [
            models.Index(fields=["subject"]),
        ]

    def __str__(self) -> str:
        return f"{self.subject.name}: {self.title}"


class Problem(models.Model):
    class ProblemType(models.TextChoices):
        SINGLE = "single", "Single"
        MULTIPLE = "multiple", "Multiple"
        ORDERING = "ordering", "Ordering"

    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="problems"
    )
    content = models.JSONField(default=dict)
    type = models.CharField(max_length=16, choices=ProblemType.choices)
    image = models.ImageField(upload_to="exam/problems/images/", null=True, blank=True)
    audio = models.FileField(
        upload_to="exam/problems/audio/",
        null=True,
        blank=True,
        validators=[FileExtensionValidator(["mp3", "wav"])],
    )
    options = models.JSONField(default=list)
    correct = models.JSONField(default=list)
    score = models.IntegerField(default=1, editable=False)
    explanation = models.CharField(max_length=512)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["module"]),
            models.Index(fields=["type"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(score=1), name="exam_problem_score_fixed_one"
            ),
        ]

    def __str__(self) -> str:
        return f"Problem #{self.pk} ({self.type})"

    def clean(self):
        if not isinstance(self.options, list):
            raise ValidationError({"options": "Options must be a list."})
        if len(self.options) > 15:
            raise ValidationError(
                {"options": "Options length must be less than or equal to 15."}
            )

        if not isinstance(self.correct, list):
            raise ValidationError({"correct": "Correct must be a list of indexes."})
        if not all(isinstance(i, int) for i in self.correct):
            raise ValidationError({"correct": "All correct indexes must be integers."})

        option_count = len(self.options)
        if any(i < 0 or i >= option_count for i in self.correct):
            raise ValidationError({"correct": "Correct indexes must exist in options."})

        if self.type == self.ProblemType.SINGLE and len(self.correct) != 1:
            raise ValidationError(
                {"correct": "Single problem must have exactly one correct index."}
            )

        if self.type == self.ProblemType.MULTIPLE and len(self.correct) < 1:
            raise ValidationError(
                {"correct": "Multiple problem must have at least one correct index."}
            )

        if self.type == self.ProblemType.ORDERING:
            expected = list(range(option_count))
            if self.correct != expected:
                raise ValidationError(
                    {
                        "correct": "Ordering problem must contain all option indexes in exact order."
                    }
                )

        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
