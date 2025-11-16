# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    WorkerProfile, Case, Layer, Task, Question, Pathology, Scheme, Answer
)




# Аутентификация
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




# Логика сайта

class PathologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pathology
        fields = ['id', 'name', 'description', 'cases']

class LayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        fields = ['id', 'number', 'layer_img', 'layer_description']

class SchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        fields = ['id', 'scheme_img', 'scheme_description_img']

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'is_correct']

class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'name', 'instruction', 'qtype', 'answers']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        question = Question.objects.create(**validated_data)
        for ans in answers_data:
            Answer.objects.create(question=question, **ans)
        return question

class TaskSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Task
        fields = ['id', 'case', 'questions']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        task = Task.objects.create(**validated_data)
        for q in questions_data:
            answers_data = q.pop('answers')
            question = Question.objects.create(task=task, **q)
            for ans in answers_data:
                Answer.objects.create(question=question, **ans)
        return task

class CaseSerializer(serializers.ModelSerializer):
    layers = LayerSerializer(many=True, read_only=True)
    schemes = SchemeSerializer(many=True, read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Case
        fields = ['id', 'name', 'pathology', 'created_at', 'layers', 'schemes', 'tasks']

