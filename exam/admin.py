from django.contrib import admin
from django.utils.html import format_html

from .models import Module, Problem, Subject


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "duration_sec", "max_score"]
    list_filter = ["type"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ModuleInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ["title", "subject"]
    list_filter = ["subject"]
    search_fields = ["title", "subject__name"]


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ["id", "subject_name", "module", "type", "preview"]
    list_filter = ["module", "module__subject", "type"]
    search_fields = ["module__title", "module__subject__name"]

    def subject_name(self, obj):
        return obj.module.subject.name

    subject_name.short_description = "Subject"

    def preview(self, obj):
        content_text = str(obj.content)
        if content_text:
            return content_text[:80]
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No preview"

    preview.short_description = "Preview"
