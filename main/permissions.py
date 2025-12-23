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


from rest_framework import permissions

class IsAdminOrAuthenticatedReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # 1. Сначала проверяем, авторизован ли пользователь в принципе
        if not (request.user and request.user.is_authenticated):
            return False

        # 2. Если метод безопасный (GET), разрешаем (т.к. мы уже проверили авторизацию выше)
        if request.method in permissions.SAFE_METHODS:
            return True

        # 3. Для всех остальных методов (POST, PUT, DELETE) требуем права админа.
        # В твоей модели Account админы и суперадмины имеют флаг is_staff=True
        return request.user.is_staff