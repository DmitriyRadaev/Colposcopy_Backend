from django.contrib.auth import get_user_model
from rest_framework import serializers

from main.models import Student, Attempt, Task, Case, Parameter, Recommendation, Layer1, Layer2, \
    Layer3, Layer4


class RegistrationSerializer(serializers.ModelSerializer):

    password2 = serializers.CharField(style={"input_type": "password"})

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "password", "password2")
        extra_kwargs = {
            "password": {"write_only": True},
            "password2": {"write_only": True}
        }

    def save(self):
        user = get_user_model()(
            email=self.validated_data["email"],
            username=self.validated_data["username"],
        )

        password = self.validated_data["password"]
        password2 = self.validated_data["password2"]

        if password != password2:
            raise serializers.ValidationError(
                {"password": "Passwords do not match!"})

        user.set_password(password)
        user.save()

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"}, write_only=True)


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("username", "email")


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

