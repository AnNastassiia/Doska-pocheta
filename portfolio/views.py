from django import forms
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from functools import wraps
from .models import (
	Student,
	Skill,
	Achievement,
	Employer,
	ContactRequest,
	ManagerProfile,
	Notification,
	Vacancy,
	Application,
)
from django.contrib.auth.models import User

MAX_PROFILE_PHOTO_SIZE_MB = 5
ALLOWED_IMAGE_CONTENT_TYPES = {
	'image/jpeg',
	'image/png',
	'image/webp',
	'image/gif',
}
MAX_ABOUT_ME_LENGTH = 1000


def send_admin_notification(subject, message):
	"""
	Отправляет служебное уведомление администратору, если адрес настроен.
	Ошибки отправки не должны ломать основной пользовательский сценарий.
	"""
	recipient = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', '') or getattr(settings, 'DEFAULT_FROM_EMAIL', '')
	if not recipient:
		return False

	try:
		send_mail(
			subject=subject,
			message=message,
			from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
			recipient_list=[recipient],
			fail_silently=False,
		)
		return True
	except Exception:
		return False


def create_notification(user, title, message, url='', level='info', send_email=False, email_subject=None, email_message=None):
	Notification.objects.create(
		user=user,
		title=title or '',
		message=message,
		url=url or '',
		level=level or 'info',
	)
	if send_email:
		to_email = (user.email or '').strip()
		if to_email:
			try:
				send_mail(
					subject=email_subject or (title or 'Уведомление'),
					message=email_message or message,
					from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
					recipient_list=[to_email],
					fail_silently=True,
				)
			except Exception:
				pass


def get_manager_users():
	# активные менеджеры + staff
	qs = User.objects.filter(is_active=True).filter(
		Q(is_staff=True) | Q(is_superuser=True) | Q(manager_profile__is_active=True)
	).distinct()
	return list(qs)


def has_employer_contact_access(employer, student):
	return ContactRequest.objects.filter(
		employer=employer,
		student=student,
		status='approved_by_student',
	).exists()


def is_manager_user(user):
	return bool(
		user.is_authenticated and (
			user.is_staff or user.is_superuser or (
				hasattr(user, 'manager_profile') and user.manager_profile.is_active
			)
		)
	)


def manager_required(view_func):
	@wraps(view_func)
	def _wrapped_view(request, *args, **kwargs):
		if not request.user.is_authenticated:
			return redirect(f"{settings.LOGIN_URL}?next={request.path}")
		if not is_manager_user(request.user):
			return HttpResponseForbidden('Доступ разрешен только менеджеру или администратору.')
		return view_func(request, *args, **kwargs)
	return _wrapped_view


def admin_required(view_func):
	@wraps(view_func)
	def _wrapped_view(request, *args, **kwargs):
		if not request.user.is_authenticated:
			return redirect(f"{settings.LOGIN_URL}?next={request.path}")
		if not (request.user.is_staff or request.user.is_superuser):
			return HttpResponseForbidden('Доступ разрешен только техническому администратору.')
		return view_func(request, *args, **kwargs)
	return _wrapped_view


class ExtendedUserCreationForm(UserCreationForm):
	error_messages = {
		'password_mismatch': 'Пароли не совпадают.',
	}
	username = forms.CharField(required=False, widget=forms.HiddenInput())
	email = forms.EmailField(required=True, label='Электронная почта')
	password1 = forms.CharField(
		label='Пароль',
		strip=False,
		help_text='Пароль должен содержать не менее 8 символов.',
		widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
	)
	password2 = forms.CharField(
		label='Подтвердите пароль',
		strip=False,
		help_text='Введите тот же пароль ещё раз для подтверждения.',
		widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
	)
	user_type = forms.ChoiceField(
		choices=[('student', 'Студент колледжа'), ('employer', 'Работодатель')],
		widget=forms.RadioSelect,
		label='Тип аккаунта'
	)

	class Meta(UserCreationForm.Meta):
		model = User
		fields = ('username', 'email', 'password1', 'password2')

	def clean_email(self):
		email = self.cleaned_data.get('email')
		if User.objects.filter(email__iexact=email).exists():
			raise forms.ValidationError('Пользователь с таким email уже существует.')
		return email

	def save(self, commit=True):
		user = super().save(commit=False)
		user.email = self.cleaned_data['email']
		user.username = self.cleaned_data['email']
		if commit:
			user.save()
		return user


class CustomAuthenticationForm(AuthenticationForm):
	username = forms.EmailField(label='Электронная почта', widget=forms.EmailInput(attrs={'autofocus': True}))
	password = forms.CharField(label='Пароль', strip=False, widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))

	error_messages = {
		'invalid_login': 'Пожалуйста, введите правильные электронную почту и пароль.',
		'inactive': 'Этот аккаунт не активен.',
	}

	def clean_username(self):
		# Берем значение как email
		email = self.cleaned_data.get('username')
		if email:
			# Преобразуем его в username (для Django это одно и то же в нашей системе)
			self.cleaned_data['username'] = email.lower().strip()
		return self.cleaned_data['username']


class StudentRegistrationForm(forms.ModelForm):
	class Meta:
		model = Student
		fields = ['full_name', 'course', 'student_card_number', 'social_link', 'contact_email', 'data_processing_consent']


class EmployerRegistrationForm(forms.ModelForm):
	class Meta:
		model = Employer
		fields = ['company_name', 'sector', 'website', 'contact_person', 'registration_purpose']


