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
from portfolio import views as portfolio_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', portfolio_views.index, name='index'),
    path('signup/', portfolio_views.signup, name='signup'),
    path('login/', portfolio_views.login_view, name='login'),
    path('accounts/login/', RedirectView.as_view(url='/login/', permanent=False)),
    path('logout/', portfolio_views.logout_view, name='logout'),
    path('profile/<int:student_id>/', portfolio_views.student_profile, name='student_profile'),
    path('profile/<int:student_id>/request-contact/', portfolio_views.request_contact, name='request_contact'),
    path('dashboard/', portfolio_views.dashboard, name='dashboard'),
    path('edit-profile/', portfolio_views.edit_profile, name='edit_profile'),
    path('edit-employer-profile/', portfolio_views.edit_employer_profile, name='edit_employer_profile'),
    path('edit-skills/', portfolio_views.edit_skills, name='edit_skills'),
    path('add-project/', portfolio_views.add_project, name='add_project'),
    path('edit-privacy/', portfolio_views.edit_privacy, name='edit_privacy'),
]
