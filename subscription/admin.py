from django.contrib import admin
from .models import Tariff, Subscription


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    """Admin configuration for Tariff model."""

    list_display = ['title', 'days_count', 'cost', 'is_trial', 'created_at', 'updated_at']
    list_filter = ['is_trial', 'days_count', 'created_at']
    search_fields = ['title', 'days_count']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'days_count', 'cost', 'is_trial')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin configuration for Subscription model."""

    list_display = ['user', 'tariff', 'deadline', 'is_active', 'created_at']
    list_filter = ['tariff', 'created_at']
    search_fields = ['user__username', 'user__email', 'tariff__title']
    readonly_fields = ['deadline', 'created_at', 'is_active']
    ordering = ['-created_at']

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'tariff')
        }),
        ('Subscription Details', {
            'fields': ('deadline', 'created_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )

    def is_active(self, obj):
        """Display if subscription is active."""
        if obj is None:
            return False
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = 'Active'