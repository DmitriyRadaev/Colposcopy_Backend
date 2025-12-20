from rest_framework_simplejwt import authentication as jwt_authentication
from django.conf import settings
from rest_framework import authentication, exceptions as rest_exceptions


def enforce_csrf(request):
    if request.path == '/api/auth/logout/' or request.path.endswith('/logout/'):
        return

    check = authentication.CSRFCheck(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise rest_exceptions.PermissionDenied('CSRF Failed: %s' % reason)


class CustomAuthentication(jwt_authentication.JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        raw_token = None

        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        if request.path != '/api/auth/logout/':
            enforce_csrf(request)

        return self.get_user(validated_token), validated_token