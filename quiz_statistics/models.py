from django.conf import settings
from django.db import models


class UserAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    quiz = models.ForeignKey(
        "quizzes.Quiz",
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    score = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "quiz"]),
            models.Index(fields=["quiz", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["is_completed"]),
        ]
        ordering = ["-created_at"]


class UserAnswer(models.Model):
    attempt = models.ForeignKey(
        UserAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        "quizzes.Question",
        on_delete=models.CASCADE,
        related_name="user_answers",
    )
    selected_options = models.JSONField(default=list)
    is_correct = models.BooleanField()

    class Meta:
        indexes = [
            models.Index(fields=["attempt", "question"]),
            models.Index(fields=["question"]),
            models.Index(fields=["is_correct"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"],
                name="unique_question_per_attempt",
            )
        ]
