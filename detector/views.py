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
from detector.models import PasswordReset, Workspace
from .forms import WorkspaceForm
from allauth.socialaccount.models import SocialAccount
from django.http import JsonResponse
from supabase import create_client, Client
from .forms import UserProfileForm
from .models import Profile
# from django.shortcuts import render, get_object_or_404

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

def index(request):
    return render(request, 'detector/index.html')

def about(request):
    return render(request, 'detector/about.html')

def services(request):
    return render(request, 'detector/services.html')

def admin_dashboard(request):
    return render(request, 'admin/admin_dashboard.html')

def insights(request):
    user = request.user
    profile = user.profile

    profile_picture_url = profile.get_profile_image()

    return render(request, 'insight.html', {'profile_picture_url': profile_picture_url})

def crop_details(request):
    user = request.user
    profile = user.profile

    profile_picture_url = profile.get_profile_image()

    return render(request, 'crop_details.html', {'profile_picture_url': profile_picture_url})

def logs(request):
    user = request.user
    profile = user.profile

    profile_picture_url = profile.get_profile_image()

    return render(request, 'logs.html', {'profile_picture_url': profile_picture_url})

def settings(request):
    user = request.user
    profile = user.profile

    profile_picture_url = profile.get_profile_image()

    return render(request, 'settings.html', {'profile_picture_url': profile_picture_url})

def reports(request):
    user = request.user
    profile = user.profile

    profile_picture_url = profile.get_profile_image()

    return render(request, 'reports.html', {'profile_picture_url': profile_picture_url})

def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user:
            # Check if user has a linked social account (e.g., Google)
            social_account = SocialAccount.objects.filter(user=user, provider='google').first()

            if social_account:
                # User logged in with Google; allow login via Google only
                messages.error(request, "The email is associated with google. Please log in using Google Authentication or reset your password.")
                return redirect('login')
        
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_active:
                auth_login(request, user)
                profile = user.profile
                if profile.role == 'admin':
                    return redirect('admin_dashboard')  # Change this to your actual admin page URL
                else:
                    # Redirect to the user workspace or default user page
                    return redirect('workspace')
            else:
                messages.error(request, "Please verify your email. We've sent you another verification email.")
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

def admin_register(request):
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
                is_active=True
            )

            profile, created = Profile.objects.get_or_create(user=new_user)
            if created:
                # If the profile was created, set the role to 'admin'
                profile.role = 'admin'
                profile.save()
            else:
                # If the profile already exists, update the role to 'admin'
                profile.role = 'admin'
                profile.save()

            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')

    return render(request, 'admin/admin_register.html')

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
    user = request.user
    user_profile = user.profile
    profile = user.profile
    
    profile_picture_url = profile.get_profile_image()
    workspace = Workspace.objects.filter(user=request.user)

    selected_workspace_id = request.GET.get('workspace')
    selected_workspace = None

    if selected_workspace_id:
       selected_workspace = Workspace.objects.filter(id=selected_workspace_id, user=request.user).first()
       if selected_workspace:
           user.profile.selected_workspace = selected_workspace
           user.profile.save()

    return render(request, 'dashboard.html', {'user_profile': user_profile, 'workspace': workspace, 'profile_picture_url': profile_picture_url, 'selected_workspace': selected_workspace})

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

@login_required
def workspace(request):
    user = request.user
    profile = user.profile

    profile_picture_url = profile.get_profile_image()
    workspace = Workspace.objects.filter(user=request.user)

    return render(request, "workspace.html", {'user': request.user, 'workspace': workspace, 'profile_picture_url': profile_picture_url})

@login_required
def add_workspace(request):
    if request.method == 'POST':
        form = WorkspaceForm(request.POST)
        if form.is_valid():
            # Save the workspace but don't commit to DB yet
            workspace = form.save(commit=False)
            workspace.user = request.user
            workspace.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Return a JSON response for AJAX request
                return JsonResponse({
                    'success': True,
                    'message': 'Workspace created successfully!',
                    'workspace': {
                        'id': workspace.id,
                        'name': workspace.name,
                        'description': workspace.description
                    }
                })

            workspaces = Workspace.objects.all().order_by('-id')
            return render(request, 'workspace.html', {'workspace': workspaces, 'form': form})

        else:
            # Log form errors if any
            print("Form errors:", form.errors)  # For debugging purposes
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': form.errors})
            else:
                return render(request, 'workspace.html', {'form': form})
    else:
        form = WorkspaceForm()

    workspaces = Workspace.objects.all().order_by('-id')
    return render(request, 'workspace.html', {'form': form, 'workspace': workspaces})

@login_required
def update_account(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=user)  # Handle file upload

        if form.is_valid():
            # Save the user profile and handle image upload to Supabase within the form save method
            form.save()

            # check if the user uploaded a new profile image
            profile_picture_url = profile.get_profile_image()

            if request.FILES.get('profile_image'):  # Check if a new image was uploaded
                profile_picture = request.FILES['profile_image']

                # Upload image to Supabase Storage
                supabase_url = settings.SUPABASE_URL
                supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY
                supabase: Client = create_client(supabase_url, supabase_key)

                # Generate a unique file name and upload the file
                file_name = f"profile_images/{user.id}_{profile_picture.name}"
                file_data = profile_picture.read()

                # Upload to Supabase storage
                bucket_name = "soilution-storage"
                response = supabase.storage.from_(bucket_name).upload(file_name, file_data)

                if hasattr(response, 'full_path'):  # If upload was successful, save the URL
                    profile.profile_image = f"{supabase_url}/storage/v1/object/public/{response.full_path}"
                    profile.save()

            messages.success(request, "Your account has been updated successfully!")
            return redirect('account_settings')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=user)

    # Get the profile picture URL (from Profile model)
    profile_picture_url = profile.get_profile_image()

    context = {
        'form': form,
        'user': user,
        'profile_picture_url': profile_picture_url,
    }

    return render(request, 'account_settings.html', context)

# def workspace_data(request, id):
#     workspace = get_object_or_404(Workspace, id=id)
#     # Return the workspace data as JSON
#     data = {
#         'name': workspace.name,
#         'description': workspace.description,
#         # Add other fields you need to update dynamically
#     }
#     return JsonResponse(data)
