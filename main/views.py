# views.py
from datetime import timedelta
from django.core.cache import cache
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, generics, permissions, response, decorators, status, views
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework_simplejwt import tokens, views as jwt_views, serializers as jwt_serializers, \
    exceptions as jwt_exceptions
from django.contrib.auth import authenticate
from django.conf import settings
from django.middleware import csrf
from rest_framework import exceptions as rest_exceptions
from django.contrib.auth import get_user_model

from .models import (
    WorkerProfile, Case, Layer, Question, Pathology, Scheme, PathologyImage, Answer, TestResult, UserTestAnswer,
    VideoTutorial
)
from .serializers import (
    AccountSerializer, WorkerRegistrationSerializer, AdminRegistrationSerializer, SuperAdminRegistrationSerializer,
    WorkerProfileSerializer, CaseSerializer, LayerSerializer, QuestionSerializer,
    PathologySerializer, SchemeSerializer, PathologyImageSerializer,
    TestSubmissionSerializer, TestResultSerializer, PathologyListSerializer, ClinicalCaseInfoSerializer,
    PathologyDetailInfoSerializer, CaseDetailInfoSerializer, TestTaskSerializer, CaseSubmissionSerializer,
    TestSubmissionWrapperSerializer, UserProfileSerializer, UserTryInfoSerializer, HistoryTaskSerializer,
    VideoTutorialSerializer, TutorialListSerializer, TutorialDetailSerializer, TutorialCreateSerializer,
    TutorialDeleteSerializer, TestListSerializer, PathologyInfoSerializer
)
from .permissions import IsSuperAdmin, IsAdminOrSuperAdmin,IsAdminOrAuthenticatedReadOnly



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
    res.set_cookie(
        key="user_role",
        value="admin" if user.is_staff else "worker",
        max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
        secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
        httponly=True,
        samesite='Lax'
    )

    res["X-CSRFToken"] = csrf.get_token(request)
    return res

@csrf_exempt
@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.AllowAny])
def logoutView(request):
    # 1. Блэклист refresh токена
    try:
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if refresh_token:
            token = tokens.RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        # Если токен уже невалиден или его нет, игнорируем
        pass

    # 2. Формируем ответ
    res = response.Response({"detail": "Logged out successfully"}, status=status.HTTP_200_OK)

    # 3. Удаляем Access Token
    res.delete_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        path=settings.SIMPLE_JWT.get('AUTH_COOKIE_PATH', '/'),
        samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
    )

    # 4. Удаляем Refresh Token
    res.delete_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
        path=settings.SIMPLE_JWT.get('AUTH_COOKIE_PATH', '/'),
        samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
    )

    # 5. Удаляем куку роли
    res.delete_cookie(
        key="user_role",
        path=settings.SIMPLE_JWT.get('AUTH_COOKIE_PATH', '/'),
        samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
    )

    res.delete_cookie(
        key="is_staff",
        path=settings.SIMPLE_JWT.get('AUTH_COOKIE_PATH', '/'),
        samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
    )

    # 6. Удаляем CSRF куки
    res.delete_cookie(
        key=settings.CSRF_COOKIE_NAME,
        path='/',
        samesite=settings.CSRF_COOKIE_SAMESITE
    )

    res.delete_cookie(
        key="X-CSRFToken",
        path='/',
        samesite=settings.CSRF_COOKIE_SAMESITE
    )

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
        if response_obj.data.get("access"):
            response_obj.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                value=response_obj.data['access'],
                expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
                httponly=True, # Жестко True
                samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
            )
            del response_obj.data["access"]

        if response_obj.data.get("refresh"):
            response_obj.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                value=response_obj.data['refresh'],
                expires=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
                secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
                httponly=True, # Жестко True
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
    permission_classes = [IsAdminOrAuthenticatedReadOnly]


class PathologyImageViewSet(viewsets.ModelViewSet):
    queryset = PathologyImage.objects.all()
    serializer_class = PathologyInfoSerializer
    permission_classes = [IsAdminOrAuthenticatedReadOnly]


class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = [IsAdminOrAuthenticatedReadOnly]

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminOrAuthenticatedReadOnly]


