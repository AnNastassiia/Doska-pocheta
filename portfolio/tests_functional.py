from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (
    Achievement,
    Application,
    ContactRequest,
    Employer,
    Inquiry,
    ManagerProfile,
    Notification,
    Student,
    Vacancy,
)


class PublicPagesTests(TestCase):
    def test_index_page_loads(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_vacancies_list_loads(self):
        response = self.client.get(reverse('vacancies_list'))
        self.assertEqual(response.status_code, 200)

    def test_help_and_about_load(self):
        self.assertEqual(self.client.get(reverse('help_guide')).status_code, 200)
        self.assertEqual(self.client.get(reverse('about_organization')).status_code, 200)

    def test_login_page_loads(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)


class RoleAccessTests(TestCase):
    def setUp(self):
        self.manager_user = User.objects.create_user(
            username='manager@test.local', email='manager@test.local', password='pass12345',
        )
        ManagerProfile.objects.create(
            user=self.manager_user, full_name='Тест Менеджер', is_active=True,
        )

        self.student_user = User.objects.create_user(
            username='student@test.local', email='student@test.local', password='pass12345',
        )
        self.student = Student.objects.create(
            user=self.student_user,
            full_name='Студент Тест',
            is_approved=True,
            birth_date=date(2000, 1, 1),
            specialty='09.02.07 Информационные системы и программирование',
        )

        self.employer_user = User.objects.create_user(
            username='employer@test.local', email='employer@test.local', password='pass12345',
        )
        self.employer = Employer.objects.create(
            user=self.employer_user,
            company_name='Test Co',
            sector='IT',
            contact_person='HR',
            phone='+7 900 000-00-00',
            is_approved=True,
        )

    def test_student_dashboard_access(self):
        self.client.login(username='student@test.local', password='pass12345')
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)
        self.assertEqual(self.client.get(reverse('student_applications')).status_code, 200)

    def test_employer_dashboard_access(self):
        self.client.login(username='employer@test.local', password='pass12345')
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)
        self.assertEqual(self.client.get(reverse('employer_vacancies')).status_code, 200)

    def test_manager_dashboard_access(self):
        self.client.login(username='manager@test.local', password='pass12345')
        self.assertEqual(self.client.get(reverse('manager_dashboard')).status_code, 200)
        self.assertEqual(self.client.get(reverse('manager_students_pending')).status_code, 200)
        self.assertEqual(self.client.get(reverse('manager_contact_requests')).status_code, 200)

    def test_unapproved_employer_can_open_vacancy_form(self):
        self.employer.is_approved = False
        self.employer.save(update_fields=['is_approved'])
        self.client.login(username='employer@test.local', password='pass12345')
        response = self.client.get(reverse('vacancy_create'))
        self.assertEqual(response.status_code, 200)


class ModerationWorkflowTests(TestCase):
    def setUp(self):
        self.manager_user = User.objects.create_user(
            username='mod-manager@test.local', email='mod-manager@test.local', password='pass12345',
        )
        self.manager_user.is_staff = True
        self.manager_user.save(update_fields=['is_staff'])

        self.student_user = User.objects.create_user(
            username='mod-student@test.local', email='mod-student@test.local', password='pass12345',
        )
        self.student = Student.objects.create(
            user=self.student_user,
            full_name='На модерации',
            is_submitted_for_review=True,
            birth_date=date(2001, 6, 1),
        )

        self.employer_user = User.objects.create_user(
            username='mod-employer@test.local', email='mod-employer@test.local', password='pass12345',
        )
        self.employer = Employer.objects.create(
            user=self.employer_user,
            company_name='Pending LLC',
            sector='IT',
            contact_person='Boss',
            phone='+7 900 111-11-11',
            is_approved=False,
        )

    def test_manager_approves_student(self):
        self.client.login(username='mod-manager@test.local', password='pass12345')
        response = self.client.post(reverse('manager_approve_student', args=[self.student.id]))
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertTrue(self.student.is_approved)

    def test_manager_rejects_student(self):
        self.client.login(username='mod-manager@test.local', password='pass12345')
        response = self.client.post(
            reverse('manager_reject_student', args=[self.student.id]),
            {'reason': 'Недостаточно данных'},
        )
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_approved)
        self.assertIn('Недостаточно', self.student.rejection_reason)

    def test_manager_approves_employer(self):
        self.client.login(username='mod-manager@test.local', password='pass12345')
        response = self.client.post(reverse('manager_approve_employer', args=[self.employer.id]))
        self.assertEqual(response.status_code, 302)
        self.employer.refresh_from_db()
        self.assertTrue(self.employer.is_approved)


