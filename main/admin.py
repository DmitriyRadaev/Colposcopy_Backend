from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    Account, WorkerProfile, Pathology, PathologyImage,
    Case, Layer, Scheme, Question, Answer, TestResult, UserTestAnswer
)



@admin.register(Account)
class AccountAdmin(UserAdmin):
    list_display = ('email', 'name', 'surname', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'name', 'surname')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Личная информация'), {'fields': ('name', 'surname', 'patronymic')}),
        (_('Роль и права'), {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        (_('Даты'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'surname', 'password1', 'password2', 'role'),
        }),
    )

    readonly_fields = ('last_login', 'created_at', 'updated_at')


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'work', 'position')
    search_fields = ('user__email', 'user__name', 'user__surname', 'work', 'position')
    raw_id_fields = ('user',)



class PathologyImageInline(admin.TabularInline):
    model = PathologyImage
    extra = 1


@admin.register(Pathology)
class PathologyAdmin(admin.ModelAdmin):
    list_display = ('name', 'cases_count', 'description_preview')
    search_fields = ('name', 'description')
    inlines = [PathologyImageInline]

    def cases_count(self, obj):
        return obj.cases.count()

    cases_count.short_description = 'Количество кейсов'

    def description_preview(self, obj):
        if len(obj.description) > 100:
            return obj.description[:100] + '...'
        return obj.description

    description_preview.short_description = 'Описание'


@admin.register(PathologyImage)
class PathologyImageAdmin(admin.ModelAdmin):
    list_display = ('pathology', 'image_preview')
    list_filter = ('pathology',)

    def image_preview(self, obj):
        if obj.image:
            return f'📷 Изображение'
        return '—'

    image_preview.short_description = 'Превью'

class LayerInline(admin.TabularInline):
    model = Layer
    extra = 1


class SchemeInline(admin.TabularInline):
    model = Scheme
    extra = 1


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'pathology', 'created_at', 'layers_count')
    list_filter = ('pathology', 'created_at')
    search_fields = ('name', 'pathology__name')
    inlines = [LayerInline, SchemeInline]

    def layers_count(self, obj):
        return obj.layers.count()

    layers_count.short_description = 'Слои'


@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    list_display = ('case', 'number', 'layer_preview')
    list_filter = ('case__pathology', 'case')
    search_fields = ('case__name', 'layer_description')
    ordering = ('case', 'number')

    def layer_preview(self, obj):
        if obj.layer_img:
            return f'📷 Слой {obj.number}'
        return '—'

    layer_preview.short_description = 'Изображение'


@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    list_display = ('case', 'scheme_preview', 'description_preview')
    list_filter = ('case__pathology', 'case')

    def scheme_preview(self, obj):
        if obj.scheme_img:
            return f'📊 Схема'
        return '—'

    scheme_preview.short_description = 'Схема'

    def description_preview(self, obj):
        if obj.scheme_description_img:
            return f'📝 Описание'
        return '—'

    description_preview.short_description = 'Описание'



class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 3


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('name', 'case', 'qtype', 'instruction_preview')
    list_filter = ('case__pathology', 'case', 'qtype')
    search_fields = ('name', 'instruction')
    inlines = [AnswerInline]

    def instruction_preview(self, obj):
        if len(obj.instruction) > 50:
            return obj.instruction[:50] + '...'
        return obj.instruction

    instruction_preview.short_description = 'Инструкция'

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'text_preview', 'is_correct')
    list_filter = ('question__case', 'question')
    search_fields = ('text', 'question__name')

    def text_preview(self, obj):
        if len(obj.text) > 50:
            return obj.text[:50] + '...'
        return obj.text

    text_preview.short_description = 'Текст ответа'


class UserTestAnswerInline(admin.TabularInline):
    model = UserTestAnswer
    extra = 0
    readonly_fields = ('question', 'answer')
    can_delete = False


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'pathology', 'score', 'max_score', 'percentage', 'grade', 'created_at')
    list_filter = ('pathology', 'grade', 'created_at')
    search_fields = ('user__email', 'user__name', 'user__surname')
    readonly_fields = ('user', 'pathology', 'score', 'max_score', 'percentage', 'grade', 'created_at')
    inlines = [UserTestAnswerInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserTestAnswer)
class UserTestAnswerAdmin(admin.ModelAdmin):
    list_display = ('test_result', 'question', 'answer', 'is_correct')
    list_filter = ('test_result__pathology',)
    readonly_fields = ('test_result', 'question', 'answer')

    def is_correct(self, obj):
        return obj.answer.is_correct

    is_correct.boolean = True
    is_correct.short_description = 'Правильный?'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.site_header = "Панель управления"
admin.site.site_title = "Админ-панель"
admin.site.index_title = "Добро пожаловать в админ-панель"
