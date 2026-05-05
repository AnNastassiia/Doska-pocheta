from django.contrib import admin
from datetime import date
from django.utils import timezone

# Register your models here.

from .models import Student, Achievement, Employer, ManagerProfile, ContactRequest, Vacancy, Application, Notification


class StudentAgeGroupFilter(admin.SimpleListFilter):
    title = 'Возраст'
    parameter_name = 'age_group'

    def lookups(self, request, model_admin):
        return (
            ('adult', 'Совершеннолетние (18+)'),
            ('minor', 'Несовершеннолетние (<18)'),
            ('unknown', 'Возраст не указан'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        today = timezone.localdate()
        try:
            adult_cutoff = today.replace(year=today.year - 18)
        except ValueError:
            # Для 29 февраля в невисокосный год
            adult_cutoff = date(today.year - 18, 2, 28)

        if value == 'unknown':
            return queryset.filter(birth_date__isnull=True)
        if value == 'adult':
            return queryset.filter(birth_date__isnull=False, birth_date__lte=adult_cutoff)
        if value == 'minor':
            return queryset.filter(birth_date__isnull=False, birth_date__gt=adult_cutoff)
        return queryset


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'course', 'student_card_number', 'is_approved', 'created_at']
    list_filter = ['course', 'is_approved', 'data_processing_consent', StudentAgeGroupFilter]
    search_fields = ['full_name', 'course', 'student_card_number']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_students', 'reject_students']

    def approve_students(self, request, queryset):
        queryset.update(is_approved=True)
    approve_students.short_description = 'Одобрить выбранных студентов на доске почета'

    def reject_students(self, request, queryset):
        queryset.update(is_approved=False)
    reject_students.short_description = 'Отклонить выбранных студентов'


@admin.register(ManagerProfile)
class ManagerProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['full_name', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'sector', 'contact_person', 'is_approved', 'created_at']
    list_filter = ['sector', 'is_approved']
    search_fields = ['company_name', 'contact_person']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_employers', 'reject_employers']

    def approve_employers(self, request, queryset):
        queryset.update(is_approved=True)
    approve_employers.short_description = 'Одобрить работодателей'

    def reject_employers(self, request, queryset):
        queryset.update(is_approved=False)
    reject_employers.short_description = 'Отклонить работодателей'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['title', 'student', 'achievement_type', 'date_achieved', 'is_approved', 'is_public']
    list_filter = ['is_approved', 'is_public', 'achievement_type', 'date_achieved']
    search_fields = ['title', 'student__full_name', 'description']
    list_editable = ['is_approved', 'is_public']  # можно менять прямо в списке
    
    # Действия для массового одобрения
    actions = ['approve_selected', 'make_public']
    
    def approve_selected(self, request, queryset):
        queryset.update(is_approved=True)
    approve_selected.short_description = "Одобрить выбранные достижения"
    
    def make_public(self, request, queryset):
        queryset.update(is_public=True)
    make_public.short_description = "Опубликовать на доске почета"


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ['student', 'employer', 'status', 'requested_at', 'responded_at']
    list_filter = ['status', 'requested_at']
    search_fields = ['student__full_name', 'employer__company_name', 'employer__user__email']


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer', 'employment_type', 'status', 'is_public', 'created_at']
    list_filter = ['employment_type', 'status', 'is_public']
    search_fields = ['title', 'employer__company_name', 'tech_stack', 'region']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['vacancy', 'student', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['vacancy__title', 'student__full_name', 'student__user__email']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'level', 'is_read', 'created_at']
    list_filter = ['level', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']