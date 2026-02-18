from django.contrib import admin

# Register your models here.

from .models import Student, Achievement

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'course', 'data_processing_consent', 'created_at']
    list_filter = ['course', 'data_processing_consent']
    search_fields = ['full_name', 'course']
    readonly_fields = ['created_at', 'updated_at']

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