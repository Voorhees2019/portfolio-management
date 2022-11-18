from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from .models import User, Company
from .forms import EditUserForm, CompanyForm
from .tokens import account_activation_token
from .tasks import send_verification_email


@login_required
def personal_information(request):
    user = request.user
    context = {
        'user': user,
        'menu': 'personal_information',
    }
    return render(request, 'accounts/personal_information.html', context)


@login_required
def edit_personal_information(request):
    user = request.user
    if request.method == 'POST':
        form = EditUserForm(instance=user, data=request.POST, files=request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.email_confirmed = False
            user.save()
            return redirect(reverse('personal_information'))
    else:
        form = EditUserForm(instance=user)
    context = {
        'form': form,
        'menu': 'personal_information',
    }
    return render(request, 'accounts/edit_personal_information.html', context)


def login(request):
    from .forms import UserAuthForm

    redirect_to = request.POST.get('next', request.GET.get('next', ''))

    if request.user.is_authenticated:
        if redirect_to == request.path:
            raise ValueError('Redirection loop for authenticated user detected.')
        return redirect(reverse('index'))
    elif request.method == 'POST':
        form = UserAuthForm(request, data=request.POST)
        if form.is_valid():
            auth.login(request, form.get_user())
            return redirect(reverse('index'))
    else:
        form = UserAuthForm(request)

    context = {
        'form': form,
    }
    return render(request, 'accounts/login.html', context)


def notify_verification_email_sent(request):
    messages.success(request, 'Verification email has been sent to your email address. Please check your inbox.')


def verify_profile_email(request):
    user = request.user
    send_verification_email.delay(user_id=user.id)
    notify_verification_email_sent(request)
    return redirect('personal_information')


def register(request):
    from .forms import UserRegistrationForm
    if request.user.is_authenticated:
        return redirect(reverse('index'))

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            user.save()
            send_verification_email.delay(user_id=user.id)
            notify_verification_email_sent(request)
            auth.login(request, user)
            return redirect('personal_information')
    else:
        form = UserRegistrationForm()

    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)


def set_user_password(request):
    from django.contrib.auth.forms import SetPasswordForm
    if request.user.has_usable_password():
        return redirect('password_change')

    user = get_object_or_404(User, id=request.user.id)

    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your new password has been successfully set')
            return redirect('personal_information')
    else:
        form = SetPasswordForm(user)

    context = {
        'form': form,
    }
    return render(request, 'accounts/set_password.html', context)


def email_confirm(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.email_confirmed = True
        user.save()
        messages.success(request, 'Email address successfully confirmed.')
        return redirect('personal_information')
    else:
        return HttpResponse('Activation link is invalid!')


def logout(request):
    _next = request.GET.get('next')
    auth.logout(request)
    return redirect(_next if _next else settings.LOGOUT_REDIRECT_URL)


def company_information(request):
    company = Company.objects.filter(founder=request.user).first()
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            company = form.save(commit=False)
            company.founder = request.user
            company.save()
            return redirect('company_information')
    else:
        form = CompanyForm(instance=company)
    return render(request, 'accounts/company_information.html', {'form': form})
