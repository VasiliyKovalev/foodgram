from rest_framework import permissions


class IsAdminOnly(permissions.BasePermission):
    """Проверка разрешений для админа."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin()


class IsAdminOrReadOnly(permissions.BasePermission):
    """Проверка разрешений для админа или на чтение."""

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated and request.user.is_admin())
        )


class IsAdminAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """Проверка разрешений для админа и автора или на чтение."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_admin()
            or obj.author == request.user
        )
