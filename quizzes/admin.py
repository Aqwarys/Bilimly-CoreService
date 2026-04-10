from django.contrib import admin

from .models import Question, Quiz


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_free", "cost", "course", "lesson")
    search_fields = ("title",)
    list_filter = ("is_free",)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "quiz", "type", "score")
    list_filter = ("type", "score")
    search_fields = ("quiz__title",)
