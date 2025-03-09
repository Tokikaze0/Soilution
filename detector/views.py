from django.shortcuts import render, redirect
from django.contrib.auth.models import User 
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from django.urls import reverse
from detector.models import PasswordReset

def index(request):
    return render(request, 'detector/index.html')

def about(request):
    return render(request, 'detector/about.html')

def services(request):
    return render(request, 'detector/services.html')

def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return redirect('dashboard')
            else:
                messages.info(request, "Please verify your email. We've sent you another verification email.")
                return redirect('login')

        else:
            messages.error(request, "Invalid login credentials. Please try again.")
            return redirect('login')

    return render(request, 'login.html')
 
def register(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user_data_has_error = False

        if User.objects.filter(username=username).exists():
            user_data_has_error = True
            messages.error(request, "This username is already existed.")

        if User.objects.filter(email=email).exists():
            user_data_has_error = True
            messages.error(request, "This email is already in use. Please use a different email address.")

        if len(password) < 5:
            user_data_has_error = True
            messages.error(request, "Password must be at least 5 characters")

        if user_data_has_error:
            return redirect('register')
        else:
            new_user = User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email, 
                password=password,
                is_active=False
            )

            request.session['just_registered'] = True

            token = default_token_generator.make_token(new_user)
            uid = urlsafe_base64_encode(str(new_user.pk).encode())

            domain = 'localhost:8000'
            mail_subject = "Confirm your registration"
            message = render_to_string('confirmation_email.html', {
                'user': new_user,
                'domain': domain,
                'uid': uid,
                'token': token,
            })
            send_mail(mail_subject, message, settings.DEFAULT_FROM_EMAIL, [email],  html_message=message,)

            # messages.success(request, "Account created. Please check your email to confirm your registration.")
            return redirect('verification_email')

    return render(request, 'register.html')

def confirm_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = get_user_model().objects.get(pk=uid)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()

            messages.success(request, "Email confirmed! You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "The confirmation link is invalid or expired.")
            return redirect('register')

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, "Invalid confirmation link.")
        return redirect('register')

def verification_email(request):
    if not request.session.get('just_registered', False):
        return redirect('login')
    
    return render(request, 'verification_email.html')

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

def ForgotPassword(request):
    if request.method == "POST":
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)

            new_password_reset = PasswordReset(user=user)
            new_password_reset.save()

            password_reset_url = reverse('reset-password', kwargs={'reset_id': new_password_reset.reset_id})

            full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'

            context = {
                'user': user,
                'reset_url': full_password_reset_url,
            }

            email_body = render_to_string('password_reset_email.html', context)
        
            email_message = EmailMessage(
                'Reset your password',
                email_body,
                settings.EMAIL_HOST_USER, 
                [email]
            )

            email_message.content_subtype = 'html'
            
            email_message.fail_silently = True
            email_message.send()

            return redirect('password-reset-sent', reset_id=new_password_reset.reset_id)

        except User.DoesNotExist:
            messages.error(request, f"No user with email '{email}' found")
            return redirect('forgot-password')

    return render(request, 'forgot_password.html')

def PasswordResetSent(request, reset_id):
    if PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request, 'password_reset_sent.html')
    else:
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

def ResetPassword(request, reset_id):
    try:
        password_reset_id = PasswordReset.objects.get(reset_id=reset_id)

        if request.method == "POST":
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            passwords_have_error = False

            if password != confirm_password:
                passwords_have_error = True
                messages.error(request, 'Passwords do not match')

            if len(password) < 5:
                passwords_have_error = True
                messages.error(request, 'Password must be at least 5 characters long')

            expiration_time = password_reset_id.created_when + timezone.timedelta(minutes=10)

            if timezone.now() > expiration_time:
                passwords_have_error = True
                messages.error(request, 'Reset link has expired')

                password_reset_id.delete()

            if not passwords_have_error:
                user = password_reset_id.user
                user.set_password(password)
                user.save()

                password_reset_id.delete()

                messages.success(request, 'Password reset. Proceed to login')
                return redirect('login')
            else:
                return redirect('reset-password', reset_id=reset_id)

    
    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

    return render(request, 'reset_password.html')

def logoutView(request):
    logout(request)
    return redirect('index')


