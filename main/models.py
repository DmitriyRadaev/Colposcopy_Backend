# models.py
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


# -------------------------------------------------------------------------
# ACCOUNT / AUTHENTICATION
# -------------------------------------------------------------------------
class AccountManager(BaseUserManager):
    def create_user(self, email, name, surname, patronymic=None, password=None, role="WORKER", **kwargs):
        if not email:
            raise ValueError("Email is required")
        if not name:
            raise ValueError("Name is required")
        if not surname:
            raise ValueError("Surname is required")

        email = self.normalize_email(email)
        # Сохраняем name, surname, patronymic
        user = self.model(
            email=email,
            name=name,
            surname=surname,
            patronymic=patronymic or "",  # Если None, пишем пустую строку
            role=role,
            **kwargs
        )
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, surname, password=None, **kwargs):
        # Передаем параметры в create_user
        user = self.create_user(
            email=email,
            name=name,
            surname=surname,
            password=password,
            role=Account.Role.SUPERADMIN,
            **kwargs
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def create_admin(self, email, name, surname, password=None, **kwargs):
        user = self.create_user(
            email=email,
            name=name,
            surname=surname,
            password=password,
            role=Account.Role.ADMIN,
            **kwargs
        )
        user.is_staff = True
        user.save(using=self._db)
        return user

    def create_worker(self, email, name, surname, patronymic=None, password=None, work=None, position=None,
                      **kwargs):
        user = self.create_user(
            email=email,
            name=name,
            surname=surname,
            patronymic=patronymic,
            password=password,
            role=Account.Role.WORKER,
            **kwargs
        )

        if work is not None or position is not None:
            # Получаем модель WorkerProfile динамически, чтобы избежать циклического импорта, если они в одном файле
            # или просто импортируем, если структура позволяет.
            # Здесь предполагаем, что они в одном файле models.py
            WorkerProfile.objects.update_or_create(user=user, defaults={
                "work": work or "",
                "position": position or ""
            })
        return user


class Account(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Главный администратор"
        ADMIN = "ADMIN", "Администратор"
        WORKER = "WORKER", "Работник"

    email = models.EmailField(null=False, blank=False, unique=True)

    # --- Новые поля вместо username ---
    name = models.CharField(max_length=50, blank=False, null=False, verbose_name="Имя")
    surname = models.CharField(max_length=50, blank=False, null=False, verbose_name="Фамилия")
    patronymic = models.CharField(max_length=50, blank=True, default="", verbose_name="Отчество")
    # ----------------------------------

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.WORKER)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    # Поля, обязательные при создании суперюзера через консоль (кроме email и пароля)
    REQUIRED_FIELDS = ["name", "surname"]

    def __str__(self):
        # Красивое отображение ФИО
        full_name = f"{self.surname} {self.name} {self.patronymic}".strip()
        return f"{full_name} ({self.role})"

    def has_perm(self, perm, obj=None):
        if self.is_superuser or self.role == Account.Role.SUPERADMIN:
            return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        if self.is_superuser or self.role == Account.Role.SUPERADMIN:
            return True
        return True

    @property
    def is_superadmin(self):
        return self.role == Account.Role.SUPERADMIN

    @property
    def is_admin_role(self):
        return self.role == Account.Role.ADMIN

    @property
    def is_worker(self):
        return self.role == Account.Role.WORKER

class WorkerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="worker_profile")
    work = models.CharField(max_length=255, blank=True, null=False)
    position = models.CharField(max_length=255, blank=True, null=False)

    def __str__(self):
        return f"Profile for {self.user.email}"


# -------------------------------------------------------------------------
# MAIN CONTENT MODELS
# -------------------------------------------------------------------------

class Pathology(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)

    def __str__(self):
        return self.name


class PathologyImage(models.Model):
    pathology = models.ForeignKey(Pathology, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="pathology_img/", null=False, blank=False)


class Case(models.Model):
    pathology = models.ForeignKey(Pathology, on_delete=models.CASCADE, related_name="cases")
    name = models.CharField(max_length=255, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Case {self.pk}"


class Layer(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="layers")
    number = models.PositiveIntegerField(default=1)
    layer_img = models.ImageField(upload_to="case_layers/")
    layer_description = models.TextField(blank=True)

    class Meta:
        unique_together = ("case", "number")
        ordering = ("number",)

    def __str__(self):
        return f"{self.case} — Layer {self.number}"


class Scheme(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="schemes")
    scheme_img = models.ImageField(upload_to="schemes/scheme_img/")
    scheme_description_img = models.ImageField(upload_to="schemes/scheme_description_img/")


# -------------------------------------------------------------------------
# TESTING LOGIC
# -------------------------------------------------------------------------

class Question(models.Model):
    class qtype(models.TextChoices):
        single = 'single'
        multiple = 'multiple'

    # Changed: Linked directly to Case (removed Task model)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="questions")

    name = models.CharField(max_length=255, null=False, blank=False)
    instruction = models.CharField(max_length=255, null=False, blank=False)
    qtype = models.CharField(max_length=20, choices=qtype.choices, default=qtype.single)

    def __str__(self):
        return self.name


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class TestResult(models.Model):
    """
    Модель для хранения истории прохождения тестов пользователями.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="test_results")
    pathology = models.ForeignKey(Pathology, on_delete=models.SET_NULL, null=True, related_name="test_results")

    # Статистика попытки
    score = models.IntegerField(default=0)  # Количество правильных ответов пользователя
    max_score = models.IntegerField(default=0)  # Общее количество правильных ответов в тесте
    percentage = models.FloatField(default=0.0)  # Процент прохождения

    # Текстовая оценка (Отлично, Хорошо, Удовлетворительно, Неудовлетворительно)
    grade = models.CharField(max_length=30, blank=True)
    time_spent = models.DurationField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.percentage}% ({self.grade})"


class UserTestAnswer(models.Model):
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)

    def __str__(self):
        return f"Result {self.test_result.id} - Ans {self.answer.id}"