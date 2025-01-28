from rest_framework import permissions


class IsAdminAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """Проверка разрешений для админа и автора или на чтение."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_admin()
            or obj.author == request.user
        )
