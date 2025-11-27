from django.utils import timezone
from rest_framework import viewsets, generics, permissions, response, decorators, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt import tokens, views as jwt_views, serializers as jwt_serializers, exceptions as jwt_exceptions
from django.contrib.auth import authenticate
from django.conf import settings
from django.middleware import csrf
from rest_framework import exceptions as rest_exceptions
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import (
    WorkerProfile, Case, Layer, Task, Question, Pathology, Scheme,
    PathologyImage, Attempt, AttemptAnswer
)

from .serializers import (
    AccountSerializer, WorkerRegistrationSerializer, AdminRegistrationSerializer, SuperAdminRegistrationSerializer,
    WorkerProfileSerializer, CaseSerializer, LayerSerializer, TaskSerializer, QuestionSerializer,
    PathologySerializer, SchemeSerializer, PathologyImageSerializer, AttemptSerializer
)

from .permissions import IsSuperAdmin, IsAdminOrSuperAdmin


# -----------------------------
# AUTH
# -----------------------------
Account = get_user_model()


def get_user_tokens(user):
    refresh = tokens.RefreshToken.for_user(user)
    return {"refresh_token": str(refresh), "access_token": str(refresh.access_token)}


@decorators.api_view(["POST"])
@decorators.permission_classes([])
def loginView(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        raise rest_exceptions.ValidationError({"detail": "Email and password required"})

    user = authenticate(email=email, password=password)
    if not user:
        raise rest_exceptions.AuthenticationFailed("Email or password is incorrect!")

    tokens_dict = get_user_tokens(user)
    res = Response(tokens_dict)

    res.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        value=tokens_dict["access_token"],
        expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
        secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
        httponly=settings.SIMPLE_JWT.get('AUTH_COOKIE_HTTP_ONLY', True),
        samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
    )
    res.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
        value=tokens_dict["refresh_token"],
        expires=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
        secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
        httponly=settings.SIMPLE_JWT.get('AUTH_COOKIE_HTTP_ONLY', True),
        samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
    )
    res["X-CSRFToken"] = csrf.get_token(request)
    return res


@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.IsAuthenticated])
def logoutView(request):
    try:
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if refresh_token:
            token = tokens.RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass

    res = Response({"detail": "Logged out"})
    res.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
    res.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
    res.delete_cookie("X-CSRFToken")
    return res


class CookieTokenRefreshSerializer(jwt_serializers.TokenRefreshSerializer):
    refresh = None

    def validate(self, attrs):
        attrs['refresh'] = self.context['request'].COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if attrs['refresh']:
            return super().validate(attrs)
        raise jwt_exceptions.InvalidToken("No valid refresh token in cookie")


class CookieTokenRefreshView(jwt_views.TokenRefreshView):
    serializer_class = CookieTokenRefreshSerializer

    def finalize_response(self, request, response_obj, *args, **kwargs):
        if response_obj.data.get("refresh"):
            response_obj.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                value=response_obj.data['refresh'],
                expires=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
                secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
                httponly=settings.SIMPLE_JWT.get('AUTH_COOKIE_HTTP_ONLY', True),
                samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
            )
            del response_obj.data["refresh"]

        response_obj["X-CSRFToken"] = request.COOKIES.get("csrftoken")
        return super().finalize_response(request, response_obj, *args, **kwargs)


# -----------------------------
# REGISTRATION
# -----------------------------
class WorkerRegisterView(generics.CreateAPIView):
    serializer_class = WorkerRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class AdminRegisterView(generics.CreateAPIView):
    serializer_class = AdminRegistrationSerializer
    permission_classes = [IsSuperAdmin]


class SuperAdminRegisterView(generics.CreateAPIView):
    serializer_class = SuperAdminRegistrationSerializer
    permission_classes = [IsSuperAdmin]


@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def current_user_view(request):
    serializer = AccountSerializer(request.user)
    return Response(serializer.data)


# -----------------------------
# CRUD Viewsets
# -----------------------------
class WorkerProfileViewSet(viewsets.ModelViewSet):
    queryset = WorkerProfile.objects.select_related("user").all()
    serializer_class = WorkerProfileSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return super().get_queryset()
        return WorkerProfile.objects.filter(user=user)


class PathologyViewSet(viewsets.ModelViewSet):
    queryset = Pathology.objects.all()
    serializer_class = PathologySerializer


class PathologyImageViewSet(viewsets.ModelViewSet):
    queryset = PathologyImage.objects.all()
    serializer_class = PathologyImageSerializer


class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class LayerViewSet(viewsets.ModelViewSet):
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer


class SchemeViewSet(viewsets.ModelViewSet):
    queryset = Scheme.objects.all()
    serializer_class = SchemeSerializer


# -----------------------------
# ATTEMPTS
# -----------------------------
class AttemptViewSet(viewsets.ModelViewSet):
    queryset = Attempt.objects.all()
    serializer_class = AttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Создаём попытку для текущего пользователя
        serializer.save(worker=self.request.user)

    @action(detail=True, methods=["post"])
    def submit_answers(self, request, pk=None):
        """
        Фронт отправляет JSON вида:
        {
            "answers": [
                {"question": 19, "selected_answers": [62]},
                {"question": 20, "selected_answers": [65]}
            ]
        }
        """
        attempt = self.get_object()
        answers_data = request.data.get("answers", [])

        for answer_data in answers_data:
            question_id = answer_data.get("question")
            selected_ids = answer_data.get("selected_answers", [])
            question = get_object_or_404(Question, pk=question_id)

            # Создаём или обновляем запись AttemptAnswer
            attempt_answer, _ = AttemptAnswer.objects.update_or_create(
                attempt=attempt,
                question=question
            )

            # Устанавливаем выбранные ответы
            attempt_answer.selected_answers.set(selected_ids)

            # Проверяем правильность
            correct_ids = set(question.answers.filter(is_correct=True).values_list("id", flat=True))
            attempt_answer.is_correct = set(selected_ids) == correct_ids
            attempt_answer.save()

        # Сохраняем время окончания попытки
        attempt.end_time = timezone.now()
        attempt.save()

        # Возвращаем полные данные попытки с результатами
        serializer = AttemptSerializer(attempt)
        return Response(serializer.data)


class AttemptCreateView(generics.CreateAPIView):
    serializer_class = AttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

