from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Student, Skill, Achievement, Employer, ContactRequest, EnrollmentOrder
from django.contrib.auth.models import User


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
		fields = ('username', 'email', 'password1', 'password2', 'user_type')

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
		fields = ['full_name', 'course', 'student_card_number', 'social_link', 'photo', 'contact_email']


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


class ProjectForm(forms.ModelForm):
	class Meta:
		model = Achievement
		fields = ['title', 'description', 'achievement_type', 'document', 'project_file', 'date_achieved']


class PrivacyForm(forms.ModelForm):
	class Meta:
		model = Student
		fields = ['hide_contacts', 'is_private']


@login_required
def edit_privacy(request):
	student, _ = Student.objects.get_or_create(user=request.user, defaults={'full_name': request.user.username, 'course': 'Студент'})
	if request.method == 'POST':
		form = PrivacyForm(request.POST, instance=student)
		if form.is_valid():
			form.save()
			return render(request, 'portfolio/edit_privacy_success.html')
	else:
		form = PrivacyForm(instance=student)
	return render(request, 'portfolio/edit_privacy.html', {'form': form})


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
			return render(request, 'portfolio/add_project_success.html')
	else:
		form = ProjectForm()
	return render(request, 'portfolio/add_project.html', {'form': form})


@login_required
def edit_skills(request):
	student, _ = Student.objects.get_or_create(user=request.user, defaults={'full_name': request.user.username, 'course': 'Студент'})
	if request.method == 'POST':
		form = SkillForm(request.POST)
		if form.is_valid():
			student.skills.set(form.cleaned_data['skills'])
			return render(request, 'portfolio/edit_skills_success.html')
	else:
		form = SkillForm(initial={'skills': student.skills.all()})
	return render(request, 'portfolio/edit_skills.html', {'form': form})


@login_required
def edit_profile(request):
	student, _ = Student.objects.get_or_create(user=request.user, defaults={'full_name': request.user.username, 'course': 'Студент'})
	if request.method == 'POST':
		form = StudentProfileForm(request.POST, request.FILES, instance=student)
		if form.is_valid():
			form.save()
			return render(request, 'portfolio/edit_profile_success.html')
	else:
		form = StudentProfileForm(instance=student)
	return render(request, 'portfolio/edit_profile.html', {'form': form})


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
	if hasattr(request.user, 'employer'):
		employer = request.user.employer
		profile_status = 'Ожидает одобрения администрацией'
		if employer.is_approved:
			profile_status = 'Работодатель одобрен'
		return render(request, 'portfolio/dashboard.html', {'employer': employer, 'profile_status': profile_status})

	if hasattr(request.user, 'student'):
		student = request.user.student
		profile_status = 'Ожидает одобрения администрацией'
		if student.is_approved:
			profile_status = 'Одобрен и виден на доске почета'
		
		# Подготавливаем данные для шаблона
		achievements_pending_count = student.achievements.filter(is_approved=False).count()
		
		return render(request, 'portfolio/dashboard.html', {
			'student': student, 
			'profile_status': profile_status,
			'achievements_pending_count': achievements_pending_count
		})

	return render(request, 'portfolio/dashboard.html', {'student': None, 'profile_status': 'Неопределен'})


def index(request):
	specialty = request.GET.get('specialty', '')
	skill = request.GET.get('skill', '').strip()

	students = Student.objects.filter(is_approved=True, is_private=False)
	if specialty:
		students = students.filter(course__icontains=specialty)
	if skill:
		students = students.filter(achievements__description__icontains=skill).distinct()

	return render(request, 'portfolio/index.html', {'students': students, 'specialty': specialty, 'skill': skill})


def signup(request):
	redirect_to = request.GET.get('redirect_to', 'dashboard')
	initial_type = request.GET.get('type', 'student')
	
	if request.method == 'POST':
		user_form = ExtendedUserCreationForm(request.POST)
		student_form = StudentRegistrationForm(request.POST, prefix='student')
		employer_form = EmployerRegistrationForm(request.POST, prefix='employer')

		if user_form.is_valid():
			user_type = user_form.cleaned_data['user_type']
			if user_type == 'student' and student_form.is_valid():
				user = user_form.save(commit=False)
				user.username = user_form.cleaned_data['email']
				user.email = user_form.cleaned_data['email']
				user.save()
				student = student_form.save(commit=False)
				student.user = user
				student.is_approved = False
				student.save()
				login(request, user)
				return redirect('dashboard')

			if user_type == 'employer' and employer_form.is_valid():
				user = user_form.save(commit=False)
				user.username = user_form.cleaned_data['email']
				user.email = user_form.cleaned_data['email']
				user.save()
				employer = employer_form.save(commit=False)
				employer.user = user
				employer.is_approved = False
				employer.save()
				login(request, user)
				return redirect(redirect_to)

	else:
		user_form = ExtendedUserCreationForm()
		student_form = StudentRegistrationForm(prefix='student')
		employer_form = EmployerRegistrationForm(prefix='employer')

	return render(request, 'portfolio/signup.html', {
		'user_form': user_form, 
		'student_form': student_form, 
		'employer_form': employer_form,
		'initial_type': initial_type,
		'redirect_to': redirect_to
	})


@login_required
def logout_view(request):
	logout(request)
	return redirect('index')


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

	if (student.is_private and request.user != student.user) or (not student.is_approved and not request.user.is_staff and request.user != student.user):
		return redirect('index')

	can_see_contacts = False
	is_own_profile = False
	
	if request.user.is_authenticated:
		is_own_profile = request.user == student.user
		
		# Студент видит свои контакты
		if is_own_profile:
			can_see_contacts = True
		# Работодатель видит контакты, если его профиль одобрен
		elif hasattr(request.user, 'employer'):
			employer = request.user.employer
			can_see_contacts = employer.is_approved

	context = {
		'student': student,
		'achievements': student.achievements.filter(is_approved=True, is_public=True),
		'skills': student.skills.all(),
		'can_see_contacts': can_see_contacts,
		'is_own_profile': is_own_profile,
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
	
	# Проверяем, не заказывал ли уже
	existing_request = ContactRequest.objects.filter(employer=employer, student=student).first()
	if not existing_request:
		ContactRequest.objects.create(employer=employer, student=student)
	
	return redirect('student_profile', student_id=student_id)

