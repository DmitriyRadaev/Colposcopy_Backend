from django.contrib.auth import get_user_model
from rest_framework import serializers

from main.models import Attempt, Task, Case, Parameter, Recommendation, Layer1, Layer2, \
    Layer3, Layer4, Account, WorkerProfile


class WorkerRegistrationSerializer(serializers.ModelSerializer):
    place_of_work = serializers.CharField(required=False, allow_blank=True)
    position = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = Account
        fields = ("email", "username", "password", "place_of_work", "position")

    def create(self, validated_data):
        place = validated_data.pop("place_of_work", "")
        pos = validated_data.pop("position", "")
        user = Account.objects.create_worker(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
        )
        # создать/обновить профиль
        WorkerProfile.objects.update_or_create(user=user, defaults={
            "place_of_work": place,
            "position": pos
        })
        return user

class AdminCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = Account
        fields = ("email", "username", "password", "role")
        read_only_fields = ("role",)  # можно фиксировать роль ADMIN в view

    def create(self, validated_data):
        # ожидаем что view установит роль ADMIN
        role = validated_data.get("role", Account.Role.ADMIN)
        user = Account.objects.create_admin(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
        )
        user.role = role
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


class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = WorkerProfile

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