class StudentProfileForm(forms.ModelForm):
	class Meta:
		model = Student
		fields = ['about_me', 'social_link', 'photo', 'contact_email', 'phone', 'telegram', 'whatsapp', 'preferred_contact_note']
		widgets = {
			'photo': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
			'about_me': forms.Textarea(attrs={
				'rows': 5,
				'placeholder': 'Расскажите о себе, своих интересах и целях...',
				'maxlength': MAX_ABOUT_ME_LENGTH,
			}),
		}
		help_texts = {
			'about_me': f'До {MAX_ABOUT_ME_LENGTH} символов.',
		}

	def clean_about_me(self):
		about_me = (self.cleaned_data.get('about_me') or '').strip()
		if len(about_me) > MAX_ABOUT_ME_LENGTH:
			raise ValidationError(f'Раздел "О себе" не должен превышать {MAX_ABOUT_ME_LENGTH} символов.')
		return about_me

	def clean_photo(self):
		photo = self.cleaned_data.get('photo')
		if not photo:
			return photo

		if getattr(photo, 'content_type', None) not in ALLOWED_IMAGE_CONTENT_TYPES:
			raise ValidationError('Можно загружать только изображения (JPG, PNG, WEBP, GIF).')

		max_size_bytes = MAX_PROFILE_PHOTO_SIZE_MB * 1024 * 1024
		if photo.size > max_size_bytes:
			raise ValidationError(f'Размер фото не должен превышать {MAX_PROFILE_PHOTO_SIZE_MB} МБ.')

		return photo


class EmployerProfileForm(forms.ModelForm):
	class Meta:
		model = Employer
		fields = ['company_name', 'sector', 'website', 'contact_person', 'registration_purpose']


class SkillForm(forms.Form):
	skills = forms.ModelMultipleChoiceField(
		queryset=Skill.objects.filter(is_approved=True),
		widget=forms.CheckboxSelectMultiple,
		required=False,
		label='Выберите навыки'
	)
	custom_skills = forms.CharField(
		required=False,
		label='Добавить свои навыки',
		help_text='Укажите через запятую, например: Python, Docker, Figma'
	)


class ProjectForm(forms.ModelForm):
	class Meta:
		model = Achievement
		fields = ['title', 'link', 'description']
		widgets = {
			'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Дополнительное описание (необязательно)'}),
			'link': forms.URLInput(attrs={'placeholder': 'https://github.com/... или ссылка на PDF'}),
		}


class VacancyForm(forms.ModelForm):
	class Meta:
		model = Vacancy
		fields = ['title', 'description', 'requirements', 'region', 'tech_stack', 'employment_type', 'status', 'is_public']
		widgets = {
			'description': forms.Textarea(attrs={'rows': 5}),
			'requirements': forms.Textarea(attrs={'rows': 4}),
		}


class ApplicationForm(forms.ModelForm):
	class Meta:
		model = Application
		fields = ['message']
		widgets = {
			'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Коротко расскажите, почему вам интересна вакансия'}),
		}


class ContactRequestMessageForm(forms.Form):
	message = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}), label='Комментарий к запросу')


class ContactRequestDecisionForm(forms.Form):
	response_message = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}), label='Комментарий студентa')


class PrivacyForm(forms.ModelForm):
	class Meta:
		model = Student
		fields = ['hide_contacts', 'is_private']


class StudentDashboardForm(StudentProfileForm):
	skills = forms.ModelMultipleChoiceField(
		queryset=Skill.objects.filter(is_approved=True),
		widget=forms.CheckboxSelectMultiple,
		required=False,
		label='Навыки'
	)
	custom_skills = forms.CharField(
		required=False,
		label='Дополнительные навыки',
		help_text='Можно указать через запятую: Python, Docker, Figma'
	)
	hide_contacts = forms.BooleanField(
		required=False,
		label='Скрыть контактные данные для пользователей'
	)
	is_private = forms.BooleanField(
		required=False,
		label='Сделать профиль приватным'
	)
	is_incognito = forms.BooleanField(
		required=False,
		label='Режим «Инкогнито» (скрыть ФИО/группу/фото на публичной странице)'
	)

	class Meta(StudentProfileForm.Meta):
		fields = StudentProfileForm.Meta.fields + ['hide_contacts', 'is_private', 'is_incognito']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		student = self.instance
		if student and student.pk:
			self.fields['skills'].initial = student.skills.all()
			self.fields['hide_contacts'].initial = student.hide_contacts
			self.fields['is_private'].initial = student.is_private
			self.fields['is_incognito'].initial = getattr(student, 'is_incognito', False)

	def save(self, commit=True):
		student = super().save(commit=False)
		student.hide_contacts = self.cleaned_data.get('hide_contacts', False)
		student.is_private = self.cleaned_data.get('is_private', False)
		student.is_incognito = self.cleaned_data.get('is_incognito', False)
		student.is_approved = False
		student.is_submitted_for_review = False

		if commit:
			student.save()

			selected_skills = list(self.cleaned_data.get('skills') or [])
			custom_skills_raw = self.cleaned_data.get('custom_skills', '')
			if custom_skills_raw:
				for raw_name in custom_skills_raw.replace('\n', ',').split(','):
					name = raw_name.strip()
					if not name:
						continue
					skill = Skill.objects.filter(name__iexact=name).first()
					if not skill:
						skill = Skill.objects.create(name=name, is_approved=True)
					selected_skills.append(skill)

			unique_skill_ids = []
			seen_ids = set()
			for skill in selected_skills:
				if skill.id not in seen_ids:
					seen_ids.add(skill.id)
					unique_skill_ids.append(skill.id)
			student.skills.set(unique_skill_ids)

		return student


