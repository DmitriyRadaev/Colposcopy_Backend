from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from main import views

from main.views import (
    PathologyViewSet, CaseViewSet, TaskViewSet, QuestionViewSet,
    LayerViewSet, SchemeViewSet, PathologyImageViewSet,
    AttemptViewSet
)

# ----------------------------
# РОУТЕРЫ (ViewSets)
# ----------------------------
router = DefaultRouter()
router.register(r'pathologies', PathologyViewSet, basename='pathology')
router.register(r'cases', CaseViewSet, basename='case')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'layers', LayerViewSet, basename='layer')
router.register(r'schemes', SchemeViewSet, basename='scheme')
router.register(r'pathology-images', PathologyImageViewSet, basename='pathology-image')

router.register(r'attempts', AttemptViewSet, basename='attempt')



urlpatterns = [

    path("api/auth/login/", views.loginView, name="login"),
    path("api/auth/logout/", views.logoutView, name="logout"),
    path("api/auth/refresh_token/", views.CookieTokenRefreshView.as_view(), name="token_refresh"),

    # ТЕКУЩИЙ АВТОРИЗОВАННЫЙ ПОЛЬЗОВАТЕЛЬ
    path("api/auth/user/", views.current_user_view, name="current_user"),

    # РЕГИСТРАЦИИ
    path("api/auth/register/worker/", views.WorkerRegisterView.as_view(), name="worker_register"),
    path("api/auth/register/admin/", views.AdminRegisterView.as_view(), name="admin_register"),
    path("api/auth/register/super-admin/", views.SuperAdminRegisterView.as_view(), name="super_admin_register"),


    path("api/", include(router.urls)),


    path("admin/", admin.site.urls),
]
