# urls.py
from os.path import basename

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from rest_framework.routers import DefaultRouter

from django.conf import settings
from main import views
from main.serializers import QuestionBulkCreateView
from main.views import (
    PathologyViewSet,
    CaseViewSet,
    QuestionViewSet,
    LayerViewSet,
    SchemeViewSet,
    PathologyImageViewSet,
    SubmitTestView, PathologyListInfoView,
    ClinicalCaseListView, PathologyDetailView, CaseDetailInfoView, GetTestTasksView,
    UserProfileView, UserTestHistoryView, TestResultHistoryView,
    TutorialListView, TutorialDetailView, TutorialCreateView, TutorialDeleteView,
    TestListInfoView, AdminPathologyListInfoView, TutorialUpdateView
)

# ----------------------------
# РОУТЕРЫ (ViewSets)
# ----------------------------
router = DefaultRouter()
router.register(r'pathologies', PathologyViewSet, basename='pathology')
router.register(r'case_submit', CaseViewSet, basename='case')
router.register(r'questions_submit', QuestionViewSet, basename='question')
router.register(r'layers', LayerViewSet, basename='layer')
router.register(r'schemes', SchemeViewSet, basename='scheme')
router.register(r'pathology-images', PathologyImageViewSet, basename='pathology-images')
# ----------------------------
# URL
# ----------------------------
urlpatterns = [
    # Авторизация
    path("api/auth/login/", views.loginView, name="login"),
    path("api/auth/logout/", views.logoutView, name="logout"),
    path("api/auth/refresh_token/", views.CookieTokenRefreshView.as_view(), name="token_refresh"),

    # Регистрация
    path("api/auth/register/worker/", views.WorkerRegisterView.as_view(), name="worker_register"),
    path("api/auth/register/admin/", views.AdminRegisterView.as_view(), name="admin_register"),
    # path("api/auth/register/superadmin/", views.SuperAdminRegisterView.as_view()),


    path("api/test/submit/", SubmitTestView.as_view(), name="submit_test"),  # Отправка теста

    # Главные API
    path("api/", include(router.urls)),
    path('api/atlas/atlas-list/', PathologyListInfoView.as_view(), name='atlas-list-info'), # GET: Получить список всех патологий (только ID и Название) для меню атласа.
    path('api/atlas/admin-atlas-list/',AdminPathologyListInfoView.as_view(), name='admin-atlas-list'), # GET Получить список всех паталогий для админки
    path('api/test/test-list/',TestListInfoView.as_view(), name='test-list-info'), # GET: Получить список всех тестов у которых есть кейсы
    path('api/clincal-cases/cases/', ClinicalCaseListView.as_view(), name='clinical-cases-list'), # GET: Получить список патологий, внутри которых лежат списки ID их клинических случаев.
    path('api/atlas/pathology/<int:id>/', PathologyDetailView.as_view(), name='pathology-detail'),  # GET: Получить полную информацию о конкретной патологии (описание, фотографии) по её ID.
    path('api/cases/case/<int:id>/', CaseDetailInfoView.as_view(), name='case-detail-info'), # GET: Получить данные конкретного клинического случая по ID (слои изображений, схемы, описания слоев).
    path('api/test/test-tasks/<str:pathology_ids>/', GetTestTasksView.as_view(), name='get-test-tasks'),    # GET: Сгенерировать тест. Принимает строку ID патологий через дефис (например, "1-3-5").
    path('api/test/submit-answers/', SubmitTestView.as_view(), name='test-submit'),       # POST: Отправить ответы пользователя на проверку.
    path('api/questions/bulk-create/', QuestionBulkCreateView.as_view(), name='questions-bulk-create'), # Убрать?
    path('api/account/profile/', UserProfileView.as_view(), name='current-user-profile'), # GET: Получить данные текущего пользователя (ФИО, работа, email). # PATCH: Изменить данные профиля или сменить пароль.
    path('api/account/try-list/', UserTestHistoryView.as_view(), name='profile-history'), # GET: Получить список всех попыток прохождения тестов текущего пользователя (Дата, Оценка, Время).
    path('api/account/attempt/<int:id>/', TestResultHistoryView.as_view(), name='history-detail'),  # GET: Получить детальный разбор конкретной попытки по её ID.
    path('api/admin-zone/', admin.site.urls),    # Админ-панель Django.
    path('api/tutorial/tutorials-list/', TutorialListView.as_view(), name='tutorials-list'), # GET: Получить список туториалов
    path('api/tutorial/<int:id>/', TutorialDetailView.as_view(), name='tutorial-detail'), # GET: Получить детальную информацию о туториале по ID
    path('api/tutorial/create/', TutorialCreateView.as_view(), name='tutorial-create'), # POST: Создать туториал
    path('api/tutorial/delete/<int:id>/', TutorialDeleteView.as_view(), name='tutorial-delete'),  # DELETE: Удалить туториал
    path('api/tutorial/update/<int:id>/', TutorialUpdateView.as_view(), name='tutorial-update'),  # UPDATE: Редактирование туториала


    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)