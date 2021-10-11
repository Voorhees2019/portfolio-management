from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('login/', views.login, name='login'),
    path('set-password/', views.set_user_password, name='set_password'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('email-confirm/<uidb64>/<token>/', views.email_confirm, name='email_confirm'),
    # password change
    path(
        'password-change/',
        auth_views.PasswordChangeView.as_view(
            template_name='accounts/password_change_form.html',
        ),
        name='password_change'),
    path(
        'password-change/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='accounts/password_change_done.html',
        ),
        name='password_change_done'),
    # password reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
            html_email_template_name='accounts/email/password_reset.html',
            subject_template_name='accounts/email/password_reset_subject.txt',
            template_name='accounts/password_reset.html',
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html',
        ), name='password_reset_done'),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    # user profile
    path('profile/personal-information/', views.personal_information, name='personal_information'),
    path('profile/personal-information/verify-email/', views.verify_profile_email, name='verify_profile_email'),
    path('profile/personal-information/edit/', views.edit_personal_information, name='edit_personal_information'),
]
