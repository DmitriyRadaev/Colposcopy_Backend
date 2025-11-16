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



class Pathology(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)


class Case(models.Model):
    pathology = models.ForeignKey(Pathology, on_delete=models.CASCADE, related_name="cases")
    name = models.CharField(max_length=255, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name or f"Case {self.pk}"

class Task(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="tasks")
    def __str__(self):
        return f"{self.pk}"

class Question(models.Model):

    class qtype(models.TextChoices):
        single = 'single'
        multiple = 'multiple'

    name = models.CharField(max_length=255, null=False, blank=False)
    instruction = models.CharField(max_length=255, null=False, blank=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="questions")
    qtype = models.CharField(max_length=20, choices=qtype.choices, default=qtype.single)

class Layer(models.Model):

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="layers")
    number = models.PositiveIntegerField(default=1)
    layer_img = models.ImageField(upload_to="static/case_layers/")
    layer_description = models.TextField(max_length=255, blank=True)

    class Meta:
        unique_together = ("case", "number")
        ordering = ("number",)

    def __str__(self):
        return f"{self.case} — Layer {self.number}"

class Scheme(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="schemes")
    scheme_img = models.ImageField(upload_to="static/schemes/scheme_img/")
    scheme_description_img = models.ImageField(upload_to="static/schemes/scheme_description_img/")

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text