class LayerViewSet(viewsets.ModelViewSet):
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer
    permission_classes = [IsAdminOrAuthenticatedReadOnly]


class SchemeViewSet(viewsets.ModelViewSet):
    queryset = Scheme.objects.all()
    serializer_class = SchemeSerializer
    permission_classes = [IsAdminOrAuthenticatedReadOnly]


# -------------------------------------------------------------------------
# ЛОГИКА ТЕСТИРОВАНИЯ
# -------------------------------------------------------------------------

class SubmitTestView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # 1. Валидация
        serializer = TestSubmissionWrapperSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        submission_items = validated_data.get('items', [])
        duration_seconds = validated_data.get('duration', 0)

        if not submission_items:
            return response.Response({"detail": "Список ответов пуст"}, status=status.HTTP_400_BAD_REQUEST)

        # ---------------------------------------------------
        # 2. Сбор данных
        # ---------------------------------------------------
        # Список ID кейсов, которые реально были в тесте
        case_ids = [item['caseId'] for item in submission_items]

        # Группировка ответов
        user_answers_map = {}
        user_selected_ids_flat = []

        for case_item in submission_items:
            for question_item in case_item['answers']:
                q_id = question_item['questionId']
                selected_ids = set(question_item['selectedAnswers'])
                user_answers_map[q_id] = selected_ids
                user_selected_ids_flat.extend(question_item['selectedAnswers'])

        # ---------------------------------------------------
        # 3. Подсчет баллов
        # ---------------------------------------------------
        # Фильтруем вопросы ТОЛЬКО по case_ids.
        questions_qs = Question.objects.filter(case__id__in=case_ids).prefetch_related('answers')

        user_score = 0
        max_score = 0

        for question in questions_qs:
            max_score += 1  # +1 балл за вопрос

            correct_answer_ids = set(ans.id for ans in question.answers.all() if ans.is_correct)
            user_selected_set = user_answers_map.get(question.id, set())

            if user_selected_set == correct_answer_ids:
                user_score += 1

        if max_score == 0: max_score = 1
        percentage = round((user_score / max_score) * 100, 2)

        if percentage >= 90:
            grade = "Отлично"
        elif percentage >= 75:
            grade = "Хорошо"
        elif percentage >= 50:
            grade = "Удовлетворительно"
        else:
            grade = "Неудовлетворительно"

        # Определение патологии (для статистики)
        first_case = get_object_or_404(Case, pk=case_ids[0])
        pathology = first_case.pathology

        # ---------------------------------------------------
        # 4. Сохранение
        # ---------------------------------------------------
        test_result = TestResult.objects.create(
            user=request.user,
            pathology=pathology,
            score=user_score,
            max_score=max_score,
            percentage=percentage,
            grade=grade,
            time_spent=timedelta(seconds=duration_seconds)
        )


        test_result.cases.set(case_ids)

        if user_selected_ids_flat:
            selected_answers_objs = Answer.objects.filter(id__in=user_selected_ids_flat)
            user_test_answers = []
            for ans_obj in selected_answers_objs:
                user_test_answers.append(
                    UserTestAnswer(
                        test_result=test_result,
                        question=ans_obj.question,
                        answer=ans_obj
                    )
                )
            UserTestAnswer.objects.bulk_create(user_test_answers)

        user_id = request.user.id

        active_key_pointer = f"user_{user_id}_current_test_key"
        actual_cache_key = cache.get(active_key_pointer)

        if actual_cache_key:
            cache.delete(actual_cache_key)
            cache.delete(active_key_pointer)

        return_serializer = TestResultSerializer(test_result)
        return response.Response(return_serializer.data, status=status.HTTP_201_CREATED)

class PathologyListInfoView(generics.ListAPIView):
    queryset = Pathology.objects.all()
    serializer_class = PathologyListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        queryset = queryset.annotate(
            images_count=Count('images')
        ).filter(
            images_count__gt=0
        ).order_by('number')

        serializer = self.get_serializer(queryset, many=True)

        return response.Response({
            "items": serializer.data
        })

class AdminPathologyListInfoView(generics.ListAPIView):
    queryset = Pathology.objects.all()
    serializer_class = PathologyListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.order_by('number')

        serializer = self.get_serializer(queryset, many=True)

        return response.Response({
            "items": serializer.data
        })

