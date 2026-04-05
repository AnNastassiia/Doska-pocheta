from django.db import models

# Create your models here.
from django.contrib.auth.models import User


class Skill(models.Model):
    """
    Навык/технология для справочника
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Название навыка")
    is_approved = models.BooleanField(default=True, verbose_name="Одобрен администратором")

    def __str__(self):
        return self.name


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
    student_card_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Номер студенческого билета"
    )
    course = models.CharField(
        max_length=100,
        verbose_name="Группа / Специальность"
    )
    social_link = models.URLField(
        blank=True,
        verbose_name="Ссылка на соцсеть"
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name="Профиль одобрен администратором"
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
    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Причина отказа администратора"
    )
    skills = models.ManyToManyField(
        Skill,
        blank=True,
        related_name='students',
        verbose_name="Навыки"
    )
    hide_contacts = models.BooleanField(
        default=False,
        verbose_name="Скрыть контакты"
    )
    is_private = models.BooleanField(
        default=False,
        verbose_name="Сделать профиль приватным"
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
    admin_comment = models.TextField(
        blank=True,
        verbose_name="Комментарий администратора"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.full_name}: {self.title}"
    
    class Meta:
        verbose_name = "Достижение"
        verbose_name_plural = "Достижения"
        ordering = ['-date_achieved']  # новые сверху


class ContactRequest(models.Model):
    employer = models.ForeignKey(
        'Employer', on_delete=models.CASCADE, related_name='contact_requests', verbose_name='Работодатель'
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='contact_requests', verbose_name='Студент'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата запроса')
    is_handled = models.BooleanField(default=False, verbose_name='Обработано')

    class Meta:
        verbose_name = 'Запрос контактов'
        verbose_name_plural = 'Запросы контактов'
        ordering = ['-created_at']


class EnrollmentOrder(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='enrollment_orders', verbose_name='Студент'
    )
    file = models.FileField(upload_to='orders/', verbose_name='Файл приказа (PDF)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')
    assigned_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Поставил статус'
    )

    class Meta:
        verbose_name = 'Приказ зачисления'
        verbose_name_plural = 'Приказы зачисления'
        ordering = ['-created_at']


class Employer(models.Model):
    """Модель для работодателей"""
    EMPLOYMENT_SECTORS = [
        ('it', 'IT'),
        ('design', 'Дизайн'),
        ('marketing', 'Маркетинг'),
        ('other', 'Другое'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    company_name = models.CharField(
        max_length=255,
        verbose_name="Название организации"
    )
    sector = models.CharField(
        max_length=50,
        choices=EMPLOYMENT_SECTORS,
        verbose_name="Сфера деятельности"
    )
    website = models.URLField(
        blank=True,
        verbose_name="Сайт компании"
    )
    contact_person = models.CharField(
        max_length=200,
        verbose_name="Контактное лицо"
    )
    registration_purpose = models.TextField(
        blank=True,
        verbose_name="Цель регистрации"
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name="Аккаунт одобрен администратором"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} ({self.contact_person})"

    class Meta:
        verbose_name = "Работодатель"
        verbose_name_plural = "Работодатели"
        ordering = ['company_name']        