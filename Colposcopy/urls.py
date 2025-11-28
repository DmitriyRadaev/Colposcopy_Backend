# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from main import views
from main.views import (
    PathologyViewSet,
    CaseViewSet,
    QuestionViewSet,
    LayerViewSet,
    SchemeViewSet,
    PathologyImageViewSet,
    SubmitTestView  # Новый view для тестирования
)

# ----------------------------
# РОУТЕРЫ (ViewSets)
# ----------------------------
router = DefaultRouter()
router.register(r'pathologies', PathologyViewSet, basename='pathology')
router.register(r'cases', CaseViewSet, basename='case')
# router.register(r'tasks', TaskViewSet) — УДАЛЕНО
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'layers', LayerViewSet, basename='layer')
router.register(r'schemes', SchemeViewSet, basename='scheme')
router.register(r'pathology-images', PathologyImageViewSet, basename='pathology-images')

# ----------------------------
# URL patterns
# ----------------------------
urlpatterns = [
    # --- AUTH ---
    path("api/auth/login/", views.loginView, name="login"),
    path("api/auth/logout/", views.logoutView, name="logout"),
    path("api/auth/refresh_token/", views.CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/user/", views.current_user_view, name="account"), # Поправил имя view на current_user_view

    # --- REGISTRATION ---
    path("api/auth/register/worker/", views.WorkerRegisterView.as_view(), name="worker_register"),
    path("api/auth/register/admin/", views.AdminRegisterView.as_view(), name="admin_register"),
    # path("api/auth/register/superadmin/", views.SuperAdminRegisterView.as_view()), # Если нужно

    # --- TEST LOGIC ---
    # Эндпоинт для отправки результатов теста (POST запрос)
    path("api/test/submit/", SubmitTestView.as_view(), name="submit_test"),

    # --- MAIN API (CRUD) ---
    path("api/", include(router.urls)),
]