class VacancyAndInquiryTests(TestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            username='inq-student@test.local', email='inq-student@test.local', password='pass12345',
        )
        self.student = Student.objects.create(
            user=self.student_user,
            full_name='Взрослый Студент',
            is_approved=True,
            birth_date=date(2000, 1, 1),
        )

        self.employer_user = User.objects.create_user(
            username='inq-employer@test.local', email='inq-employer@test.local', password='pass12345',
        )
        self.employer = Employer.objects.create(
            user=self.employer_user,
            company_name='Inquiry Co',
            sector='IT',
            contact_person='HR',
            phone='+7 900 222-22-22',
            is_approved=True,
        )

        self.vacancy = Vacancy.objects.create(
            employer=self.employer,
            title='Backend Dev',
            description='Test vacancy',
            status='published',
            is_public=True,
        )

    def test_employer_creates_and_publishes_vacancy(self):
        self.client.login(username='inq-employer@test.local', password='pass12345')
        response = self.client.post(reverse('vacancy_create'), {
            'title': 'New Vacancy',
            'description': 'Description',
            'requirements': 'Python',
            'region': 'Москва',
            'employment_type': 'internship',
            'status': 'published',
            'is_public': True,
            'target_specialties': '',
            'send_notifications': False,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Vacancy.objects.filter(title='New Vacancy').exists())

    def test_employer_invites_adult_student(self):
        self.client.login(username='inq-employer@test.local', password='pass12345')
        response = self.client.post(
            reverse('create_inquiry', args=[self.student.id]),
            {'message': 'Приглашаем на собеседование', 'vacancy': self.vacancy.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Inquiry.objects.filter(employer=self.employer, student=self.student).exists())

    def test_student_accepts_inquiry(self):
        inquiry = Inquiry.objects.create(
            employer=self.employer,
            student=self.student,
            vacancy=self.vacancy,
            message='Приглашение',
            status='pending',
        )
        self.client.login(username='inq-student@test.local', password='pass12345')
        response = self.client.post(
            reverse('update_inquiry_status', args=[inquiry.id]),
            {'action': 'accept', 'response_message': 'Согласен'},
        )
        self.assertEqual(response.status_code, 302)
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, 'accepted')

    def test_employer_updates_application_status(self):
        application = Application.objects.create(
            vacancy=self.vacancy,
            student=self.student,
            message='Отклик',
            status='submitted',
        )
        self.client.login(username='inq-employer@test.local', password='pass12345')
        response = self.client.post(
            reverse('update_application_status', args=[application.id]),
            {'action': 'accept', 'message': 'Добро пожаловать'},
        )
        self.assertEqual(response.status_code, 302)
        application.refresh_from_db()
        self.assertEqual(application.status, 'accepted')


class StudentProfileTests(TestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            username='proj-student@test.local', email='proj-student@test.local', password='pass12345',
        )
        self.student = Student.objects.create(
            user=self.student_user,
            full_name='Проектный Студент',
            is_approved=True,
            birth_date=date(2000, 1, 1),
        )

    def test_student_adds_achievement(self):
        self.client.login(username='proj-student@test.local', password='pass12345')
        response = self.client.post(reverse('add_project'), {
            'title': 'Мой проект',
            'description': 'Описание',
            'link': 'https://github.com/test',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Achievement.objects.filter(student=self.student, title='Мой проект').exists())

    def test_public_profile_visible_for_approved_student(self):
        response = self.client.get(reverse('student_profile', args=[self.student.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Проектный Студент')

    def test_notifications_mark_read(self):
        notification = Notification.objects.create(
            user=self.student_user,
            title='Тест',
            message='Тестовое уведомление',
            level='info',
        )
        self.client.login(username='proj-student@test.local', password='pass12345')
        response = self.client.post(reverse('notification_mark_read', args=[notification.id]))
        self.assertEqual(response.status_code, 302)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