class AdminCreateStudentForm(forms.Form):
	email = forms.EmailField(required=True, label='Электронная почта')
	full_name = forms.CharField(required=True, label='ФИО', max_length=200)
	course = forms.CharField(required=True, label='Группа / Специальность', max_length=100)
	birth_date = forms.DateField(required=True, label='Дата рождения', widget=forms.DateInput(attrs={'type': 'date'}))

	def clean_email(self):
		email = (self.cleaned_data.get('email') or '').lower().strip()
		if not email:
			return email
		if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
			raise forms.ValidationError('Пользователь с таким email уже существует.')
		return email


class CreateManagerForm(UserCreationForm):
	email = forms.EmailField(required=True, label='Электронная почта')
	full_name = forms.CharField(required=True, label='ФИО менеджера', max_length=200)
	is_active = forms.BooleanField(required=False, initial=True, label='Активный менеджер')

	class Meta(UserCreationForm.Meta):
		model = User
		fields = ('email', 'full_name', 'password1', 'password2')

	def clean_email(self):
		email = (self.cleaned_data.get('email') or '').lower().strip()
		if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
			raise forms.ValidationError('Пользователь с таким email уже существует.')
		return email

	def save(self, commit=True):
		user = super().save(commit=False)
		user.username = self.cleaned_data['email']
		user.email = self.cleaned_data['email']
		if commit:
			user.save()
			ManagerProfile.objects.create(
				user=user,
				full_name=self.cleaned_data['full_name'],
				is_active=self.cleaned_data['is_active'],
			)
		return user


@login_required
def add_project(request):
	student, _ = Student.objects.get_or_create(user=request.user, defaults={'full_name': request.user.username, 'course': 'Студент'})
	if request.method == 'POST':
		form = ProjectForm(request.POST, request.FILES)
		if form.is_valid():
			project = form.save(commit=False)
			project.student = student
			project.is_approved = False
			project.is_public = False
			project.save()
			student.is_approved = False
			student.is_submitted_for_review = False
			student.save(update_fields=['is_approved', 'is_submitted_for_review', 'updated_at'])
			return render(request, 'portfolio/add_project_success.html')
	else:
		form = ProjectForm()
	return render(request, 'portfolio/add_project.html', {'form': form, 'edit_mode': False})


@login_required
def edit_project(request, project_id):
	student, _ = Student.objects.get_or_create(user=request.user, defaults={'full_name': request.user.username, 'course': 'Студент'})
	project = Achievement.objects.filter(id=project_id, student=student).first()
	if not project:
		return redirect('dashboard')

	if request.method == 'POST':
		form = ProjectForm(request.POST, request.FILES, instance=project)
		if form.is_valid():
			updated_project = form.save(commit=False)
			updated_project.student = student
			updated_project.is_approved = False
			updated_project.is_public = False
			updated_project.save()
			student.is_approved = False
			student.is_submitted_for_review = False
			student.save(update_fields=['is_approved', 'is_submitted_for_review', 'updated_at'])
			return redirect('dashboard')
	else:
		form = ProjectForm(instance=project)

	return render(request, 'portfolio/add_project.html', {'form': form, 'edit_mode': True, 'project': project})


@login_required
def edit_employer_profile(request):
	employer, _ = Employer.objects.get_or_create(user=request.user, defaults={'company_name': '', 'sector': 'other', 'contact_person': ''})
	if request.method == 'POST':
		form = EmployerProfileForm(request.POST, instance=employer)
		if form.is_valid():
			form.save()
			return render(request, 'portfolio/edit_employer_profile_success.html')
	else:
		form = EmployerProfileForm(instance=employer)
	return render(request, 'portfolio/edit_employer_profile.html', {'form': form})


@login_required
def dashboard(request):
	if is_manager_user(request.user) and not hasattr(request.user, 'student') and not hasattr(request.user, 'employer'):
		return redirect('manager_dashboard')

	if hasattr(request.user, 'employer'):
		employer = request.user.employer
		profile_status = 'Ожидает проверки менеджером'
		if employer.is_approved:
			profile_status = 'Работодатель одобрен'
		return render(request, 'portfolio/dashboard.html', {'employer': employer, 'profile_status': profile_status})

	if hasattr(request.user, 'student'):
		student = request.user.student
		save_message = ''
		if request.method == 'POST':
			dashboard_form = StudentDashboardForm(request.POST, request.FILES, instance=student)
			if dashboard_form.is_valid():
				dashboard_form.save()
				save_message = 'Изменения сохранены в черновик. Когда будете готовы, отправьте профиль на модерацию.'
				dashboard_form = StudentDashboardForm(instance=student)
		else:
			dashboard_form = StudentDashboardForm(instance=student)

		profile_status = 'Черновик: заполните профиль и отправьте на модерацию'
		if student.is_submitted_for_review:
			profile_status = 'На модерации у менеджера'
		if student.is_approved:
			profile_status = 'Одобрен и виден на доске почета'
		elif student.rejection_reason and not student.is_submitted_for_review:
			profile_status = 'Возвращен на доработку менеджером'
		
		# Подготавливаем данные для шаблона
		achievements_pending_count = student.achievements.filter(is_approved=False).count()
		
		return render(request, 'portfolio/dashboard.html', {
			'student': student, 
			'dashboard_form': dashboard_form,
			'save_message': save_message,
			'profile_status': profile_status,
			'achievements_pending_count': achievements_pending_count,
		})

	return render(request, 'portfolio/dashboard.html', {'student': None, 'profile_status': 'Неопределен'})


