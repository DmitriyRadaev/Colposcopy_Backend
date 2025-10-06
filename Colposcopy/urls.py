# urls.py
from multiprocessing.managers import Token

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from main.views import (
    UniversityAdminViewSet, StudentViewSet, AttemptViewSet,
    TaskViewSet, CaseViewSet, ParameterViewSet,
    RecommendationViewSet, Layer1ViewSet,
    Layer2ViewSet, Layer3ViewSet, Layer4ViewSet
)

# Создаем роутер и регистрируем ViewSets
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
router.register(r'university-admins', UniversityAdminViewSet, basename='universityadmin')

urlpatterns = [
    # Включаем все URL-адреса, сгенерированные роутером
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]