# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    WorkerProfile, Case, Layer, Task, Question, Choice,
    Parameter, Recommendation, Attempt, AttemptAnswer
)

Account = get_user_model()


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ("id", "email", "username", "is_active", "is_staff", "is_superuser", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class WorkerRegistrationSerializer(serializers.ModelSerializer):
    place_of_work = serializers.CharField(write_only=True, required=True)
    position = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Account
        fields = ("email", "username", "password", "password2", "place_of_work", "position")

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        place = validated_data.pop("place_of_work")
        pos = validated_data.pop("position")
        password = validated_data.pop("password")
        user = Account.objects.create_worker(
            email=validated_data["email"],
            username=validated_data["username"],
            password=password,
            place_of_work=place,
            position=pos
        )
        return user


class AdminRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Account
        fields = ("email", "username", "password", "password2")

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = Account.objects.create_admin(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"]
        )
        return user


class SuperAdminRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Account
        fields = ("email", "username", "password", "password2")

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = Account.objects.create_superuser(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"]
        )
        return user


class WorkerProfileSerializer(serializers.ModelSerializer):
    user = AccountSerializer(read_only=True)
    class Meta:
        model = WorkerProfile
        fields = ("id", "user", "place_of_work", "position")


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = ("id", "name")


class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = ("id", "name")


class LayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        fields = ("id", "case", "number", "layer_img", "layer_description")
        read_only_fields = ("id",)


class CaseSerializer(serializers.ModelSerializer):
    layers = LayerSerializer(many=True, read_only=True)
    parameters = serializers.PrimaryKeyRelatedField(many=True, queryset=Parameter.objects.all(), required=False)
    recommendations = serializers.PrimaryKeyRelatedField(many=True, queryset=Recommendation.objects.all(), required=False)

    class Meta:
        model = Case
        fields = ("id", "name", "description", "diagnosis", "parameters", "recommendations", "layers", "created_at")
        read_only_fields = ("id", "created_at", "layers")


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("id", "title", "description", "case", "order")


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ("id", "text")


class ChoiceAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ("id", "text", "is_correct")


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    class Meta:
        model = Question
        fields = ("id", "task", "case", "title", "instruction", "multiple", "order", "choices")


class AttemptAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttemptAnswer
        fields = ("id", "attempt", "question", "selected_choice", "free_text", "time_spent", "is_correct")
        read_only_fields = ("is_correct",)

    def create(self, validated_data):
        ans = super().create(validated_data)
        try:
            ans.evaluate()
        except Exception:
            pass
        return ans


class AttemptSerializer(serializers.ModelSerializer):
    answers = AttemptAnswerSerializer(many=True, read_only=True)
    class Meta:
        model = Attempt
        fields = ("id", "worker", "task", "case", "start_time", "end_time", "duration", "correct_count", "incorrect_count", "score", "status", "answers")
        read_only_fields = ("worker","start_time","end_time","duration","correct_count","incorrect_count","score","status","answers")