@manager_required
def manager_dashboard(request):
	pending_students = Student.objects.filter(is_submitted_for_review=True).count()
	pending_employers = Employer.objects.filter(is_approved=False).count()
	pending_achievements = Achievement.objects.filter(is_approved=False, student__is_submitted_for_review=True).count()
	recent_students = Student.objects.order_by('-updated_at')[:5]
	recent_employers = Employer.objects.order_by('-created_at')[:5]
	return render(request, 'portfolio/manager_dashboard.html', {
		'pending_students': pending_students,
		'pending_employers': pending_employers,
		'pending_achievements': pending_achievements,
		'recent_students': recent_students,
		'recent_employers': recent_employers,
		'can_manage_managers': request.user.is_staff or request.user.is_superuser,
	})


@manager_required
def manager_students_pending(request):
	students = Student.objects.filter(is_submitted_for_review=True).select_related('user').prefetch_related('skills', 'achievements')
	return render(request, 'portfolio/manager_students_pending.html', {'students': students})


@manager_required
def manager_students_all(request):
	q = (request.GET.get('q') or '').strip()
	students = Student.objects.all().select_related('user').order_by('full_name')
	if q:
		students = students.filter(Q(full_name__icontains=q) | Q(course__icontains=q) | Q(user__email__icontains=q))
	return render(request, 'portfolio/manager_students_all.html', {'students': students, 'q': q})


@manager_required
def manager_unpublish_student(request, student_id):
	if request.method != 'POST':
		return redirect('manager_students_all')

	student = Student.objects.filter(id=student_id).first()
	if not student:
		return redirect('manager_students_all')

	student.is_approved = False
	student.is_submitted_for_review = False
	if not (student.rejection_reason or '').strip():
		student.rejection_reason = 'Профиль снят с доски почёта менеджером.'
	student.save(update_fields=['is_approved', 'is_submitted_for_review', 'rejection_reason', 'updated_at'])
	student.achievements.update(is_public=False)
	create_notification(
		user=student.user,
		title='Профиль снят с доски почёта',
		message='Менеджер снял ваш профиль с доски почёта. При необходимости обновите данные и отправьте профиль на модерацию.',
		url='/dashboard/',
		level='warning',
		send_email=True,
		email_subject='Профиль снят с доски почёта',
		email_message='Менеджер снял ваш профиль с доски почёта. Войдите в кабинет и при необходимости отправьте профиль на модерацию повторно: /dashboard/',
	)
	return redirect('manager_students_all')


@manager_required
def manager_employers_pending(request):
	employers = Employer.objects.filter(is_approved=False).select_related('user')
	return render(request, 'portfolio/manager_employers_pending.html', {'employers': employers})


@manager_required
def manager_employers_all(request):
	q = (request.GET.get('q') or '').strip()
	employers = Employer.objects.all().select_related('user').order_by('company_name')
	if q:
		employers = employers.filter(Q(company_name__icontains=q) | Q(contact_person__icontains=q) | Q(user__email__icontains=q))
	return render(request, 'portfolio/manager_employers_all.html', {'employers': employers, 'q': q})


@manager_required
def manager_create_student(request):
	"""
	Менеджер создаёт студента и высылает логин/пароль на его email.
	"""
	created_user = None
	plain_password = None
	email_sent = False
	email_error = ''

	if request.method == 'POST':
		form = AdminCreateStudentForm(request.POST)
		if form.is_valid():
			email = form.cleaned_data['email']
			plain_password = get_random_string(12)
			try:
				with transaction.atomic():
					user = User.objects.create_user(
						username=email,
						email=email,
						password=plain_password,
					)
					Student.objects.create(
						user=user,
						full_name=form.cleaned_data['full_name'],
						course=form.cleaned_data['course'],
						birth_date=form.cleaned_data['birth_date'],
						is_approved=False,
						data_processing_consent=False,
					)
					send_mail(
						subject='Доступ к личному кабинету студента',
						message=(
							'Здравствуйте!\n\n'
							'Для вас создан аккаунт студента в системе "Доска почета".\n\n'
							f'Логин: {email}\n'
							f'Временный пароль: {plain_password}\n\n'
							'Рекомендуем сменить пароль после первого входа.\n'
							'Вход: /login/\n'
						),
						from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
						recipient_list=[email],
						fail_silently=False,
					)
				created_user = user
				email_sent = True
			except Exception as exc:
				plain_password = None
				email_error = f'Студент не создан: письмо не отправлено. Ошибка: {exc}'
	else:
		form = AdminCreateStudentForm()

	return render(request, 'portfolio/manager_create_student.html', {
		'form': form,
		'created_user': created_user,
		'plain_password': plain_password,
		'email_sent': email_sent,
		'email_error': email_error,
	})


@admin_required
def manager_assign_role(request):
	created_manager_user = None

	if request.method == 'POST':
		create_manager_form = CreateManagerForm(request.POST)
		if create_manager_form.is_valid():
			created_manager_user = create_manager_form.save()
	else:
		create_manager_form = CreateManagerForm()

	return render(request, 'portfolio/manager_assign_role.html', {
		'create_manager_form': create_manager_form,
		'created_manager_user': created_manager_user,
	})


