# main/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from main import views

# ----------------------------
# РОУТЕРЫ (ViewSets)
# ----------------------------
router = DefaultRouter()
router.register(r'cases', views.CaseViewSet, basename='case')
router.register(r'layers', views.LayerViewSet, basename='layer')
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'attempts', views.AttemptViewSet, basename='attempt')
router.register(r'parameters', views.ParameterViewSet, basename='parameter')
router.register(r'recommendations', views.RecommendationViewSet, basename='recommendation')

# ----------------------------
# URL patterns
# ----------------------------
urlpatterns = [
    # --- AUTH ---
    path("api/auth/login/", views.loginView, name="login"),
    path("api/auth/logout/", views.logoutView, name="logout"),
    path("api/auth/refresh/", views.CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/user/", views.Account, name="account"),

    # --- REGISTRATION ---
    path("api/auth/register/worker/", views.WorkerRegisterView.as_view(), name="worker_register"),
    path("api/auth/register/admin/", views.AdminRegisterView.as_view(), name="admin_register"),

    # --- MAIN API ---
    path("api/", include(router.urls)),
]
