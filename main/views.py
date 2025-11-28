# views.py
from rest_framework import viewsets, generics, permissions, response, decorators, status
from rest_framework.views import APIView
from rest_framework_simplejwt import tokens, views as jwt_views, serializers as jwt_serializers, \
    exceptions as jwt_exceptions
from django.contrib.auth import authenticate
from django.conf import settings
from django.middleware import csrf
from rest_framework import exceptions as rest_exceptions
from django.contrib.auth import get_user_model

from .models import (
    WorkerProfile, Case, Layer, Question, Pathology, Scheme, PathologyImage, Answer, TestResult
)
from .serializers import (
    AccountSerializer, WorkerRegistrationSerializer, AdminRegistrationSerializer, SuperAdminRegistrationSerializer,
    WorkerProfileSerializer, CaseSerializer, LayerSerializer, QuestionSerializer,
    PathologySerializer, SchemeSerializer, PathologyImageSerializer,
    TestSubmissionSerializer, TestResultSerializer, PathologyListSerializer, ClinicalCaseInfoSerializer,
    PathologyDetailInfoSerializer
)
from .permissions import IsSuperAdmin, IsAdminOrSuperAdmin

# -------------------------------------------------------------------------
# АУТЕНТИФИКАЦИЯ (JWT в Cookies)
# -------------------------------------------------------------------------

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


@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def current_user_view(request):
    serializer = AccountSerializer(request.user)
    return response.Response(serializer.data)


# -------------------------------------------------------------------------
# РЕГИСТРАЦИЯ И ПРОФИЛИ
# -------------------------------------------------------------------------

class WorkerRegisterView(generics.CreateAPIView):
    serializer_class = WorkerRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class AdminRegisterView(generics.CreateAPIView):
    serializer_class = AdminRegistrationSerializer
    permission_classes = [IsSuperAdmin]


class SuperAdminRegisterView(generics.CreateAPIView):
    serializer_class = SuperAdminRegistrationSerializer
    permission_classes = [IsSuperAdmin]


class WorkerProfileViewSet(viewsets.ModelViewSet):
    queryset = WorkerProfile.objects.select_related("user").all()
    serializer_class = WorkerProfileSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return super().get_queryset()
        return WorkerProfile.objects.filter(user=user)


# -------------------------------------------------------------------------
# ОСНОВНАЯ ЛОГИКА (CRUD)
# -------------------------------------------------------------------------

class PathologyViewSet(viewsets.ModelViewSet):
    queryset = Pathology.objects.all()
    serializer_class = PathologySerializer


class PathologyImageViewSet(viewsets.ModelViewSet):
    queryset = PathologyImage.objects.all()
    serializer_class = PathologyImageSerializer


class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer


# TaskViewSet удален, так как модель Task удалена.
# Вопросы теперь привязаны напрямую к Case.

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class LayerViewSet(viewsets.ModelViewSet):
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer


class SchemeViewSet(viewsets.ModelViewSet):
    queryset = Scheme.objects.all()
    serializer_class = SchemeSerializer


# -------------------------------------------------------------------------
# ЛОГИКА ТЕСТИРОВАНИЯ
# -------------------------------------------------------------------------

class SubmitTestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # 1. Валидация входных данных (ids патологии, кейсов и ответов)
        serializer = TestSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pathology_id = serializer.validated_data['pathology_id']
        case_ids = serializer.validated_data['case_ids']
        user_answer_ids = serializer.validated_data['answer_ids']  # Список ID ответов пользователя

        # 2. Получаем выбранные кейсы, чтобы убедиться, что они существуют
        selected_cases = Case.objects.filter(id__in=case_ids, pathology_id=pathology_id)
        if not selected_cases.exists():
            return response.Response(
                {"detail": "Не найдены кейсы для указанной патологии."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Считаем MAX балл (Знаменатель)
        # Находим ВСЕ правильные ответы (is_correct=True), которые существуют
        # внутри вопросов, привязанных к выбранным кейсам.
        correct_answers_db = Answer.objects.filter(
            question__case__in=selected_cases,
            is_correct=True
        )
        max_score = correct_answers_db.count()

        # 4. Считаем балл пользователя (Числитель)
        # Пользователь получает балл, если ID его ответа совпадает с правильным ответом из БД.
        # Используем set для уникальности ID, чтобы исключить дубли.
        user_answer_ids_set = set(user_answer_ids)

        # Фильтруем список правильных ответов базы данных: оставляем только те,
        # ID которых есть в ответах пользователя.
        user_score = correct_answers_db.filter(id__in=user_answer_ids_set).count()

        # 5. Вычисляем процент
        if max_score > 0:
            percentage = (user_score / max_score) * 100
        else:
            percentage = 0  # Если вопросов/правильных ответов в кейсах не было вообще

        # Округляем до 1 знака (можно до целого, как удобнее)
        percentage = round(percentage, 1)

        # 6. Определяем оценку согласно ТЗ
        # 0-64% Неудовлетворительно
        # 65-74% Удовлетворительно
        # 75-84% Хорошо
        # 85-100% Отлично
        if percentage >= 85:
            grade = "Отлично"
        elif percentage >= 75:
            grade = "Хорошо"
        elif percentage >= 65:
            grade = "Удовлетворительно"
        else:
            grade = "Неудовлетворительно"

        # 7. Сохраняем результат в историю
        result = TestResult.objects.create(
            user=request.user,
            pathology_id=pathology_id,
            score=user_score,
            max_score=max_score,
            percentage=percentage,
            grade=grade
        )

        # 8. Возвращаем результат клиенту
        return response.Response(TestResultSerializer(result).data, status=status.HTTP_201_CREATED)


class PathologyListInfoView(generics.ListAPIView):
    queryset = Pathology.objects.all()
    serializer_class = PathologyListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        return response.Response({
            "items": serializer.data
        })


class ClinicalCaseListView(generics.ListAPIView):
    # Оптимизация запроса к БД
    queryset = Pathology.objects.prefetch_related("cases").all()
    serializer_class = ClinicalCaseInfoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        # Оборачиваем в items согласно GetClinicalCasesInfoDto
        return response.Response({
            "items": serializer.data
        })

class PathologyDetailView(generics.RetrieveAPIView):
    queryset = Pathology.objects.prefetch_related("images").all()
    serializer_class = PathologyDetailInfoSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'