@manager_required
def manager_approve_student(request, student_id):
	student = Student.objects.filter(id=student_id).first()
	if not student:
		return redirect('manager_students_pending')
	student.is_approved = True
	student.is_submitted_for_review = False
	student.rejection_reason = ''
	student.save(update_fields=['is_approved', 'is_submitted_for_review', 'rejection_reason', 'updated_at'])
	student.achievements.update(is_approved=True, is_public=True, admin_comment='')
	create_notification(
		user=student.user,
		title='Профиль одобрен',
		message='Ваш профиль одобрен менеджером и опубликован на доске почёта.',
		url='/dashboard/',
		level='success',
		send_email=True,
		email_subject='Профиль одобрен',
		email_message='Ваш профиль одобрен менеджером и опубликован на доске почёта. Кабинет: /dashboard/',
	)
	return redirect('manager_students_pending')


@manager_required
def manager_reject_student(request, student_id):
	student = Student.objects.filter(id=student_id).first()
	if not student:
		return redirect('manager_students_pending')
	reason = (request.POST.get('reason') or '').strip()
	student.is_approved = False
	student.is_submitted_for_review = False
	student.rejection_reason = reason or 'Требуется доработка профиля.'
	student.save(update_fields=['is_approved', 'is_submitted_for_review', 'rejection_reason', 'updated_at'])
	student.achievements.filter(is_approved=False).update(admin_comment=student.rejection_reason, is_public=False)
	create_notification(
		user=student.user,
		title='Профиль возвращён на доработку',
		message=f'Менеджер вернул профиль на доработку. Причина: {student.rejection_reason}',
		url='/dashboard/',
		level='warning',
		send_email=True,
		email_subject='Профиль возвращён на доработку',
		email_message=f'Менеджер вернул профиль на доработку.\n\nПричина:\n{student.rejection_reason}\n\nИсправьте и отправьте на модерацию в кабинете: /dashboard/',
	)
	return redirect('manager_students_pending')


@login_required
def submit_profile_for_moderation(request):
	if request.method != 'POST':
		return redirect('dashboard')
	if not hasattr(request.user, 'student'):
		return redirect('dashboard')

	student = request.user.student
	student.is_approved = False
	student.is_submitted_for_review = True
	student.rejection_reason = ''
	student.save(update_fields=['is_approved', 'is_submitted_for_review', 'rejection_reason', 'updated_at'])

	for manager_user in get_manager_users():
		create_notification(
			user=manager_user,
			title='Новая модерация профиля',
			message=f'Студент "{student.full_name}" отправил профиль на модерацию.',
			url='/manager/students/pending/',
			level='info',
			send_email=True,
			email_subject='Новая модерация профиля',
			email_message=f'Студент "{student.full_name}" отправил профиль на модерацию.\nОткройте: /manager/students/pending/',
		)

	send_admin_notification(
		subject='Студент отправил профиль на модерацию',
		message=(
			f'Студент {student.full_name} отправил профиль на модерацию.\n'
			f'Email: {student.user.email or "не указан"}\n'
			f'Группа/специальность: {student.course}\n'
			f'Контактный email: {student.contact_email or "не указан"}\n'
			f'Навыков: {student.skills.count()}\n'
			f'Проектов/достижений: {student.achievements.count()}\n\n'
			'Откройте кабинет менеджера и выполните модерацию.'
		),
	)
	return redirect('dashboard')


@manager_required
def manager_approve_employer(request, employer_id):
	employer = Employer.objects.filter(id=employer_id).first()
	if not employer:
		return redirect('manager_employers_pending')
	employer.is_approved = True
	employer.save(update_fields=['is_approved', 'updated_at'])
	create_notification(
		user=employer.user,
		title='Доступ одобрен',
		message='Менеджер одобрил ваш аккаунт работодателя. Теперь вы можете отправлять запросы на связь студентам.',
		url='/dashboard/',
		level='success',
		send_email=True,
		email_subject='Доступ работодателя одобрен',
		email_message='Менеджер одобрил ваш аккаунт работодателя. Теперь вы можете отправлять запросы на связь студентам.',
	)
	if request.POST.get('redirect') == 'all':
		return redirect('manager_employers_all')
	return redirect('manager_employers_pending')


@manager_required
def manager_block_employer(request, employer_id):
	employer = Employer.objects.filter(id=employer_id).first()
	if not employer:
		return redirect('manager_employers_pending')
	employer.is_approved = False
	employer.save(update_fields=['is_approved', 'updated_at'])
	create_notification(
		user=employer.user,
		title='Доступ отключён',
		message='Менеджер отключил доступ к отправке запросов на связь студентам.',
		url='/dashboard/',
		level='danger',
		send_email=True,
		email_subject='Доступ работодателя отключён',
		email_message='Менеджер отключил доступ к отправке запросов на связь студентам.',
	)
	if request.POST.get('redirect') == 'all':
		return redirect('manager_employers_all')
	return redirect('manager_employers_pending')


def index(request):
	specialty = request.GET.get('specialty', '')
	skill = request.GET.get('skill', '').strip()
	region = request.GET.get('region', '').strip()

	students = Student.objects.filter(is_approved=True, is_private=False)
	if specialty:
		students = students.filter(course__icontains=specialty)
	if skill:
		students = students.filter(Q(skills__name__icontains=skill) | Q(achievements__title__icontains=skill) | Q(achievements__link__icontains=skill)).distinct()
	if region:
		students = students.filter(course__icontains=region)

	featured_vacancies = Vacancy.objects.filter(
		status='published',
		is_public=True,
	).select_related('employer').order_by('-created_at')[:7]

	return render(request, 'portfolio/index.html', {
		'students': students,
		'specialty': specialty,
		'skill': skill,
		'region': region,
		'featured_vacancies': featured_vacancies,
	})


