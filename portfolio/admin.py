from django.contrib import admin

# Register your models here.

from .models import Student, Achievement, Employer


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'course', 'student_card_number', 'is_approved', 'created_at']
    list_filter = ['course', 'is_approved', 'data_processing_consent']
    search_fields = ['full_name', 'course', 'student_card_number']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_students', 'reject_students']

    def approve_students(self, request, queryset):
        queryset.update(is_approved=True)
    approve_students.short_description = 'Одобрить выбранных студентов на доске почета'

    def reject_students(self, request, queryset):
        queryset.update(is_approved=False)
    reject_students.short_description = 'Отклонить выбранных студентов'


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