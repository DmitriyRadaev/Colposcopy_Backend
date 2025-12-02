# serializers.py
from rest_framework import serializers, generics
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


# Сериализатор для ОТВЕТА сервера (результат теста)
class TestResultSerializer(serializers.ModelSerializer):
    pathology_name = serializers.CharField(source='pathology.name', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = TestResult
        fields = ['id', 'user_name', 'pathology_name', 'score', 'max_score', 'percentage', 'grade', 'created_at']



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


class CaseDetailInfoSerializer(serializers.ModelSerializer):
    imgContainer = serializers.SerializerMethodField()
    descriptionContainer = serializers.SerializerMethodField()
    imgSchema = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = ("id", "imgContainer", "imgSchema", "descriptionContainer")

    def get_imgContainer(self, obj):
        request = self.context.get('request')
        urls = []

        # 1. Добавляем картинки слоев (Layers)
        layers = obj.layers.all().order_by('number')
        for layer in layers:
            if layer.layer_img:
                url = layer.layer_img.url.replace('\\', '/')
                if request:
                    url = request.build_absolute_uri(url)
                urls.append(url)

        # 2. Добавляем картинку схемы (Scheme) в КОНЕЦ этого же списка
        scheme = obj.schemes.first()
        if scheme and scheme.scheme_img:
            url_scheme = scheme.scheme_img.url.replace('\\', '/')
            if request:
                url_scheme = request.build_absolute_uri(url_scheme)
            urls.append(url_scheme)

        return urls

    def get_imgSchema(self, obj):
        # Здесь возвращаем картинку ОПИСАНИЯ схемы (scheme_description_img)
        request = self.context.get('request')
        scheme = obj.schemes.first()

        if scheme and scheme.scheme_description_img:
            url = scheme.scheme_description_img.url.replace('\\', '/')
            if request:
                return request.build_absolute_uri(url)
            return url
        return ""

    def get_descriptionContainer(self, obj):
        # Текстовые описания слоев
        layers = obj.layers.all().order_by('number')
        descriptions = []
        for layer in layers:
            # Добавляем описание, даже если оно пустое, чтобы индексы совпадали с картинками (если нужно)
            # Или добавляем только если есть текст:
            if layer.layer_description:
                descriptions.append(layer.layer_description)
        return descriptions


class TestAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ('id', 'text')

class TestQuestionSerializer(serializers.ModelSerializer):
    question = serializers.CharField(source='name')
    # Меняем IntegerField на SerializerMethodField, чтобы обработать вручную
    typeQuestion = serializers.SerializerMethodField()
    instructions = serializers.CharField(source='instruction')
    answers = TestAnswerSerializer(many=True)

    class Meta:
        model = Question
        fields = ('id', 'question', 'typeQuestion', 'instructions', 'answers')

    def get_typeQuestion(self, obj):
        # Логика превращения текста в цифру для фронта
        # Если в базе "multiple" -> отправляем 1
        # Если "single" или что-то другое -> отправляем 0
        if str(obj.qtype).lower() == "multiple":
            return 1
        return 0

class TestTaskSerializer(serializers.ModelSerializer):
    imageSrcs = serializers.SerializerMethodField()
    testsQuestions = TestQuestionSerializer(source='questions', many=True)

    class Meta:
        model = Case
        fields = ('id', 'imageSrcs', 'testsQuestions')

    def get_imageSrcs(self, obj):
        request = self.context.get('request')
        urls = []
        # Слои
        for layer in obj.layers.all().order_by('number'):
            if layer.layer_img:
                url = layer.layer_img.url.replace('\\', '/')
                if request: url = request.build_absolute_uri(url)
                urls.append(url)
        # Схема (если надо)
        scheme = obj.schemes.first()
        if scheme and scheme.scheme_img:
            s_url = scheme.scheme_img.url.replace('\\', '/')
            if request: s_url = request.build_absolute_uri(s_url)
            urls.append(s_url)
        return urls



class QuestionSubmissionSerializer(serializers.Serializer):
    questionId = serializers.IntegerField()
    selectedAnswers = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True
    )

class CaseSubmissionSerializer(serializers.Serializer):
    caseId = serializers.IntegerField()
    answers = QuestionSubmissionSerializer(many=True)


class TestSubmissionWrapperSerializer(serializers.Serializer):
    items = CaseSubmissionSerializer(many=True)
    duration = serializers.IntegerField(min_value=0, required=False, default=0)

class QuestionBulkCreateView(generics.CreateAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    def get_serializer(self, *args, **kwargs):
        # Если входящие данные ('data') — это список, ставим many=True
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)


