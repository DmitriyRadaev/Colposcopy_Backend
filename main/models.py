from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    admin_list = models.ForeignKey('UniversityAdmin',on_delete=models.CASCADE,null=True)
    def __str__(self):
        return self.name

class UniversityAdmin(models.Model):
    fullname = models.CharField(max_length=120)
    university = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    date_start = models.DateField(auto_now=False, auto_now_add=True)
    date_end = models.DateField(auto_now=False, auto_now_add=True)
    student_list = models.ForeignKey('Student', on_delete=models.CASCADE,null=True)
    def __str__(self):
        return self.fullname

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

