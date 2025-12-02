# urls.py
from os.path import basename

from django.conf.urls.static import static
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
    UserProfileView  # Новый view для тестирования
)

# ----------------------------
# РОУТЕРЫ (ViewSets)
# ----------------------------
router = DefaultRouter()
router.register(r'pathologies', PathologyViewSet, basename='pathology')
router.register(r'cases', CaseViewSet, basename='case')
#router.register(r'questions', QuestionViewSet, basename='question')
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

    # --- REGISTRATION ---
    path("api/auth/register/worker/", views.WorkerRegisterView.as_view(), name="worker_register"),
    path("api/auth/register/admin/", views.AdminRegisterView.as_view(), name="admin_register"),
    # path("api/auth/register/superadmin/", views.SuperAdminRegisterView.as_view()), # Если нужно

    # --- TEST LOGIC ---
    # Эндпоинт для отправки результатов теста (POST запрос)
    path("api/test/submit/", SubmitTestView.as_view(), name="submit_test"),



    # --- MAIN API (CRUD) ---
    path("api/", include(router.urls)),
    path('api/atlas/atlas-list/', PathologyListInfoView.as_view(), name='atlas-list-info'),
    path('api/clincal-cases/cases/', ClinicalCaseListView.as_view(), name='clinical-cases-list'),
    path('api/atlas/pathology/<int:id>/', PathologyDetailView.as_view(), name='pathology-detail'),
    path('api/test/test-tasks/<str:pathology_ids>/', GetTestTasksView.as_view(), name='get-test-tasks'),
    path('api/test/submit-answers/', SubmitTestView.as_view(), name='test-submit'),
   # path('api/cases/case/<int:id>/', CaseDetailInfoView.as_view(), name='case-detail-info'),
    path('api/questions/bulk-create/', QuestionBulkCreateView.as_view(), name='questions-bulk-create'),
    path('api/account/profile/', UserProfileView.as_view(), name='current-user-profile'),



    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)