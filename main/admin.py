from django.contrib import admin
from .models import (
    Account, WorkerProfile, Pathology, PathologyImage, Case, Task, Question,
    Answer, Layer, Scheme, Attempt, AttemptAnswer
)

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "username", "role", "is_staff", "is_superuser")
    list_filter = ("role", "is_staff", "is_superuser")
    search_fields = ("email", "username")

@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "place_of_work", "position")

@admin.register(Pathology)
class PathologyAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

@admin.register(PathologyImage)
class PathologyImageAdmin(admin.ModelAdmin):
    list_display = ("id", "pathology", "image")

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "pathology", "created_at")

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "case")

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "task", "qtype")

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "question", "is_correct")
    list_filter = ("is_correct",)

@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    list_display = ("id", "case", "number")

@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    list_display = ("id", "case")

@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "worker", "start_time", "end_time", "created_at")
    filter_horizontal = ("cases",)

@admin.register(AttemptAnswer)
class AttemptAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "attempt", "question", "is_correct")
    filter_horizontal = ("selected_answers",)
