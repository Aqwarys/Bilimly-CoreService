from rest_framework.permissions import BasePermission

from subscription.models import user_has_active_subscription


class IsAdminUserOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class CanAccessQuiz(BasePermission):
    message = "Active subscription required to access this quiz."

    def has_object_permission(self, request, view, obj):
        if obj.is_free:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return user_has_active_subscription(request.user)