def signup(request):
	redirect_to = request.GET.get('redirect_to', 'dashboard')
	initial_type = request.GET.get('type', 'employer')
	
	if request.method == 'POST':
		user_form = ExtendedUserCreationForm(request.POST)
		user_type = request.POST.get('user_type', 'employer')
		# Студенты больше не регистрируются сами — аккаунт создает менеджер.
		student_form = None
		employer_form = EmployerRegistrationForm(request.POST, prefix='employer')

		if user_form.is_valid():
			if user_type != 'employer':
				user_form.add_error(None, 'Регистрация студента отключена. Аккаунт студента создаёт менеджер.')
			elif employer_form.is_valid():
				user = user_form.save(commit=False)
				user.username = user_form.cleaned_data['email'].lower().strip()
				user.email = user_form.cleaned_data['email'].lower().strip()
				user.save()
				employer = employer_form.save(commit=False)
				employer.user = user
				employer.is_approved = False
				employer.save()
				send_admin_notification(
					subject='Зарегистрировался новый работодатель',
					message=(
						f'Новый работодатель зарегистрировался в системе.\n'
						f'Компания: {employer.company_name}\n'
						f'Контактное лицо: {employer.contact_person}\n'
						f'Email: {user.email}\n'
						f'Сфера: {employer.get_sector_display()}\n'
						f'Сайт: {employer.website or "не указан"}\n\n'
						'Профиль ожидает одобрения.'
					),
				)
				login(request, user)
				return redirect(redirect_to)

	else:
		user_form = ExtendedUserCreationForm()
		employer_form = EmployerRegistrationForm(prefix='employer')

	return render(request, 'portfolio/signup.html', {
		'user_form': user_form, 
		'employer_form': employer_form,
		'initial_type': initial_type,
		'redirect_to': redirect_to
	})


@manager_required
def admin_create_student(request):
	return redirect('manager_create_student')


@login_required
def logout_view(request):
	logout(request)
	return redirect('index')


@login_required
def notifications_list(request):
	mode = (request.GET.get('mode') or '').strip()
	level = (request.GET.get('level') or '').strip()
	items = Notification.objects.filter(user=request.user)
	if mode == 'unread':
		items = items.filter(is_read=False)
	if level:
		items = items.filter(level=level)
	items = items.order_by('-created_at')[:200]
	return render(request, 'portfolio/notifications.html', {
		'items': items,
		'mode': mode,
		'level': level,
		'levels': Notification.LEVEL_CHOICES,
	})


@login_required
def notification_mark_read(request, notification_id):
	if request.method != 'POST':
		return redirect('notifications')
	Notification.objects.filter(id=notification_id, user=request.user).update(is_read=True)
	return redirect('notifications')


@login_required
def notifications_mark_all_read(request):
	if request.method != 'POST':
		return redirect('notifications')
	Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
	return redirect('notifications')


def help_guide(request):
	return render(request, 'portfolio/help_guide.html')


def vacancies_list(request):
	q = (request.GET.get('q') or '').strip()
	region = (request.GET.get('region') or '').strip()
	stack = (request.GET.get('stack') or '').strip()
	emp_type = (request.GET.get('type') or '').strip()

	vacancies = Vacancy.objects.filter(status='published', is_public=True).select_related('employer', 'employer__user').order_by('-created_at')
	if q:
		vacancies = vacancies.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(requirements__icontains=q))
	if region:
		vacancies = vacancies.filter(region__icontains=region)
	if stack:
		vacancies = vacancies.filter(tech_stack__icontains=stack)
	if emp_type:
		vacancies = vacancies.filter(employment_type=emp_type)

	return render(request, 'portfolio/vacancies_list.html', {
		'vacancies': vacancies,
		'q': q,
		'region': region,
		'stack': stack,
		'emp_type': emp_type,
		'emp_types': Vacancy.EMPLOYMENT_TYPES,
	})


def vacancy_detail(request, vacancy_id):
	vacancy = Vacancy.objects.filter(id=vacancy_id, is_public=True).select_related('employer', 'employer__user').first()
	if not vacancy:
		return redirect('vacancies_list')

	already_applied = False
	if hasattr(request.user, 'student'):
		already_applied = Application.objects.filter(vacancy=vacancy, student=request.user.student).exists()

	return render(request, 'portfolio/vacancy_detail.html', {
		'vacancy': vacancy,
		'already_applied': already_applied,
		'can_apply': hasattr(request.user, 'student'),
	})


@login_required
def employer_vacancies(request):
	if not hasattr(request.user, 'employer'):
		return redirect('dashboard')
	employer = request.user.employer
	if not employer.is_approved:
		return redirect('student_profile', student_id=student_id)
	vacancies = Vacancy.objects.filter(employer=employer).order_by('-updated_at')
	return render(request, 'portfolio/employer_vacancies.html', {'vacancies': vacancies})


@login_required
def vacancy_create(request):
	if not hasattr(request.user, 'employer'):
		return redirect('dashboard')
	employer = request.user.employer
	if request.method == 'POST':
		form = VacancyForm(request.POST)
		if form.is_valid():
			vacancy = form.save(commit=False)
			vacancy.employer = employer
			vacancy.save()
			return redirect('employer_vacancies')
	else:
		form = VacancyForm(initial={'status': 'published', 'is_public': True})
	return render(request, 'portfolio/vacancy_form.html', {'form': form, 'edit_mode': False})


