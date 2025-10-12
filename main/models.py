from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


class AccountManager(BaseUserManager):
    def create_user(self, email, username, password=None, **kwargs):

        if not email:
            raise ValueError("Email is required")

        if not username:
            raise ValueError("Username is required")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, username, password, **kwargs):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password
        )

        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return


class Account(AbstractBaseUser,PermissionsMixin):
    email = models.EmailField(null=False, blank=False, unique=True)
    username = models.CharField(max_length=50, blank=False, null=False)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

class Student(models.Model):
    surname = models.CharField(max_length=120)
    name = models.CharField(max_length=120)
    middle_name = models.CharField(max_length=120)
    birth_date = models.DateField()
    email = models.EmailField(unique=True)
    def __str__(self):
        return f"{self.surname} {self.name} {self.middle_name}"

class Attempt(models.Model):
    start_time = models.TimeField(auto_now=False, auto_now_add=True)
    end_time = models.TimeField()
    mark = models.IntegerField()
    status = models.CharField(max_length=120)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
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

