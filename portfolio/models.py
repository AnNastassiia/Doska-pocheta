from django.db import models

# Create your models here.
from django.contrib.auth.models import User

class Student(models.Model):
    """
    Модель для хранения информации о студентах
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    
    full_name = models.CharField(
        max_length=200,
        verbose_name="ФИО"
    )
    
    course = models.CharField(
        max_length=100,
        verbose_name="Курс/Направление"
    )
    
    photo = models.ImageField(
        upload_to='students/photos/',
        blank=True,
        null=True,
        verbose_name="Фотография"
    )
    
    # ВАЖНО для несовершеннолетних!
    data_processing_consent = models.BooleanField(
        default=False,
        verbose_name="Согласие на обработку данных"
    )
    
    contact_email = models.EmailField(
        blank=True,
        verbose_name="Контактный email"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    def __str__(self):
        return f"{self.full_name} ({self.course})"
    
    class Meta:
        verbose_name = "Студент"
        verbose_name_plural = "Студенты"
        ordering = ['full_name']




class Achievement(models.Model):
    """
    Модель для достижений студентов (проекты, грамоты и т.д.)
    """
    # Связь с студентом: один студент → много достижений
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE,  # если удалить студента - удалятся его достижения
        related_name='achievements',  # как обращаться из студента: student.achievements.all()
        verbose_name="Студент"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="Название достижения"
    )
    
    description = models.TextField(
        verbose_name="Подробное описание"
    )
    
    # Тип достижения (проект, грамота, практика и т.д.)
    ACHIEVEMENT_TYPES = [
        ('project', 'Учебный проект'),
        ('competition', 'Олимпиада/Конкурс'),
        ('practice', 'Практика/Стажировка'),
        ('certificate', 'Сертификат'),
        ('other', 'Другое'),
    ]
    
    achievement_type = models.CharField(
        max_length=20,
        choices=ACHIEVEMENT_TYPES,
        default='other',
        verbose_name="Тип достижения"
    )
    
    # Файлы (сканы грамот, проекты и т.д.)
    document = models.FileField(
        upload_to='achievements/documents/',
        blank=True,
        null=True,
        verbose_name="Документ (грамота, сертификат)"
    )
    
    project_file = models.FileField(
        upload_to='achievements/projects/',
        blank=True,
        null=True,
        verbose_name="Файл проекта"
    )
    
    date_achieved = models.DateField(
        verbose_name="Дата получения"
    )
    
    # Одобрено ли администратором для публикации
    is_approved = models.BooleanField(
        default=False,
        verbose_name="Одобрено для публикации"
    )
    
    # Показывать ли на публичной доске почета
    is_public = models.BooleanField(
        default=False,
        verbose_name="Показывать на доске почета"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.full_name}: {self.title}"
    
    class Meta:
        verbose_name = "Достижение"
        verbose_name_plural = "Достижения"
        ordering = ['-date_achieved']  # новые сверху        