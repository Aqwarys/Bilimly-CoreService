from django.contrib import admin

from .models import Question, Quiz


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "course", "lesson", "is_free", "cost")
    search_fields = ("title",)
    list_filter = ("is_free",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "quiz", "type", "score")
    list_filter = ("type", "score")
    search_fields = ("explanation",)
