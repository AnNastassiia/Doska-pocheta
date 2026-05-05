from datetime import date
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Application, ContactRequest, Employer, Notification, Student, Vacancy


class SmokeWorkflowTests(TestCase):
	def setUp(self):
		self.manager_user = User.objects.create_user(username='manager@test.local', email='manager@test.local', password='pass12345')
		self.manager_user.is_staff = True
		self.manager_user.save(update_fields=['is_staff'])

		self.student_user = User.objects.create_user(username='student@test.local', email='student@test.local', password='pass12345')
		self.student = Student.objects.create(
			user=self.student_user,
			full_name='Иван Иванов',
			course='ПИ-41',
			is_approved=True,
			contact_email='student-contact@test.local',
			birth_date=date(2000, 1, 1),
		)

		self.employer_user = User.objects.create_user(username='employer@test.local', email='employer@test.local', password='pass12345')
		self.employer = Employer.objects.create(
			user=self.employer_user,
			company_name='Test Company',
			sector='it',
			contact_person='HR',
			is_approved=True,
		)

	def test_contact_request_requires_student_approval(self):
		self.client.login(username='employer@test.local', password='pass12345')
		response = self.client.post(reverse('request_contact', args=[self.student.id]), {'message': 'Хотим связаться'})
		self.assertEqual(response.status_code, 302)
		cr = ContactRequest.objects.get(employer=self.employer, student=self.student)
		self.assertEqual(cr.status, 'pending_student')

		self.client.logout()
		self.client.login(username='student@test.local', password='pass12345')
		response = self.client.post(reverse('approve_contact_request', args=[cr.id]), {'response_message': 'Ок'})
		self.assertEqual(response.status_code, 302)
		cr.refresh_from_db()
		self.assertEqual(cr.status, 'approved_by_student')

	def test_vacancy_apply_creates_application_and_notification(self):
		vacancy = Vacancy.objects.create(
			employer=self.employer,
			title='Python Intern',
			description='Internship',
			status='published',
			is_public=True,
		)
		self.client.login(username='student@test.local', password='pass12345')
		response = self.client.post(reverse('apply_to_vacancy', args=[vacancy.id]), {'message': 'Готов работать'})
		self.assertEqual(response.status_code, 302)
		self.assertTrue(Application.objects.filter(vacancy=vacancy, student=self.student).exists())
		self.assertTrue(Notification.objects.filter(user=self.employer_user, title='Новый отклик на вакансию').exists())

	def test_manager_can_unpublish_student(self):
		self.client.login(username='manager@test.local', password='pass12345')
		response = self.client.post(reverse('manager_unpublish_student', args=[self.student.id]))
		self.assertEqual(response.status_code, 302)
		self.student.refresh_from_db()
		self.assertFalse(self.student.is_approved)
