from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.conf import settings

class AccountManager(BaseUserManager):
    def create_user(self, email, username, password=None, role="WORKER", **kwargs):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, role=role, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password, **kwargs):
        # superadmin — главный админ
        user = self.create_user(email=email, username=username, password=password, role=Account.Role.SUPERADMIN, **kwargs)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def create_admin(self, email, username, password=None, **kwargs):
        user = self.create_user(email=email, username=username, password=password, role=Account.Role.ADMIN, **kwargs)
        user.is_staff = True
        user.save(using=self._db)
        return user

    def create_worker(self, email, username, password=None, **kwargs):
        return self.create_user(email=email, username=username, password=password, role=Account.Role.WORKER, **kwargs)


class Account(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Главный администратор"
        ADMIN = "ADMIN", "Администратор"
        WORKER = "WORKER", "Работник"

    email = models.EmailField(null=False, blank=False, unique=True)
    username = models.CharField(max_length=50, blank=False, null=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.WORKER)

    is_admin = models.BooleanField(default=False)     # можно использовать для логики
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)     # даёт доступ в admin-site
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.username} ({self.role})"

    def has_perm(self, perm, obj=None):
        # по умолчанию суперюзер имеет всё
        if self.is_superuser or self.role == Account.Role.SUPERADMIN:
            return True
        # можно расширять: проверять конкретные perms
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        if self.is_superuser or self.role == Account.Role.SUPERADMIN:
            return True
        return True  # или ограничить

    # дополнительное удобство:
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
    place_of_work = models.CharField(max_length=255, blank=True, null=False)
    position = models.CharField(max_length=255, blank=True, null=False)

    def __str__(self):
        return f"Profile for {self.user.email}"

class Attempt(models.Model):
    start_time = models.TimeField(auto_now=False, auto_now_add=True)
    end_time = models.TimeField()
    mark = models.IntegerField()
    status = models.CharField(max_length=120)
    WorkerProfile = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE)
    def __str__(self):
        return self.start_time,self.end_time,self.mark,self.status

class Task(models.Model):
    category = models.CharField(max_length=120)
    case = models.ForeignKey('Case', on_delete=models.CASCADE)
    def __str__(self):
        return self.category

class Case(models.Model):
    description = models.TextField()
    diagnosis = models.CharField(max_length=120)
    layer1 = models.ForeignKey('Layer1', on_delete=models.CASCADE)
    layer2 = models.ForeignKey('Layer2', on_delete=models.CASCADE)
    layer3 = models.ForeignKey('Layer3', on_delete=models.CASCADE)
    layer4 = models.ForeignKey('Layer4', on_delete=models.CASCADE)
    parameters = models.ForeignKey('Parameter', on_delete=models.CASCADE)
    recommendations = models.ForeignKey('Recommendation', on_delete=models.CASCADE)
    def __str__(self):
        return self.description
class Parameter(models.Model):
    name = models.CharField(max_length=120)
    def __str__(self):
        return self.name
class Recommendation(models.Model):
    name = models.CharField(max_length=120)
    def __str__(self):
        return self.name
class Layer1(models.Model):
    layer_img = models.ImageField(upload_to='images/')
    layer_description = models.CharField(max_length=120)
    def __str__(self):
        return self.layer_img
class Layer2(models.Model):
    layer_img = models.ImageField(upload_to='images/')
    layer_description = models.CharField(max_length=120)
    def __str__(self):
        return self.layer_img

class Layer3(models.Model):
    layer_img = models.ImageField(upload_to='images/')
    layer_description = models.CharField(max_length=120)
    def __str__(self):
        return self.layer_img

class Layer4(models.Model):
    layer_img = models.ImageField(upload_to='images/')
    book_img = models.ImageField(upload_to='images/')
    def __str__(self):
        return self.layer_img

