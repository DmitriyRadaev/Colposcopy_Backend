# urls.py


from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from main import views
from main.views import (
    StudentViewSet, AttemptViewSet,
    TaskViewSet, CaseViewSet, ParameterViewSet,
    RecommendationViewSet, Layer1ViewSet,
    Layer2ViewSet, Layer3ViewSet, Layer4ViewSet
)


router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'attempts', AttemptViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'cases', CaseViewSet)
router.register(r'parameters', ParameterViewSet)
router.register(r'recommendations', RecommendationViewSet)
router.register(r'layers1', Layer1ViewSet)
router.register(r'layers2', Layer2ViewSet)
router.register(r'layers3', Layer3ViewSet)
router.register(r'layers4', Layer4ViewSet)



urlpatterns = [
    # Включаем все URL-адреса, сгенерированные роутером
    path('api/', include(router.urls)),
    path('api/auth/login', views.loginView),
    path('api/auth/register', views.registerView),
    path('api/auth/refresh-token', views.CookieTokenRefreshView.as_view()),
    path('api/auth/logout', views.logoutView),
    path("api/auth/user", views.user),

    path('api/admin/', admin.site.urls),
]