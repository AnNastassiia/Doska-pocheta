"""
Загрузка демонстрационных данных для локальной разработки и ручного тестирования.

Использование:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --clear
"""
from datetime import date, timedelta
from pathlib import Path
import shutil

from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from portfolio.models import (
    Achievement,
    Application,
    ContactRequest,
    Employer,
    Inquiry,
    ManagerProfile,
    Notification,
    Skill,
    Student,
    Vacancy,
)

DEMO_DOMAIN = 'demo.local'
DEFAULT_PASSWORD = 'Demo2026!'


class Command(BaseCommand):
    help = 'Создаёт демонстрационные данные для тестирования сайта'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить ранее созданные demo-аккаунты (@demo.local) перед загрузкой',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self._clear_demo_data()

        with transaction.atomic():
            data = self._create_all()

        self.stdout.write(self.style.SUCCESS('\n=== Демо-данные загружены ===\n'))
        self.stdout.write(f'Пароль для всех аккаунтов: {DEFAULT_PASSWORD}\n')
        self._print_accounts(data)

    def _clear_demo_data(self):
        demo_users = User.objects.filter(email__iendswith=f'@{DEMO_DOMAIN}')
        count = demo_users.count()
        demo_users.delete()
        self.stdout.write(self.style.WARNING(f'Удалено demo-пользователей: {count}'))

    def _create_user(self, email, *, is_staff=False, is_superuser=False):
        user, created = User.objects.get_or_create(
            username=email,
            defaults={'email': email, 'is_staff': is_staff, 'is_superuser': is_superuser},
        )
        if not created:
            user.email = email
            user.is_staff = is_staff
            user.is_superuser = is_superuser
        user.set_password(DEFAULT_PASSWORD)
        user.save()
        return user

    def _copy_photo(self, student, filename='photo_2026-04-26_21-51-50.jpg'):
        source = Path('media/students/photos') / filename
        if not source.exists():
            return
        dest_dir = Path('media/students/photos')
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_name = f'demo_{student.user_id}_{filename}'
        dest = dest_dir / dest_name
        shutil.copy2(source, dest)
        with dest.open('rb') as fh:
            student.photo.save(dest_name, File(fh), save=True)

    def _create_all(self):
        admin = self._create_user('admin@demo.local', is_staff=True, is_superuser=True)

        manager_user = self._create_user('manager@demo.local')
        manager, _ = ManagerProfile.objects.get_or_create(
            user=manager_user,
            defaults={'full_name': 'Петрова Анна Сергеевна', 'is_active': True},
        )

        skills = {}
        for name in ('Python', 'Django', 'JavaScript', 'React', 'PostgreSQL', 'Git', 'Docker'):
            skill, _ = Skill.objects.get_or_create(name=name, defaults={'is_approved': True})
            skills[name] = skill

        students = {}

        s1_user = self._create_user('student.approved@demo.local')
        students['approved'] = Student.objects.create(
            user=s1_user,
            full_name='Иванов Алексей Дмитриевич',
            student_card_number='ST-2024-001',
            specialty='09.02.07 Информационные системы и программирование',
            about_me='Разрабатываю веб-приложения на Django и React. Участвовал в хакатонах.',
            birth_date=date(2003, 5, 15),
            is_approved=True,
            data_processing_consent=True,
            job_search_status='internship',
            contact_email='student.approved@demo.local',
            phone='+7 (900) 111-22-33',
            telegram='@alex_ivanov',
            social_link='https://github.com/demo-alex',
            manager=manager,
        )
        students['approved'].skills.set([skills['Python'], skills['Django'], skills['PostgreSQL']])
        self._copy_photo(students['approved'])

        s2_user = self._create_user('student.pending@demo.local')
        students['pending'] = Student.objects.create(
            user=s2_user,
            full_name='Смирнова Екатерина Игоревна',
            specialty='09.02.07 Информационные системы и программирование',
            about_me='Профиль заполнен, ожидает модерации.',
            birth_date=date(2004, 8, 20),
            is_submitted_for_review=True,
            data_processing_consent=True,
            contact_email='student.pending@demo.local',
            phone='+7 (900) 222-33-44',
            manager=manager,
        )
        students['pending'].skills.set([skills['JavaScript'], skills['React']])

        s3_user = self._create_user('student.minor@demo.local')
        students['minor'] = Student.objects.create(
            user=s3_user,
            full_name='Козлов Максим Андреевич',
            specialty='09.02.07 Информационные системы и программирование',
            birth_date=date(2010, 3, 10),
            is_approved=True,
            data_processing_consent=True,
            parent_phone='+7 (900) 333-44-55',
            parent_email='parent.kozlov@demo.local',
            contact_email='student.minor@demo.local',
            manager=manager,
        )

        s4_user = self._create_user('student.private@demo.local')
        students['private'] = Student.objects.create(
            user=s4_user,
            full_name='Николаева Ольга Петровна',
            specialty='09.02.07 Информационные системы и программирование',
            birth_date=date(2002, 11, 1),
            is_approved=True,
            is_private=True,
            is_incognito=True,
            hide_contacts=True,
            data_processing_consent=True,
            contact_email='student.private@demo.local',
            manager=manager,
        )

        s5_user = self._create_user('student.rejected@demo.local')
        students['rejected'] = Student.objects.create(
            user=s5_user,
            full_name='Волков Денис Сергеевич',
            specialty='09.02.07 Информационные системы и программирование',
            birth_date=date(2003, 1, 25),
            rejection_reason='Недостаточно информации в профиле. Добавьте достижения и фото.',
            data_processing_consent=True,
            contact_email='student.rejected@demo.local',
            manager=manager,
        )

        for student_key, student in students.items():
            if student_key in ('approved', 'pending'):
                Achievement.objects.create(
                    student=student,
                    title='Веб-приложение «Доска почёта»',
                    description='Дипломный проект — платформа для студенческих портфолио.',
                    link='https://github.com/demo/honor-board',
                    achievement_type='project',
                    is_approved=student.is_approved,
                    is_public=student.is_approved,
                )
                Achievement.objects.create(
                    student=student,
                    title='Хакатон «CodeFest 2025»',
                    description='2 место в номинации «Лучший backend».',
                    achievement_type='competition',
                    is_approved=student.is_approved,
                    is_public=student.is_approved,
                )

        emp1_user = self._create_user('employer.approved@demo.local')
        employer_approved = Employer.objects.create(
            user=emp1_user,
            company_name='ООО «ТехноСофт»',
            sector='IT / Разработка ПО',
            website='https://technosoft.demo.local',
            contact_person='Сидорова Мария',
            phone='+7 (495) 100-20-30',
            registration_purpose='Поиск стажёров и junior-разработчиков',
            is_approved=True,
        )

        emp2_user = self._create_user('employer.pending@demo.local')
        employer_pending = Employer.objects.create(
            user=emp2_user,
            company_name='ООО «СтартАп Лаб»',
            sector='Стартапы',
            contact_person='Кузнецов Игорь',
            phone='+7 (495) 200-30-40',
            registration_purpose='Регистрация для размещения вакансий',
            is_approved=False,
        )

        vacancy_published = Vacancy.objects.create(
            employer=employer_approved,
            title='Python-стажёр (Django)',
            description='Ищем стажёра для разработки внутренних сервисов на Django.',
            requirements='Python, основы Django, Git',
            region='Москва',
            employment_type='internship',
            status='published',
            is_public=True,
            target_specialties='09.02.07 Информационные системы и программирование',
            send_notifications=True,
        )
        vacancy_draft = Vacancy.objects.create(
            employer=employer_approved,
            title='Frontend-разработчик (React)',
            description='Черновик вакансии — ещё не опубликована.',
            requirements='JavaScript, React',
            region='Москва',
            employment_type='part_time',
            status='draft',
        )
        vacancy_closed = Vacancy.objects.create(
            employer=employer_approved,
            title='Системный администратор',
            description='Вакансия закрыта.',
            region='Москва',
            employment_type='full_time',
            status='closed',
        )

        Application.objects.create(
            vacancy=vacancy_published,
            student=students['approved'],
            message='Хочу пройти стажировку в вашей компании.',
            status='reviewing',
        )
        Application.objects.create(
            vacancy=vacancy_closed,
            student=students['approved'],
            message='Отклик на закрытую вакансию.',
            status='rejected',
            employer_message='Вакансия закрыта.',
        )

        ContactRequest.objects.create(
            employer=employer_approved,
            student=students['approved'],
            manager=manager,
            status='approved_by_manager',
            employer_message='Интересует кандидат для стажировки.',
            manager_response_message='Контакты переданы.',
            manager_responded_at=timezone.now() - timedelta(days=2),
        )
        ContactRequest.objects.create(
            employer=employer_approved,
            student=students['minor'],
            manager=manager,
            status='pending_manager',
            employer_message='Хотим связаться с кандидатом.',
        )

        Inquiry.objects.create(
            employer=employer_approved,
            student=students['approved'],
            vacancy=vacancy_published,
            message='Приглашаем на собеседование по вакансии Python-стажёр.',
            status='pending',
        )
        Inquiry.objects.create(
            employer=employer_approved,
            student=students['private'],
            message='Приглашение для приватного профиля.',
            status='rejected',
            response_message='Не заинтересован(а) в данный момент.',
        )

        Notification.objects.create(
            user=students['approved'].user,
            title='Новая вакансия',
            message='Опубликована вакансия «Python-стажёр (Django)»',
            url='/vacancies/',
            level='info',
        )
        Notification.objects.create(
            user=manager_user,
            title='Новый запрос контактов',
            message='Работодатель запросил контакты студента Козлов М.А.',
            url='/manager/contact-requests/',
            level='warning',
            is_read=False,
        )
        Notification.objects.create(
            user=emp1_user,
            title='Новый отклик на вакансию',
            message='Студент Иванов А.Д. откликнулся на вакансию.',
            url='/applications/employer/',
            level='success',
        )

        return {
            'admin': admin,
            'manager': manager,
            'students': students,
            'employers': {'approved': employer_approved, 'pending': employer_pending},
            'vacancies': {
                'published': vacancy_published,
                'draft': vacancy_draft,
                'closed': vacancy_closed,
            },
        }

    def _print_accounts(self, data):
        rows = [
            ('Администратор (Django admin + менеджер)', 'admin@demo.local'),
            ('Менеджер', 'manager@demo.local'),
            ('Студент — одобрен, на доске почёта', 'student.approved@demo.local'),
            ('Студент — на модерации', 'student.pending@demo.local'),
            ('Студент — несовершеннолетний', 'student.minor@demo.local'),
            ('Студент — приватный/инкогнито', 'student.private@demo.local'),
            ('Студент — отклонён', 'student.rejected@demo.local'),
            ('Работодатель — одобрен', 'employer.approved@demo.local'),
            ('Работодатель — ожидает одобрения', 'employer.pending@demo.local'),
        ]
        for role, email in rows:
            self.stdout.write(f'  {role}: {email}')

        self.stdout.write('\nПолезные URL:')
        self.stdout.write('  Главная (доска почёта): /')
        self.stdout.write('  Вакансии: /vacancies/')
        self.stdout.write('  Вход: /login/')
        self.stdout.write('  Панель менеджера: /manager/dashboard/')
        self.stdout.write('  Django admin: /admin/')
