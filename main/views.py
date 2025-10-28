# views.py
from rest_framework import viewsets, generics, permissions, response, decorators, status
from rest_framework_simplejwt import tokens, views as jwt_views, serializers as jwt_serializers, exceptions as jwt_exceptions
from django.contrib.auth import authenticate
from django.conf import settings
from django.middleware import csrf
from rest_framework import exceptions as rest_exceptions

from django.shortcuts import get_object_or_404

from django.contrib.auth import get_user_model
from .models import (
    WorkerProfile, Case, Layer, Task, Question, Choice,
    Parameter, Recommendation, Attempt
)
from .serializers import (
    AccountSerializer, WorkerRegistrationSerializer, AdminRegistrationSerializer, SuperAdminRegistrationSerializer,
    WorkerProfileSerializer, CaseSerializer, LayerSerializer, TaskSerializer, QuestionSerializer,
    ChoiceSerializer, ChoiceAdminSerializer, ParameterSerializer, RecommendationSerializer,
    AttemptSerializer, AttemptAnswerSerializer
)
from .permissions import IsSuperAdmin, IsAdminOrSuperAdmin

Account = get_user_model()


# JWT cookie helpers (from your previous code)
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
    res = response.Response(tokens_dict)

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

    res = response.Response({"detail": "Logged out"})
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


# Registration endpoints
class WorkerRegisterView(generics.CreateAPIView):
    serializer_class = WorkerRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class AdminRegisterView(generics.CreateAPIView):
    serializer_class = AdminRegistrationSerializer
    permission_classes = [IsSuperAdmin]


class SuperAdminRegisterView(generics.CreateAPIView):
    serializer_class = SuperAdminRegistrationSerializer
    permission_classes = [IsSuperAdmin]


# WorkerProfile viewset
class WorkerProfileViewSet(viewsets.ModelViewSet):
    queryset = WorkerProfile.objects.select_related("user").all()
    serializer_class = WorkerProfileSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return super().get_queryset()
        return WorkerProfile.objects.filter(user=user)


# Parameter / Recommendation
class ParameterViewSet(viewsets.ModelViewSet):
    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer
    permission_classes = [IsAdminOrSuperAdmin]


class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer
    permission_classes = [IsAdminOrSuperAdmin]


# Case / Layer / Task / Question / Choice
class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all().prefetch_related("layers")
    serializer_class = CaseSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [IsAdminOrSuperAdmin()]


class LayerViewSet(viewsets.ModelViewSet):
    queryset = Layer.objects.all().order_by("case_id", "number")
    serializer_class = LayerSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [IsAdminOrSuperAdmin()]


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAdminOrSuperAdmin]


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminOrSuperAdmin]


class ChoiceViewSet(viewsets.ModelViewSet):
    queryset = Choice.objects.all()

    def get_serializer_class(self):
        user = getattr(self.request, "user", None)
        if user and (user.is_staff or user.is_superuser):
            return ChoiceAdminSerializer
        return ChoiceSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [IsAdminOrSuperAdmin()]


# Attempt / AttemptAnswer
class AttemptViewSet(viewsets.ModelViewSet):
    queryset = Attempt.objects.all()
    serializer_class = AttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return Attempt.objects.all()
        return Attempt.objects.filter(worker=user)

    def perform_create(self, serializer):
        serializer.save(worker=self.request.user)

    @decorators.action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated], url_path="answers")
    def add_answer(self, request, pk=None):
        attempt = self.get_object()
        if attempt.worker != request.user and not (request.user.is_staff or request.user.is_superuser):
            return response.Response({"detail": "No permission"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data["attempt"] = attempt.id
        serializer = AttemptAnswerSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        ans = serializer.save()

        total = attempt.answers.count()
        correct = attempt.answers.filter(is_correct=True).count()
        attempt.correct_count = correct
        attempt.incorrect_count = max(0, total - correct)
        attempt.score = (correct / total * 100.0) if total > 0 else 0.0
        attempt.save(update_fields=["correct_count", "incorrect_count", "score"])
        return response.Response(AttemptAnswerSerializer(ans).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def finish(self, request, pk=None):
        attempt = self.get_object()
        if attempt.worker != request.user and not (request.user.is_staff or request.user.is_superuser):
            return response.Response({"detail": "No permission"}, status=status.HTTP_403_FORBIDDEN)
        attempt.finish()
        return response.Response({"status": "finished", "score": attempt.score})


# Current user
@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def current_user_view(request):
    serializer = AccountSerializer(request.user)
    return response.Response(serializer.data)
