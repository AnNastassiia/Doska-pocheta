"""
URL configuration for student_portfolio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.conf import settings
from django.conf.urls.static import static
from portfolio import views as portfolio_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', portfolio_views.index, name='index'),
    path('signup/', portfolio_views.signup, name='signup'),
    path('help/guide/', portfolio_views.help_guide, name='help_guide'),
    path('login/', portfolio_views.login_view, name='login'),
    path('accounts/login/', RedirectView.as_view(url='/login/', permanent=False)),
    path('logout/', portfolio_views.logout_view, name='logout'),
    path('password_reset/', PasswordResetView.as_view(template_name='portfolio/password_reset.html'), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(template_name='portfolio/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='portfolio/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(template_name='portfolio/password_reset_complete.html'), name='password_reset_complete'),
    path('notifications/', portfolio_views.notifications_list, name='notifications'),
    path('notifications/<int:notification_id>/read/', portfolio_views.notification_mark_read, name='notification_mark_read'),
    path('notifications/read-all/', portfolio_views.notifications_mark_all_read, name='notifications_mark_all_read'),
    path('vacancies/', portfolio_views.vacancies_list, name='vacancies_list'),
    path('vacancies/<int:vacancy_id>/', portfolio_views.vacancy_detail, name='vacancy_detail'),
    path('vacancies/<int:vacancy_id>/apply/', portfolio_views.apply_to_vacancy, name='apply_to_vacancy'),
    path('applications/me/', portfolio_views.student_applications, name='student_applications'),
    path('applications/employer/', portfolio_views.employer_applications, name='employer_applications'),
    path('applications/<int:application_id>/status/', portfolio_views.update_application_status, name='update_application_status'),
    path('contact-requests/me/', portfolio_views.student_contact_requests, name='student_contact_requests'),
    path('contact-requests/<int:request_id>/approve/', portfolio_views.approve_contact_request, name='approve_contact_request'),
    path('contact-requests/<int:request_id>/reject/', portfolio_views.reject_contact_request, name='reject_contact_request'),
    path('profile/<int:student_id>/', portfolio_views.student_profile, name='student_profile'),
    path('profile/<int:student_id>/request-contact/', portfolio_views.request_contact, name='request_contact'),
    path('profile/<int:student_id>/invite/', portfolio_views.create_inquiry, name='create_inquiry'),
    path('inquiries/student/', portfolio_views.student_inquiries, name='student_inquiries'),
    path('inquiries/employer/', portfolio_views.employer_inquiries, name='employer_inquiries'),
    path('inquiries/<int:inquiry_id>/status/', portfolio_views.update_inquiry_status, name='update_inquiry_status'),
    path('dashboard/', portfolio_views.dashboard, name='dashboard'),
    path('edit-employer-profile/', portfolio_views.edit_employer_profile, name='edit_employer_profile'),
    path('add-project/', portfolio_views.add_project, name='add_project'),
    path('edit-project/<int:project_id>/', portfolio_views.edit_project, name='edit_project'),
    path('submit-profile-for-moderation/', portfolio_views.submit_profile_for_moderation, name='submit_profile_for_moderation'),
    path('manager/dashboard/', portfolio_views.manager_dashboard, name='manager_dashboard'),
    path('manager/managers/assign/', portfolio_views.manager_assign_role, name='manager_assign_role'),
    path('manager/students/create/', portfolio_views.manager_create_student, name='manager_create_student'),
    path('manager/students/pending/', portfolio_views.manager_students_pending, name='manager_students_pending'),
    path('manager/students/all/', portfolio_views.manager_students_all, name='manager_students_all'),
    path('manager/students/<int:student_id>/unpublish/', portfolio_views.manager_unpublish_student, name='manager_unpublish_student'),
    path('manager/students/<int:student_id>/approve/', portfolio_views.manager_approve_student, name='manager_approve_student'),
    path('manager/students/<int:student_id>/reject/', portfolio_views.manager_reject_student, name='manager_reject_student'),
    path('manager/employers/pending/', portfolio_views.manager_employers_pending, name='manager_employers_pending'),
    path('manager/employers/all/', portfolio_views.manager_employers_all, name='manager_employers_all'),
    path('manager/employers/<int:employer_id>/approve/', portfolio_views.manager_approve_employer, name='manager_approve_employer'),
    path('manager/employers/<int:employer_id>/block/', portfolio_views.manager_block_employer, name='manager_block_employer'),
    path('employer/vacancies/', portfolio_views.employer_vacancies, name='employer_vacancies'),
    path('employer/vacancies/create/', portfolio_views.vacancy_create, name='vacancy_create'),
    path('employer/vacancies/<int:vacancy_id>/edit/', portfolio_views.vacancy_edit, name='vacancy_edit'),
    path('employer/vacancies/<int:vacancy_id>/delete/', portfolio_views.vacancy_delete, name='vacancy_delete'),
    path('admin/create-student/', portfolio_views.admin_create_student, name='admin_create_student'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