@login_required
def vacancy_edit(request, vacancy_id):
	if not hasattr(request.user, 'employer'):
		return redirect('dashboard')
	employer = request.user.employer
	vacancy = Vacancy.objects.filter(id=vacancy_id, employer=employer).first()
	if not vacancy:
		return redirect('employer_vacancies')
	if request.method == 'POST':
		form = VacancyForm(request.POST, instance=vacancy)
		if form.is_valid():
			form.save()
			return redirect('employer_vacancies')
	else:
		form = VacancyForm(instance=vacancy)
	return render(request, 'portfolio/vacancy_form.html', {'form': form, 'edit_mode': True, 'vacancy': vacancy})


@login_required
def vacancy_delete(request, vacancy_id):
	if request.method != 'POST' or not hasattr(request.user, 'employer'):
		return redirect('employer_vacancies')
	employer = request.user.employer
	Vacancy.objects.filter(id=vacancy_id, employer=employer).delete()
	return redirect('employer_vacancies')


@login_required
def apply_to_vacancy(request, vacancy_id):
	if not hasattr(request.user, 'student'):
		return redirect('dashboard')
	student = request.user.student
	vacancy = Vacancy.objects.filter(id=vacancy_id, status='published', is_public=True).select_related('employer', 'employer__user').first()
	if not vacancy:
		return redirect('vacancies_list')
	if request.method == 'POST':
		form = ApplicationForm(request.POST)
		if form.is_valid():
			application, created = Application.objects.get_or_create(
				vacancy=vacancy,
				student=student,
				defaults={'message': form.cleaned_data.get('message', ''), 'status': 'submitted'},
			)
			if not created:
				application.message = form.cleaned_data.get('message', application.message)
				application.status = 'submitted'
				application.save(update_fields=['message', 'status', 'updated_at'])

			create_notification(
				user=vacancy.employer.user,
				title='Новый отклик на вакансию',
				message=f'Студент "{student.full_name}" откликнулся на вакансию "{vacancy.title}".',
				url=f'/profile/{student.id}/',
				level='info',
				send_email=True,
				email_subject='Новый отклик на вакансию',
				email_message=(
					f'На вашу вакансию "{vacancy.title}" поступил отклик.\n\n'
					f'Студент: {student.full_name}\n'
					f'Профиль: /profile/{student.id}/\n'
					f'Вакансия: /vacancies/{vacancy.id}/\n'
				),
			)
			create_notification(
				user=student.user,
				title='Отклик отправлен',
				message=f'Ваш отклик на вакансию "{vacancy.title}" отправлен работодателю.',
				url='/applications/me/',
				level='success',
			)
			return redirect('student_applications')
	else:
		form = ApplicationForm()
	return render(request, 'portfolio/apply_to_vacancy.html', {'form': form, 'vacancy': vacancy})


@login_required
def student_applications(request):
	if not hasattr(request.user, 'student'):
		return redirect('dashboard')
	applications = Application.objects.filter(student=request.user.student).select_related('vacancy', 'vacancy__employer').order_by('-updated_at')
	return render(request, 'portfolio/student_applications.html', {'applications': applications})


@login_required
def employer_applications(request):
	if not hasattr(request.user, 'employer'):
		return redirect('dashboard')
	employer = request.user.employer
	applications = Application.objects.filter(vacancy__employer=employer).select_related('student', 'vacancy').order_by('-updated_at')
	return render(request, 'portfolio/employer_applications.html', {'applications': applications})


@login_required
def student_contact_requests(request):
	if not hasattr(request.user, 'student'):
		return redirect('dashboard')
	student = request.user.student
	requests = ContactRequest.objects.filter(student=student).select_related('employer', 'employer__user').order_by('-requested_at')
	return render(request, 'portfolio/student_contact_requests.html', {'requests': requests})


@login_required
def approve_contact_request(request, request_id):
	if request.method != 'POST' or not hasattr(request.user, 'student'):
		return redirect('student_contact_requests')
	cr = ContactRequest.objects.filter(id=request_id, student=request.user.student).select_related('employer', 'employer__user').first()
	if not cr or cr.status != 'pending_student':
		return redirect('student_contact_requests')
	form = ContactRequestDecisionForm(request.POST)
	if form.is_valid():
		cr.status = 'approved_by_student'
		cr.student_response_message = (form.cleaned_data.get('response_message') or '').strip()
		cr.responded_at = timezone.now()
		cr.save(update_fields=['status', 'student_response_message', 'responded_at', 'updated_at'])

		create_notification(
			user=cr.employer.user,
			title='Запрос контакта одобрен студентом',
			message=f'Студент "{cr.student.full_name}" одобрил ваш запрос на связь. Теперь контакты доступны в профиле.',
			url=f'/profile/{cr.student.id}/',
			level='success',
			send_email=True,
			email_subject='Запрос контакта одобрен',
			email_message=(
				f'Студент "{cr.student.full_name}" одобрил ваш запрос на связь.\n'
				f'Откройте профиль: /profile/{cr.student.id}/'
			),
		)
		create_notification(
			user=cr.student.user,
			title='Вы одобрили запрос на связь',
			message=f'Вы одобрили запрос компании "{cr.employer.company_name}".',
			url='/contact-requests/me/',
			level='success',
		)
	return redirect('student_contact_requests')


