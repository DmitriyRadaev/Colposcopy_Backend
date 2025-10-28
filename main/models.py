# models.py
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


# -------------------------
# Account / AccountManager
# -------------------------
class AccountManager(BaseUserManager):
    def create_user(self, email, username, password=None, role="WORKER", **kwargs):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, role=role, **kwargs)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **kwargs):
        # superadmin — главный админ
        user = self.create_user(email=email, username=username, password=password, role=Account.Role.SUPERADMIN, **kwargs)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def create_admin(self, email, username, password=None, **kwargs):
        user = self.create_user(email=email, username=username, password=password, role=Account.Role.ADMIN, **kwargs)
        user.is_staff = True
        user.save(using=self._db)
        return user

    def create_worker(self, email, username, password=None, place_of_work=None, position=None, **kwargs):

        user = self.create_user(email=email, username=username, password=password, role=Account.Role.WORKER, **kwargs)

        # Создаём профиль, если переданы данные (динамический импорт, чтобы избежать циклов)
        if place_of_work is not None or position is not None:
            WorkerProfile = self.model._meta.apps.get_model(self.model._meta.app_label, 'WorkerProfile')
            WorkerProfile.objects.update_or_create(user=user, defaults={
                "place_of_work": place_of_work or "",
                "position": position or ""
            })
        return user


class Account(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Главный администратор"
        ADMIN = "ADMIN", "Администратор"
        WORKER = "WORKER", "Работник"

    email = models.EmailField(null=False, blank=False, unique=True)
    username = models.CharField(max_length=50, blank=False, null=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.WORKER)

    # legacy / access flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)     # даёт доступ в admin-site
    is_superuser = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.username} ({self.role})"

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


# -------------------------
# Worker profile
# -------------------------
class WorkerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="worker_profile")
    place_of_work = models.CharField(max_length=255, blank=True, null=False)
    position = models.CharField(max_length=255, blank=True, null=False)

    def __str__(self):
        return f"Profile for {self.user.email}"


# -------------------------
# Parameters / Recommendations / Case / Layer / Task
# -------------------------
class Parameter(models.Model):
    name = models.CharField(max_length=120)

    def __str__(self):
        return self.name


class Recommendation(models.Model):
    name = models.CharField(max_length=120)

    def __str__(self):
        return self.name


class Case(models.Model):

    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True)
    diagnosis = models.CharField(max_length=255, blank=True)
    parameters = models.ManyToManyField(Parameter, blank=True, related_name="cases")
    recommendations = models.ManyToManyField(Recommendation, blank=True, related_name="cases")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Case {self.pk}"


class Layer(models.Model):

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="layers")
    number = models.PositiveIntegerField(default=1)
    layer_img = models.ImageField(upload_to="case_layers/")
    layer_description = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("case", "number")
        ordering = ("number",)

    def __str__(self):
        return f"{self.case} — Layer {self.number}"


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="tasks")
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title} (Case: {self.case})"


# -------------------------
# Question / Choice (for tests)
# -------------------------
class Question(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="questions", null=True, blank=True)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="questions", null=True, blank=True)
    title = models.CharField(max_length=255)         # "Задание №1: Первичный осмотр"
    instruction = models.TextField(blank=True)       # "Инструкция: Выберите один ответ."
    multiple = models.BooleanField(default=False)    # multiple-choice?
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order",)

    def __str__(self):
        return self.title


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=1000)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.question.title[:40]} — {self.text[:60]}"


# -------------------------
# Attempt / AttemptAnswer
# -------------------------
class Attempt(models.Model):
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attempts")
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="attempts")
    case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True, blank=True, related_name="attempts")

    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)

    correct_count = models.PositiveIntegerField(default=0)
    incorrect_count = models.PositiveIntegerField(default=0)
    score = models.FloatField(null=True, blank=True)  # e.g. percent 0..100

    status = models.CharField(max_length=50, default="in_progress")  # in_progress / finished
    details = models.JSONField(null=True, blank=True)  # optional detailed report

    created_at = models.DateTimeField(auto_now_add=True)

    def finish(self):
        self.end_time = timezone.now()
        if self.start_time and self.end_time:
            self.duration = self.end_time - self.start_time
        answers = self.answers.all()
        total = answers.count()
        correct = sum(1 for a in answers if a.is_correct)
        self.correct_count = correct
        self.incorrect_count = max(0, total - correct)
        self.score = (correct / total * 100) if total > 0 else 0.0
        self.status = "finished"
        self.save()

    def __str__(self):
        return f"Attempt {self.pk} by {self.worker}"


class AttemptAnswer(models.Model):
    """
    One selected answer inside an Attempt. For multiple selections, create multiple AttemptAnswer rows
    (one per selected Choice) or extend with M2M if preferred.
    """
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    free_text = models.TextField(blank=True)  # for open answers if any
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(default=timezone.now)
    time_spent = models.DurationField(null=True, blank=True)

    def evaluate(self):
        if self.selected_choice:
            self.is_correct = bool(self.selected_choice.is_correct)
        else:
            self.is_correct = False
        self.save()

    def save(self, *args, **kwargs):
        # auto-evaluate on save if possible
        if self.selected_choice and self.selected_choice_id:
            self.is_correct = bool(self.selected_choice.is_correct)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Answer to Q{self.question.pk} (Attempt {self.attempt.pk})"
