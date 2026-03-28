"""
Admin configuration for lessons app.

Registers Lesson and LessonImage models with Django admin interface.
"""
from django.contrib import admin
from .models import Lesson, LessonImage


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """
    Admin interface for Lesson model.
    """
    list_display = [
        'id',
        'title',
        'course',
        'priority',
        'is_draft',
        'auto_test'
    ]
    list_filter = [
        'is_draft',
        'auto_test',
        'course'
    ]
    search_fields = [
        'title',
        'course__name'
    ]
    readonly_fields = [
        'id'
    ]
    ordering = ['course', 'priority']

    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'title', 'priority', 'is_draft', 'auto_test')
        }),
        ('Content', {
            'fields': ('content', 'image'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )


@admin.register(LessonImage)
class LessonImageAdmin(admin.ModelAdmin):
    """
    Admin interface for LessonImage model.
    """
    list_display = [
        'id',
        'lesson',
        'image'
    ]
    list_filter = [
        'lesson'
    ]
    search_fields = [
        'lesson__title'
    ]
    readonly_fields = [
        'id'
    ]
    ordering = ['-id']

    fieldsets = (
        ('Image Information', {
            'fields': ('lesson', 'image')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