@login_required
def reject_contact_request(request, request_id):
	if request.method != 'POST' or not hasattr(request.user, 'student'):
		return redirect('student_contact_requests')
	cr = ContactRequest.objects.filter(id=request_id, student=request.user.student).select_related('employer', 'employer__user').first()
	if not cr or cr.status != 'pending_student':
		return redirect('student_contact_requests')
	form = ContactRequestDecisionForm(request.POST)
	if form.is_valid():
		cr.status = 'rejected_by_student'
		cr.student_response_message = (form.cleaned_data.get('response_message') or '').strip()
		cr.responded_at = timezone.now()
		cr.save(update_fields=['status', 'student_response_message', 'responded_at', 'updated_at'])
		create_notification(
			user=cr.employer.user,
			title='Запрос контакта отклонён',
			message=f'Студент "{cr.student.full_name}" отклонил запрос на связь.',
			url=f'/profile/{cr.student.id}/',
			level='warning',
			send_email=True,
			email_subject='Запрос контакта отклонён',
			email_message=f'Студент "{cr.student.full_name}" отклонил запрос на связь.',
		)
	return redirect('student_contact_requests')


def login_view(request):
	if request.method == 'POST':
		form = CustomAuthenticationForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			login(request, user)
			return redirect('index')
	else:
		form = CustomAuthenticationForm()
	return render(request, 'portfolio/login.html', {'form': form})


def student_profile(request, student_id):
	try:
		student = Student.objects.get(id=student_id)
	except Student.DoesNotExist:
		return redirect('index')

	if (
		(student.is_private and request.user != student.user and not is_manager_user(request.user))
		or
		(not student.is_approved and not is_manager_user(request.user) and request.user != student.user)
	):
		return redirect('index')

	can_see_contacts = False
	is_own_profile = False
	is_employer_user = False
	is_employer_approved = False
	contact_request_status = ''
	
	if request.user.is_authenticated:
		is_own_profile = request.user == student.user
		
		# Студент видит свои контакты
		if is_own_profile:
			can_see_contacts = True
		# Работодатель НЕ видит контакты студента (только запрос через письмо студенту)
		elif hasattr(request.user, 'employer'):
			employer = request.user.employer
			is_employer_user = True
			is_employer_approved = employer.is_approved
			if employer.is_approved:
				can_see_contacts = has_employer_contact_access(employer, student)
				existing_request = ContactRequest.objects.filter(employer=employer, student=student).first()
				if existing_request:
					contact_request_status = existing_request.status
		elif is_manager_user(request.user):
			can_see_contacts = True

	context = {
		'student': student,
		'achievements': student.achievements.filter(is_approved=True, is_public=True),
		'skills': student.skills.all(),
		'can_see_contacts': can_see_contacts,
		'is_own_profile': is_own_profile,
		'is_student_adult': student.is_adult,
		'is_employer_user': is_employer_user,
		'is_employer_approved': is_employer_approved,
		'contact_request_status': contact_request_status,
	}
	return render(request, 'portfolio/student_profile.html', context)


@login_required
def request_contact(request, student_id):
	"""Работодатель запрашивает контакты студента"""
	try:
		student = Student.objects.get(id=student_id)
	except Student.DoesNotExist:
		return redirect('index')
	
	# Проверяем, что это работодатель
	if not hasattr(request.user, 'employer'):
		return redirect('index')
	
	employer = request.user.employer

	# Контакты несовершеннолетних недоступны работодателям.
	if not student.is_adult:
		return redirect('student_profile', student_id=student_id)
	
	message_form = ContactRequestMessageForm(request.POST)
	message_text = ''
	if message_form.is_valid():
		message_text = (message_form.cleaned_data.get('message') or '').strip()

	contact_request, created = ContactRequest.objects.get_or_create(
		employer=employer,
		student=student,
		defaults={
			'status': 'pending_student',
			'employer_message': message_text,
		},
	)
	if not created and contact_request.status != 'pending_student':
		contact_request.status = 'pending_student'
	contact_request.employer_message = message_text
	contact_request.responded_at = None
	contact_request.student_response_message = ''
	contact_request.save(update_fields=['status', 'employer_message', 'responded_at', 'student_response_message', 'updated_at'])

	if created or contact_request.status == 'pending_student':
		create_notification(
			user=student.user,
			title='Запрос на связь от работодателя',
			message=f'Работодатель "{employer.company_name}" отправил запрос на связь. Перейдите в запросы и одобрите или отклоните.',
			url='/contact-requests/me/',
			level='info',
			send_email=False,
		)
		student_email = (student.user.email or '').strip()
		if student_email:
			try:
				send_mail(
					subject='Запрос на связь от работодателя',
					message=(
						'Здравствуйте!\n\n'
						'Работодатель хочет связаться с вами по вашему портфолио на «Доске почёта».\n\n'
						f'Организация: {employer.company_name}\n'
						f'Контактное лицо: {employer.contact_person}\n'
						f'Email: {employer.user.email}\n'
						f'Сайт: {employer.website or "не указан"}\n\n'
						f'Комментарий работодателя: {message_text or "не указан"}\n\n'
						'Подтвердите или отклоните запрос в кабинете.\n'
						'Ваши контакты работодателю не раскрываются без вашего одобрения.'
					),
					from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
					recipient_list=[student_email],
					fail_silently=True,
				)
			except Exception:
				pass
	
	return redirect('student_profile', student_id=student_id)

