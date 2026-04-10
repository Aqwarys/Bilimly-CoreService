from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("courses", "0001_initial"),
        ("lessons", "0003_alter_lesson_content"),
    ]

    operations = [
        migrations.CreateModel(
            name="Quiz",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=256, unique=True)),
                ("description", models.CharField(max_length=512)),
                ("is_free", models.BooleanField(default=True)),
                (
                    "cost",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "image",
                    models.ImageField(blank=True, null=True, upload_to="quizzes/"),
                ),
                (
                    "course",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quizzes",
                        to="courses.course",
                    ),
                ),
                (
                    "lesson",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quizzes",
                        to="lessons.lesson",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["is_free"], name="quizzes_qui_is_free_0868a3_idx"),
                    models.Index(fields=["course"], name="quizzes_qui_course__40d7d6_idx"),
                    models.Index(fields=["lesson"], name="quizzes_qui_lesson__51c158_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("single", "Single"),
                            ("multiple", "Multiple"),
                            ("ordering", "Ordering"),
                        ],
                        max_length=16,
                    ),
                ),
                ("content", models.JSONField(default=dict)),
                (
                    "image",
                    models.ImageField(blank=True, null=True, upload_to="questions/"),
                ),
                ("options", models.JSONField(default=list)),
                ("correct", models.JSONField(default=list)),
                (
                    "score",
                    models.IntegerField(
                        default=1,
                        validators=[MinValueValidator(1), MaxValueValidator(5)],
                    ),
                ),
                ("explanation", models.CharField(max_length=256)),
                (
                    "quiz",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="questions",
                        to="quizzes.quiz",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["quiz"], name="quizzes_que_quiz_id_ffb3fb_idx"),
                    models.Index(fields=["type"], name="quizzes_que_type_f3b953_idx"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="quiz",
            constraint=models.CheckConstraint(
                condition=(
                    (django.db.models.Q(course__isnull=False) & django.db.models.Q(lesson__isnull=True))
                    | (django.db.models.Q(course__isnull=True) & django.db.models.Q(lesson__isnull=False))
                ),
                name="quiz_exactly_one_target",
            ),
        ),
        migrations.AddConstraint(
            model_name="quiz",
            constraint=models.CheckConstraint(
                condition=django.db.models.Q(is_free=True) | django.db.models.Q(cost__isnull=False),
                name="quiz_cost_required_when_paid",
            ),
        ),
    ]