class TestListInfoView(generics.ListAPIView):
    """
    Список патологий с тестами, у которых есть клинические случаи
    """
    serializer_class = TestListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Возвращаем только патологии с кейсами
        return Pathology.objects.annotate(
            cases_count=Count('cases')
        ).filter(
            cases_count__gt=0
        ).order_by('number')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return response.Response({
            "items": serializer.data
        })


class ClinicalCaseListView(generics.ListAPIView):
    serializer_class = ClinicalCaseInfoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Pathology.objects.annotate(
            c_count=Count('cases')
        ).filter(
            c_count__gt=0
        ).prefetch_related("cases")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return response.Response({
            "items": serializer.data
        })


class PathologyDetailView(generics.RetrieveAPIView):
    queryset = Pathology.objects.prefetch_related("images").all()
    serializer_class = PathologyDetailInfoSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'


class CaseDetailInfoView(generics.RetrieveAPIView):
    queryset = Case.objects.prefetch_related('layers', 'schemes').all()
    serializer_class = CaseDetailInfoSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

TEST_CACHE_TIMEOUT = 60 * 10
class GetTestTasksView(generics.ListAPIView):
    serializer_class = TestTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        pathology_ids_str = self.kwargs.get('pathology_ids', '')
        user_id = self.request.user.id

        cache_key = f"user_{user_id}_test_tasks_{pathology_ids_str}"


        saved_case_ids = cache.get(cache_key)

        if saved_case_ids:

            return Case.objects.filter(id__in=saved_case_ids).prefetch_related(
                'layers', 'schemes', 'questions', 'questions__answers'
            )

        try:
            pathology_ids = [int(x) for x in pathology_ids_str.split('-') if x.isdigit()]
        except ValueError:
            pathology_ids = []

        if not pathology_ids:
            return Case.objects.none()

        final_case_ids = []
        for p_id in pathology_ids:
            # 4 случайных кейса
            random_cases = Case.objects.filter(pathology_id=p_id).values_list('id', flat=True).order_by('?')[:4]
            final_case_ids.extend([int(c_id) for c_id in random_cases])


        cache.set(cache_key, final_case_ids, timeout=TEST_CACHE_TIMEOUT)
        active_key_pointer = f"user_{user_id}_current_test_key"
        cache.set(active_key_pointer, cache_key, timeout=TEST_CACHE_TIMEOUT)

        return Case.objects.filter(id__in=final_case_ids).prefetch_related(
            'layers', 'schemes', 'questions', 'questions__answers'
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return response.Response({
            "items": serializer.data
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Возвращаем текущего юзера, который делает запрос
        return self.request.user


class UserTestHistoryView(generics.ListAPIView):
    serializer_class = UserTryInfoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TestResult.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return response.Response({
            "items": serializer.data
        })


class TestResultHistoryView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        id = kwargs.get('id')
        test_result = get_object_or_404(TestResult, id=id, user=request.user)

        selected_answer_ids = set(
            test_result.user_answers.values_list('answer_id', flat=True)
        )

        cases = test_result.cases.all().prefetch_related(
            'layers',
            'schemes',
            'questions',
            'questions__answers'
        )

        serializer = HistoryTaskSerializer(
            cases,
            many=True,
            context={
                'selected_answer_ids': selected_answer_ids,
                'request': request
            }
        )

        return response.Response({
            "items": serializer.data
        })


# 1. Список туториалов
class TutorialListView(generics.ListAPIView):
    queryset = VideoTutorial.objects.all()
    serializer_class = TutorialListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        # Оборачиваем список в ключ "items"
        return response.Response({
            "items": serializer.data
        })


# 2. Детальная информация о туториале
class TutorialDetailView(generics.RetrieveAPIView):
    queryset = VideoTutorial.objects.all()
    serializer_class = TutorialDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'


class TutorialCreateView(generics.CreateAPIView):
    queryset = VideoTutorial.objects.all()
    serializer_class = TutorialCreateSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAdminOrSuperAdmin]


class TutorialDeleteView(generics.DestroyAPIView):
    queryset = VideoTutorial.objects.all()
    serializer_class = TutorialDeleteSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    lookup_field = 'id'

