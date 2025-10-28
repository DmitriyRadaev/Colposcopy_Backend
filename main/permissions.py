# permissions.py
from rest_framework import permissions
from django.contrib.auth import get_user_model

Account = get_user_model()


class IsSuperAdmin(permissions.BasePermission):
    """Доступ только супер-администратору."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == Account.Role.SUPERADMIN
        )


class IsAdminOrSuperAdmin(permissions.BasePermission):
    """Доступ администраторам и супер-админам."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in [Account.Role.ADMIN, Account.Role.SUPERADMIN]
        )


class IsWorker(permissions.BasePermission):
    """Доступ только пользователям с ролью WORKER."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == Account.Role.WORKER
        )


class ReadOnly(permissions.BasePermission):
    """Разрешает только безопасные (GET/HEAD/OPTIONS) запросы."""
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
