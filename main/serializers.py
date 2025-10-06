from rest_framework import serializers

from main.models import Student, UniversityAdmin, Attempt, Task, Case, Parameter, Recommendation, Layer1, Layer2, \
    Layer3, Layer4, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'username']


class UniversityAdminSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UniversityAdmin
        fields = ['id','name', 'user', 'university', 'is_active']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            name=user_data['name'],
            password=user_data.get('password', '123456')  # временно
        )
        admin = UniversityAdmin.objects.create(user=user, **validated_data)
        return admin


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

