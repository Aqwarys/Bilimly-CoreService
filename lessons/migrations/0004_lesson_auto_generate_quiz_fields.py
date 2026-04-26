from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ("lessons", "0003_alter_lesson_content"),
    ]

    operations = [
        migrations.AddField(
            model_name="lesson",
            name="auto_generate_quiz",
            field=models.BooleanField(
                default=False,
                help_text="Whether to auto-generate quiz questions for this lesson.",
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="generated_questions_count",
            field=models.IntegerField(
                default=3,
                help_text="Number of questions to request from the LLM (1-5).",
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(5),
                ],
            ),
        ),
    ]
