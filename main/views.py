# views.py
from datetime import timedelta

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
    VideoTutorialSerializer, TutorialListSerializer, TutorialDetailSerializer, TutorialCreateSerializer
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

    # 5. Удаляем куку роли (если вы ее ставили при логине)
    # Мы используем строковое имя "user_role", так как в settings.SIMPLE_JWT его обычно нет по умолчанию.
    # Но используем те же path и samesite, чтобы удаление точно сработало.
    res.delete_cookie(
        key="user_role",
        path=settings.SIMPLE_JWT.get('AUTH_COOKIE_PATH', '/'),
        samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
    )

    # Если использовали is_staff
    res.delete_cookie(
        key="is_staff",
        path=settings.SIMPLE_JWT.get('AUTH_COOKIE_PATH', '/'),
        samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
    )

    # 6. Удаляем CSRF куки (стандартные Django настройки)
    res.delete_cookie(
        key=settings.CSRF_COOKIE_NAME,
        path='/',
        samesite=settings.CSRF_COOKIE_SAMESITE
    )

    # Иногда фронтенд или Nginx могут ставить дублирующую куку, лучше почистить и её
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
    serializer_class = PathologyImageSerializer
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
        case_ids = [item['caseId'] for item in submission_items]

        # Карта: { ID_вопроса: {ID_ответа_1, ID_ответа_2} }
        user_answers_map = {}
        # Плоский список для сохранения истории
        user_selected_ids_flat = []

        for case_item in submission_items:
            for question_item in case_item['answers']:
                q_id = question_item['questionId']
                selected_ids = set(question_item['selectedAnswers'])

                user_answers_map[q_id] = selected_ids
                user_selected_ids_flat.extend(question_item['selectedAnswers'])

        # ---------------------------------------------------
        # 3. Определение Патологии
        # ---------------------------------------------------
        first_case = get_object_or_404(Case, pk=case_ids[0])
        pathology = first_case.pathology

        # ---------------------------------------------------
        # 4. ПОДСЧЕТ БАЛЛОВ (1 вопрос = 1 балл)
        # ---------------------------------------------------

        # Получаем список вопросов для этих кейсов
        questions_qs = Question.objects.filter(case__id__in=case_ids).prefetch_related('answers')

        user_score = 0
        max_score = 0

        for question in questions_qs:
            # === ГЛАВНОЕ ИЗМЕНЕНИЕ ===
            # Мы увеличиваем макс. балл на 1 за каждый ВОПРОС, а не за каждый правильный ответ.
            max_score += 1

            # 1. Какие ответы правильные (множество ID)
            correct_answer_ids = set(
                ans.id for ans in question.answers.all() if ans.is_correct
            )

            # 2. Какие ответы выбрал юзер (множество ID)
            user_selected_set = user_answers_map.get(question.id, set())

            # 3. Сравниваем множества целиком
            # Если множества полностью совпадают -> +1 балл
            # Если есть лишняя галочка или не хватает нужной -> 0 баллов
            if user_selected_set == correct_answer_ids:
                user_score += 1

        if max_score == 0:
            max_score = 1

        # Процент и Оценка
        percentage = round((user_score / max_score) * 100, 2)

        if percentage >= 90:
            grade = "Отлично"
        elif percentage >= 75:
            grade = "Хорошо"
        elif percentage >= 50:
            grade = "Удовлетворительно"
        else:
            grade = "Неудовлетворительно"

        # ---------------------------------------------------
        # 5. Сохранение результата
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

        # ---------------------------------------------------
        # 6. Сохранение истории ответов
        # ---------------------------------------------------
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

        return_serializer = TestResultSerializer(test_result)
        return response.Response(return_serializer.data, status=status.HTTP_201_CREATED)

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
    queryset = Pathology.objects.prefetch_related("cases").all()
    serializer_class = ClinicalCaseInfoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
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


class GetTestTasksView(generics.ListAPIView):
    serializer_class = TestTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ids_string = self.kwargs.get('pathology_ids', '')
        pathology_ids = [int(x) for x in ids_string.split('-') if x.isdigit()]

        if not pathology_ids:
            return Case.objects.none()
        queryset = Case.objects.filter(pathology__id__in=pathology_ids).prefetch_related(
            'layers',
            'schemes',
            'questions',
            'questions__answers'
        ).distinct()

        return queryset

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
        # 1. Фильтруем по текущему пользователю
        # 2. Сортируем по дате создания (сначала новые) - order_by('-created_at')
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
        pathology = test_result.pathology
        if not pathology:
            return response.Response({"items": []})

        cases = Case.objects.filter(pathology=pathology).prefetch_related(
            'layers',
            'schemes',
            'questions',
            'questions__answers'
        ).distinct()

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
    permission_classes = [IsAdminOrAuthenticatedReadOnly]