class UserProfileSerializer(serializers.ModelSerializer):
    # Явно объявляем поля профиля, так как их нет в модели Account
    work = serializers.CharField(required=False, allow_blank=True)
    position = serializers.CharField(required=False, allow_blank=True)

    # Пароль делаем необязательным, чтобы можно было обновить профиль без смены пароля
    password = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Account
        fields = ("name", "surname", "patronymic", "email", "work", "position", "password")

    def to_representation(self, instance):
        """
        Этот метод формирует JSON, который улетит на фронтенд (GET запрос).
        """
        data = super().to_representation(instance)

        # 1. Достаем данные из профиля (WorkerProfile)
        # Используем getattr, чтобы не упасть с ошибкой, если профиля нет
        profile = getattr(instance, 'worker_profile', None)

        data['work'] = profile.work if profile else ""
        data['position'] = profile.position if profile else ""

        # 2. Пароль всегда возвращаем пустой (заглушка)
        data['password'] = ""

        return data

    def update(self, instance, validated_data):
        """
        Этот метод срабатывает при сохранении (PUT/PATCH запрос).
        """
        # 1. Извлекаем данные, которые не относятся напрямую к модели Account
        work = validated_data.pop('work', None)
        position = validated_data.pop('position', None)
        password = validated_data.pop('password', None)

        # 2. Обновляем основные поля Account (email, name, surname...)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # 3. Если пришел пароль и он не пустой — обновляем его
        if password:
            instance.set_password(password)

        instance.save()

        # 4. Обновляем или создаем профиль работника
        # Если work или position пришли в запросе (даже если пустые строки)
        if work is not None or position is not None:
            WorkerProfile.objects.update_or_create(
                user=instance,
                defaults={
                    'work': work if work is not None else "",
                    'position': position if position is not None else ""
                }
            )

        return instance


class UserTryInfoSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    date = serializers.SerializerMethodField()
    mark = serializers.CharField(source='grade')
    time = serializers.SerializerMethodField()

    class Meta:
        model = TestResult
        fields = ('id', 'date', 'mark', 'time')

    def get_date(self, obj):
        return obj.created_at.strftime("%d.%m.%Y")

    def get_time(self, obj):
        # obj.time_spent — это объект timedelta (или None)
        if obj.time_spent:
            total_seconds = int(obj.time_spent.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            # Вернет строку вида "05:03"
            return f"{minutes:02}:{seconds:02}"
        return "00:00"


# --- Level 1: IAnswers ---
class HistoryAnswerSerializer(serializers.ModelSerializer):
    # Исправлено: isSelecterd -> isSelected
    isSelected = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = ('id', 'text', 'isSelected')

    def get_isSelected(self, obj):
        # Получаем множество ID выбранных пользователем ответов из контекста
        selected_ids = self.context.get('selected_answer_ids', set())
        return obj.id in selected_ids


# --- Level 2: ITestQuestion ---
class HistoryQuestionSerializer(serializers.ModelSerializer):
    question = serializers.CharField(source='name')
    # 0 или 1
    typeQuestion = serializers.SerializerMethodField()
    instructions = serializers.CharField(source='instruction')
    # Правильно ли отвечен весь вопрос
    isCorrect = serializers.SerializerMethodField()
    answers = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ('id', 'question', 'isCorrect', 'typeQuestion', 'instructions', 'answers')

    def get_typeQuestion(self, obj):
        # Превращаем "multiple" -> 1, "single" -> 0
        if str(obj.qtype).lower() == "multiple":
            return 1
        return 0

    def get_isCorrect(self, obj):
        """
        Проверка правильности ответа на вопрос.
        Сравниваем множество правильных ответов с множеством выбранных пользователем.
        """
        selected_ids = self.context.get('selected_answer_ids', set())

        # 1. ID всех правильных вариантов для этого вопроса
        correct_answer_ids = set(a.id for a in obj.answers.all() if a.is_correct)

        # 2. ID вариантов этого вопроса, которые выбрал юзер
        # (пересечение всех выборов юзера и вариантов этого вопроса)
        all_options_ids = set(a.id for a in obj.answers.all())
        user_picked_in_this_question = selected_ids.intersection(all_options_ids)

        # 3. Если множества равны — вопрос отвечен верно
        return correct_answer_ids == user_picked_in_this_question

    def get_answers(self, obj):
        return HistoryAnswerSerializer(
            obj.answers.all(),
            many=True,
            context=self.context
        ).data


# --- Level 3: ITestTask ---
class HistoryTaskSerializer(serializers.ModelSerializer):
    imageSrcs = serializers.SerializerMethodField()
    testsQuestions = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = ('id', 'imageSrcs', 'testsQuestions')

    def get_imageSrcs(self, obj):
        request = self.context.get('request')
        urls = []
        # Слои
        for layer in obj.layers.all().order_by('number'):
            if layer.layer_img:
                url = layer.layer_img.url.replace('\\', '/')
                if request: url = request.build_absolute_uri(url)
                urls.append(url)
        # Схема (если есть)
        scheme = obj.schemes.first()
        if scheme and scheme.scheme_img:
            s_url = scheme.scheme_img.url.replace('\\', '/')
            if request: s_url = request.build_absolute_uri(s_url)
            urls.append(s_url)
        return urls

    def get_testsQuestions(self, obj):
        return HistoryQuestionSerializer(
            obj.questions.all(),
            many=True,
            context=self.context
        ).data