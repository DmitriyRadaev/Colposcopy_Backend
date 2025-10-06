# views.py

from rest_framework import viewsets, permissions
from .models import (
    UniversityAdmin, Student, Attempt,
    Task, Case, Parameter, Recommendation,
    Layer1, Layer2, Layer3, Layer4
)
from .serializers import (
    UniversityAdminSerializer, StudentSerializer,
    AttemptSerializer, TaskSerializer,
    CaseSerializer, ParameterSerializer,
    RecommendationSerializer, Layer1Serializer,
    Layer2Serializer, Layer3Serializer,
    Layer4Serializer
)

# Views для администраторов и студентов
class UniversityAdminViewSet(viewsets.ModelViewSet):
    queryset = UniversityAdmin.objects.all()
    serializer_class = UniversityAdminSerializer
    permission_classes = [permissions.IsAdminUser]  # только главный админ может управлять

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = (permissions.IsAuthenticated,)

# Views для попыток, тестов и случаев
class AttemptViewSet(viewsets.ModelViewSet):
    queryset = Attempt.objects.all()
    serializer_class = AttemptSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer

# Views для связанных данных (Parameters, Recommendations, Layers)
class ParameterViewSet(viewsets.ModelViewSet):
    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer

class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer

class Layer1ViewSet(viewsets.ModelViewSet):
    queryset = Layer1.objects.all()
    serializer_class = Layer1Serializer

class Layer2ViewSet(viewsets.ModelViewSet):
    queryset = Layer2.objects.all()
    serializer_class = Layer2Serializer

class Layer3ViewSet(viewsets.ModelViewSet):
    queryset = Layer3.objects.all()
    serializer_class = Layer3Serializer

class Layer4ViewSet(viewsets.ModelViewSet):
    queryset = Layer4.objects.all()
    serializer_class = Layer4Serializer