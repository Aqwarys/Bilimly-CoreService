"""
Permissions module for lessons app.

Contains custom permission classes for lesson-related endpoints.
"""
from rest_framework.permissions import BasePermission


class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.

    This is a custom implementation that provides more specific error messages
    for lesson-related endpoints.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True


class IsAdminUserOnly(BasePermission):
    """
    Allows access only to admin users (is_staff == True).

    Restricts access to admin-only endpoints for lesson management.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff
