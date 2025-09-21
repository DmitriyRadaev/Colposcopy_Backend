from rest_framework import serializers

from main.models import Student, UniversityAdmin, Attempt, Task, Case, Parameter, Recommendation, Layer1, Layer2, \
    Layer3, Layer4


class UniversityAdminSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = UniversityAdmin

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Student

class AttemptSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Attempt

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Task

class CaseSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Case

class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Parameter

class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Recommendation

class Layer1Serializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Layer1

class Layer2Serializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Layer2

class Layer3Serializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Layer3


class Layer4Serializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Layer4

