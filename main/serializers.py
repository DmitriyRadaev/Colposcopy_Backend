# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    WorkerProfile, Case, Layer, Question, Pathology, Scheme, Answer, PathologyImage, TestResult
)

# -------------------------------------------------------------------------
# АУТЕНТИФИКАЦИЯ И ПОЛЬЗОВАТЕЛИ
# -------------------------------------------------------------------------
Account = get_user_model()


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        # Возвращаем раздельные поля
        fields = ("id", "email", "name", "surname", "patronymic", "is_active", "is_staff", "is_superuser", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class WorkerRegistrationSerializer(serializers.ModelSerializer):
    work = serializers.CharField(write_only=True, required=True)
    position = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Account
        # Явно перечисляем новые поля
        fields = ("email", "name", "surname", "patronymic", "password", "password2", "work", "position")

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        place = validated_data.pop("work")
        pos = validated_data.pop("position")
        password = validated_data.pop("password")

        # Передаем данные напрямую в create_worker
        user = Account.objects.create_worker(
            email=validated_data["email"],
            name=validated_data["name"],
            surname=validated_data["surname"],
            patronymic=validated_data.get("patronymic", ""),
            password=password,
            work=place,
            position=pos
        )
        return user


class AdminRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Account
        fields = ("email", "name", "surname", "patronymic", "password", "password2")

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        # Передаем данные в create_admin
        user = Account.objects.create_admin(
            email=validated_data["email"],
            name=validated_data["name"],
            surname=validated_data["surname"],
            # patronymic можно достать через .get, если его не прислали
            patronymic=validated_data.get("patronymic", ""),
            password=validated_data["password"]
        )
        return user


class SuperAdminRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Account
        fields = ("email", "name", "surname", "patronymic", "password", "password2")

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = Account.objects.create_superuser(
            email=validated_data["email"],
            name=validated_data["name"],
            surname=validated_data["surname"],
            patronymic=validated_data.get("patronymic", ""),
            password=validated_data["password"]
        )
        return user


class WorkerProfileSerializer(serializers.ModelSerializer):
    user = AccountSerializer(read_only=True)

    class Meta:
        model = WorkerProfile
        fields = ("id", "user", "work", "position")


# -------------------------------------------------------------------------
# ОСНОВНОЙ КОНТЕНТ (АТЛАС, КЕЙСЫ)
# -------------------------------------------------------------------------

class PathologyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathologyImage
        fields = ['id', 'image', 'pathology']


class LayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        # 1. Добавляем 'case' в поля
        fields = ['id', 'case', 'number', 'layer_img', 'layer_description']

        # 2. Делаем его необязательным для валидатора, чтобы не ломалось
        # создание большого JSON (где case создается автоматически)
        extra_kwargs = {'case': {'required': False}}

class SchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        # То же самое для схем
        fields = ['id', 'case', 'scheme_img', 'scheme_description_img']
        extra_kwargs = {'case': {'required': False}}

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'case', 'name', 'instruction', 'qtype', 'answers']
        # Делаем case необязательным при валидации, чтобы при создании через CaseSerializer
        # не возникало ошибки (там case подставляется вручную).
        # Но при прямом создании вопроса через /api/questions/ поле case обязательно.
        extra_kwargs = {'case': {'required': False}}

    def create(self, validated_data):
        """
        Создание вопроса (POST /api/questions/).
        Требует передачи 'case' в теле запроса.
        """
        answers_data = validated_data.pop('answers')

        # Если создаем вопрос отдельно, case должен быть в validated_data
        question = Question.objects.create(**validated_data)

        for ans in answers_data:
            Answer.objects.create(question=question, **ans)
        return question


class CaseSerializer(serializers.ModelSerializer):
    # Вложенные сериализаторы для удобного заполнения (read/write)
    layers = LayerSerializer(many=True, required=False)
    schemes = SchemeSerializer(many=True, required=False)
    questions = QuestionSerializer(many=True, required=False)

    class Meta:
        model = Case
        fields = ['id', 'name', 'pathology', 'created_at', 'layers', 'schemes', 'questions']

    def create(self, validated_data):
        """
        Создание Кейса со всей вложенной структурой:
        Case -> Layers
             -> Schemes
             -> Questions -> Answers
        """
        layers_data = validated_data.pop('layers', [])
        schemes_data = validated_data.pop('schemes', [])
        questions_data = validated_data.pop('questions', [])

        # 1. Создаем сам Case
        case = Case.objects.create(**validated_data)

        # 2. Создаем Layers
        for layer_data in layers_data:
            Layer.objects.create(case=case, **layer_data)

        # 3. Создаем Schemes
        for scheme_data in schemes_data:
            Scheme.objects.create(case=case, **scheme_data)

        # 4. Создаем Questions (и внутри Answers)
        for q_data in questions_data:
            answers_data = q_data.pop('answers', [])

            # При создании вопроса привязываем его к только что созданному case
            question = Question.objects.create(case=case, **q_data)

            # Создаем ответы
            for ans_data in answers_data:
                Answer.objects.create(question=question, **ans_data)

        return case


class PathologySerializer(serializers.ModelSerializer):
    images = PathologyImageSerializer(many=True, read_only=True)
    # Для просмотра списка кейсов внутри патологии (без глубокой вложенности вопросов, чтобы не грузить атлас)
    # Если нужно видеть вопросы в атласе - уберите fields в CaseSerializer или создайте отдельный LiteCaseSerializer
    cases = CaseSerializer(many=True, read_only=True)

    class Meta:
        model = Pathology
        fields = ['id', 'name', 'description', 'images', 'cases']


# -------------------------------------------------------------------------
# ЛОГИКА ТЕСТИРОВАНИЯ
# -------------------------------------------------------------------------

class TestSubmissionSerializer(serializers.Serializer):
    pathology_id = serializers.IntegerField()
    # Список ID кейсов, которые пользователь выбрал для теста
    case_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    # Список ID ответов, которые выбрал пользователь
    answer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[]
    )


class TestResultSerializer(serializers.ModelSerializer):
    pathology_name = serializers.CharField(source='pathology.name', read_only=True)

    class Meta:
        model = TestResult
        fields = ['id', 'user', 'pathology', 'pathology_name', 'score', 'max_score', 'percentage', 'grade',
                  'created_at']



class PathologyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pathology
        fields = ("id", "name")


# Вспомогательный сериализатор, возвращает только ID кейса
class CaseIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ("id",)

# Основной сериализатор для этого эндпоинта
class ClinicalCaseInfoSerializer(serializers.ModelSerializer):
    cases = CaseIdSerializer(many=True, read_only=True)

    class Meta:
        model = Pathology
        fields = ("id", "name", "cases")

class PathologyDetailInfoSerializer(serializers.ModelSerializer):
    imgContainer = serializers.SerializerMethodField()

    class Meta:
        model = Pathology
        fields = ("id", "imgContainer", "description")

    def get_imgContainer(self, obj):
        request = self.context.get('request')
        images = obj.images.all()
        urls = []
        for img in images:
            if img.image:
                url = request.build_absolute_uri(img.image.url) if request else img.image.url
                urls.append(url)
        return urls