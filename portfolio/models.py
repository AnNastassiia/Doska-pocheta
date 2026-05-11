from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.utils import timezone


class ManagerProfile(models.Model):
    """
    Операционный менеджер: работает со студентами, работодателями и модерацией.
    Это отдельная роль от технического администратора Django.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='manager_profile',
        verbose_name="Пользователь",
    )
    full_name = models.CharField(
        max_length=200,
        verbose_name="ФИО менеджера"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Менеджер"
        verbose_name_plural = "Менеджеры"
        ordering = ['full_name']


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
    about_me = models.TextField(
        blank=True,
        verbose_name="О себе"
    )
    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Дата рождения"
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name="Профиль одобрен администратором"
    )
    is_submitted_for_review = models.BooleanField(
        default=False,
        verbose_name="Отправлен на модерацию"
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
    JOB_SEARCH_STATUS_CHOICES = [
        ('internship', 'Ищу стажировку'),
        ('job', 'В поиске работы'),
        ('found', 'Уже нашел работу'),
    ]
    job_search_status = models.CharField(
        max_length=20,
        choices=JOB_SEARCH_STATUS_CHOICES,
        default='internship',
        verbose_name='Статус поиска работы'
    )
    contact_email = models.EmailField(
        blank=True,
        verbose_name="Контактный email"
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Телефон"
    )
    telegram = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Telegram"
    )
    whatsapp = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="WhatsApp"
    )
    preferred_contact_note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Предпочтительный способ связи"
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
    is_incognito = models.BooleanField(
        default=False,
        verbose_name="Режим инкогнито (скрыть личность)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    @property
    def is_adult(self):
        """
        True, если студенту уже исполнилось 18 лет.
        """
        if not self.birth_date:
            return False
        today = timezone.localdate()
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years >= 18

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
        blank=True,
        verbose_name="Описание (необязательно)"
    )

    link = models.URLField(
        max_length=500,
        blank=True,
        default='',
        verbose_name="Ссылка (GitHub / PDF / сайт проекта)"
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
    
    date_achieved = models.DateField(
        blank=True,
        null=True,
        verbose_name="Дата добавления"
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

    def save(self, *args, **kwargs):
        if not self.date_achieved:
            self.date_achieved = timezone.localdate()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.full_name}: {self.title}"
    
    class Meta:
        verbose_name = "Достижение"
        verbose_name_plural = "Достижения"
        ordering = ['-date_achieved']  # новые сверху


class ContactRequest(models.Model):
    STATUS_CHOICES = [
        ('pending_student', 'Ожидает решения студента'),
        ('approved_by_student', 'Одобрен студентом'),
        ('rejected_by_student', 'Отклонен студентом'),
        ('expired', 'Истек'),
    ]

    employer = models.ForeignKey(
        'Employer', on_delete=models.CASCADE, related_name='contact_requests', verbose_name='Работодатель'
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='contact_requests', verbose_name='Студент'
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending_student',
        verbose_name='Статус'
    )
    employer_message = models.TextField(blank=True, verbose_name='Комментарий работодателя')
    student_response_message = models.TextField(blank=True, verbose_name='Ответ студента')
    requested_at = models.DateTimeField(default=timezone.now, verbose_name='Дата запроса')
    responded_at = models.DateTimeField(blank=True, null=True, verbose_name='Дата ответа студента')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Запрос контактов'
        verbose_name_plural = 'Запросы контактов'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['employer', 'student'], name='unique_contact_request_per_pair')
        ]


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


class Notification(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Информация'),
        ('success', 'Успех'),
        ('warning', 'Предупреждение'),
        ('danger', 'Важно'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Пользователь',
    )
    title = models.CharField(max_length=200, blank=True, default='', verbose_name='Заголовок')
    message = models.TextField(verbose_name='Сообщение')
    url = models.CharField(max_length=500, blank=True, default='', verbose_name='Ссылка')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='info', verbose_name='Уровень')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    is_seen = models.BooleanField(default=False, verbose_name='Показано во всплывающем уведомлении')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user_id}: {self.title or self.level}'


class Vacancy(models.Model):
    EMPLOYMENT_TYPES = [
        ('internship', 'Стажировка'),
        ('part_time', 'Частичная занятость'),
        ('full_time', 'Полная занятость'),
        ('project', 'Проектная работа'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликована'),
        ('closed', 'Закрыта'),
    ]

    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE,
        related_name='vacancies',
        verbose_name='Работодатель'
    )
    title = models.CharField(max_length=200, verbose_name='Название вакансии')
    description = models.TextField(verbose_name='Описание')
    requirements = models.TextField(blank=True, verbose_name='Требования')
    region = models.CharField(max_length=150, blank=True, verbose_name='Регион')
    tech_stack = models.CharField(max_length=255, blank=True, verbose_name='Стек технологий')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='internship', verbose_name='Формат')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    is_public = models.BooleanField(default=True, verbose_name='Публичная')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.employer.company_name})'


class Application(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Отправлен'),
        ('reviewing', 'На рассмотрении'),
        ('accepted', 'Принят'),
        ('rejected', 'Отклонен'),
    ]

    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Вакансия'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Студент'
    )
    message = models.TextField(blank=True, verbose_name='Сопроводительное сообщение')
    employer_message = models.TextField(blank=True, verbose_name='Сообщение работодателя')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Отклик'
        verbose_name_plural = 'Отклики'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['vacancy', 'student'], name='unique_student_application_per_vacancy')
        ]

    def __str__(self):
        return f'{self.student.full_name} -> {self.vacancy.title}'


class Inquiry(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает ответа'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
    ]

    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE,
        related_name='inquiries',
        verbose_name='Работодатель'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='inquiries',
        verbose_name='Студент'
    )
    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='inquiries',
        verbose_name='Вакансия'
    )
    message = models.TextField(verbose_name='Сообщение работодателя')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    response_message = models.TextField(blank=True, verbose_name='Сообщение студента')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Приглашение студента'
        verbose_name_plural = 'Приглашения студентов'
        ordering = ['-created_at']

    def __str__(self):
        return f'Запрос от {self.employer.company_name} к {self.student.full_name} ({self.get_status_display()})'