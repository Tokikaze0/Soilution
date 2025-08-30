from django.shortcuts import render, redirect, get_object_or_404
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
from .models import Workspace
from allauth.socialaccount.models import SocialAccount
from django.http import JsonResponse
from supabase import create_client, Client
from .forms import UserProfileForm
from .models import Profile
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.http import urlencode
from .forms import LoginForm, RegisterForm
from .models import Message
from .forms import MessageForm
from .forms import CreateUserForm
from .forms import UpdateUserForm
from django.utils.timesince import timesince
from django.db.models import Max, Count, Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_protect
import time
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import EmailMultiAlternatives
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from tensorflow import keras
import numpy as np
import os
import joblib
from django.utils.dateformat import DateFormat
from django.utils.formats import get_format
from .services import CropRecommendationService, SoilAnalysisService


supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

channel_layer = get_channel_layer()

# Initialize services
crop_service = CropRecommendationService()
soil_service = SoilAnalysisService()

def is_admin(user):
    return user.is_authenticated and user.profile.role == 'admin'

def index(request):
    list(messages.get_messages(request))
    return render(request, 'detector/index.html')

def about(request):
    return render(request, 'detector/about.html')

def services(request):
    return render(request, 'detector/services.html')

def contact_support(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if not all([name, email, subject, message]):
            messages.error(request, "All fields are required.")
            return redirect('support')

        # Clean and format the email content
        email_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px;">
                    <h2 style="color: #000; margin-bottom: 20px;">New Customer Support Message</h2>
                    
                    <p><strong>Sender Name:</strong> {name}</p>
                    <p><strong>Email Address:</strong> {email}</p>
                    <p><strong>Subject:</strong> {subject}</p>
                    
                    <hr style="margin: 24px 0;" />
                    
                    <p><strong>Message:</strong></p>
                    <p style="white-space: pre-wrap;">{message}</p>
                </div>
                </body>
            </html>
        """

        email_subject = f"Support Inquiry: {subject}"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [settings.DEFAULT_FROM_EMAIL]

        email_msg = EmailMultiAlternatives(subject=email_subject, body=message, from_email=from_email, to=to_email)
        email_msg.attach_alternative(email_content, "text/html")
        email_msg.send()

        messages.success(request, "Your message has been sent. We’ll be in touch soon!")
        return redirect('contact_support')

    return render(request, 'detector/support.html')

def insights(request):
    user = request.user
    profile = user.profile
    profile_picture_url = profile.get_profile_image()

    user_workspaces = Workspace.objects.filter(user=user)

    selected_workspace = None
    selected_workspace_id = request.session.get('selected_workspace_id')

    if selected_workspace_id:
        try:
            selected_workspace = Workspace.objects.get(id=selected_workspace_id, user=user)
        except Workspace.DoesNotExist:
            del request.session['selected_workspace_id']

    if not selected_workspace:
        selected_workspace = user_workspaces.first()
        if selected_workspace:
            request.session['selected_workspace_id'] = selected_workspace.id

    context = {
        'profile_picture_url': profile_picture_url,
        'workspace': user_workspaces,
        'selected_workspace': selected_workspace,
        'user': user,
    }

    return render(request, 'insight.html', context)

def crop_details(request):
    user = request.user
    profile = user.profile
    profile_picture_url = profile.get_profile_image()

    user_workspaces = Workspace.objects.filter(user=user)

    selected_workspace = None
    selected_workspace_id = request.session.get('selected_workspace_id')

    if selected_workspace_id:
        try:
            selected_workspace = Workspace.objects.get(id=selected_workspace_id, user=user)
        except Workspace.DoesNotExist:
            del request.session['selected_workspace_id']

    if not selected_workspace:
        selected_workspace = user_workspaces.first()
        if selected_workspace:
            request.session['selected_workspace_id'] = selected_workspace.id
            
    crop_details = {
        'apple': {
            'description': 'Apples thrive in cold, temperate regions.',
            'climate': 'Temperate',
            'soil': 'Well-drained loamy soil',
            'harvest_time': 'Late summer to early fall'
        },
        'banana': {
            'description': 'Bananas grow best in humid, tropical regions.',
            'climate': 'Tropical',
            'soil': 'Rich, well-drained loamy soil',
            'harvest_time': 'Year-round in tropical zones'
        },
        'Munggo': {
            'description': 'A pulse crop rich in protein.',
            'climate': 'Warm, semi-arid',
            'soil': 'Loamy or sandy loam',
            'harvest_time': '90–120 days after sowing'
        },
        'chickpea': {
            'description': 'Popular legume grown in cool, dry climates.',
            'climate': 'Cool and dry',
            'soil': 'Well-drained sandy loam',
            'harvest_time': '100–110 days after sowing'
        },
        'coconut': {
            'description': 'Perennial tropical crop for oil and water.',
            'climate': 'Tropical, high humidity',
            'soil': 'Sandy loam or coastal alluvial',
            'harvest_time': 'Every 45–60 days once matured'
        },
        'coffee': {
            'description': 'Popular beverage crop grown in shade.',
            'climate': 'Subtropical with rain',
            'soil': 'Rich, well-drained volcanic or loam',
            'harvest_time': '7–9 months after flowering'
        },
        'cotton': {
            'description': 'Fiber crop requiring dry climate.',
            'climate': 'Warm, dry',
            'soil': 'Black soil, alluvial',
            'harvest_time': '150–180 days after planting'
        },
        'grapes': {
            'description': 'Grown for wine, juice, and consumption.',
            'climate': 'Temperate to warm',
            'soil': 'Sandy loam with good drainage',
            'harvest_time': 'Late summer to early fall'
        },
        'dyut': {
            'description': 'Bast fiber crop used for textiles.',
            'climate': 'Warm and humid',
            'soil': 'Alluvial, loamy',
            'harvest_time': '100–120 days after sowing'
        },
        'kidneybeans': {
            'description': 'Protein-rich legume often used in soups and stews.',
            'climate': 'Warm',
            'soil': 'Loamy, well-drained',
            'harvest_time': '90–120 days'
        },
        'monggo': {
            'description': 'Cool-season legume used in dal and soups.',
            'climate': 'Cool and dry',
            'soil': 'Sandy loam to clay loam',
            'harvest_time': '110–120 days after sowing'
        },
        'mais': {
            'description': 'Widely grown cereal crop.',
            'climate': 'Warm and sunny',
            'soil': 'Fertile loam with good moisture',
            'harvest_time': '90–100 days'
        },
        'mango': {
            'description': 'Tropical fruit known as the "king of fruits."',
            'climate': 'Tropical and subtropical',
            'soil': 'Well-drained loamy soil',
            'harvest_time': 'Late spring to summer'
        },
        'mothbeans': {
            'description': 'Drought-resistant legume grown in dry areas.',
            'climate': 'Hot and dry',
            'soil': 'Sandy or loamy soil',
            'harvest_time': '70–90 days'
        },
        'mungbean': {
            'description': 'Commonly used pulse, green gram.',
            'climate': 'Warm and humid',
            'soil': 'Loamy soil',
            'harvest_time': '60–70 days'
        },
        'muskmelon': {
            'description': 'Sweet, juicy melon grown in summer.',
            'climate': 'Warm, dry',
            'soil': 'Sandy loam',
            'harvest_time': '75–100 days'
        },
        'orange': {
            'description': 'Citrus fruit rich in vitamin C.',
            'climate': 'Subtropical to tropical',
            'soil': 'Well-drained sandy loam',
            'harvest_time': 'Winter to early spring'
        },
        'papaya': {
            'description': 'Fast-growing tropical fruit.',
            'climate': 'Tropical and subtropical',
            'soil': 'Well-drained loamy soil',
            'harvest_time': '6–9 months after planting'
        },
        'pigeonpeas': {
            'description': 'Perennial legume for food and fodder.',
            'climate': 'Semi-arid',
            'soil': 'Sandy loam or black soil',
            'harvest_time': '150–200 days'
        },
        'pomegranate': {
            'description': 'Drought-resistant fruit crop.',
            'climate': 'Hot, dry summers and cool winters',
            'soil': 'Loamy or alluvial soil',
            'harvest_time': '5–7 months after flowering'
        },
        'rice': {
            'description': 'Staple cereal crop for billions.',
            'climate': 'Warm, wet (monsoon)',
            'soil': 'Clayey, loamy',
            'harvest_time': '100–180 days, varies by variety'
        },
        'watermelon': {
            'description': 'Juicy summer fruit with high water content.',
            'climate': 'Warm and dry',
            'soil': 'Sandy loam, well-drained',
            'harvest_time': '80–100 days'
        },
        'wheat': {
            'description': 'Major cereal crop for flour production.',
            'climate': 'Cool, dry',
            'soil': 'Loamy or clay loam',
            'harvest_time': '120–150 days'
        }
    }

    context = {
        'profile_picture_url': profile_picture_url,
        'workspace': user_workspaces,
        'selected_workspace': selected_workspace,
        'user': user,
        'crop_details': crop_details,
    }

    return render(request, 'crop_details.html', context)

def logs(request):
    user = request.user
    profile = user.profile
    profile_picture_url = profile.get_profile_image()

    user_workspaces = Workspace.objects.filter(user=user)

    selected_workspace = None
    selected_workspace_id = request.session.get('selected_workspace_id')

    if selected_workspace_id:
        try:
            selected_workspace = Workspace.objects.get(id=selected_workspace_id, user=user)
        except Workspace.DoesNotExist:
            del request.session['selected_workspace_id']

    if not selected_workspace:
        selected_workspace = user_workspaces.first()
        if selected_workspace:
            request.session['selected_workspace_id'] = selected_workspace.id

    context = {
        'profile_picture_url': profile_picture_url,
        'workspace': user_workspaces,
        'selected_workspace': selected_workspace,
        'user': user,
    }

    return render(request, 'logs.html', context)

def reports(request):
    user = request.user
    profile = user.profile
    profile_picture_url = profile.get_profile_image()

    user_workspaces = Workspace.objects.filter(user=user)

    selected_workspace = None
    selected_workspace_id = request.session.get('selected_workspace_id')

    if selected_workspace_id:
        try:
            selected_workspace = Workspace.objects.get(id=selected_workspace_id, user=user)
        except Workspace.DoesNotExist:
            del request.session['selected_workspace_id']

    if not selected_workspace:
        selected_workspace = user_workspaces.first()
        if selected_workspace:
            request.session['selected_workspace_id'] = selected_workspace.id
            
    # Get real crop history from database
    crop_history = crop_service.get_user_crop_history(user, selected_workspace, limit=10)
    crop_history_data = []
    
    for history in crop_history:
        crop_history_data.append({
            "timestamp": history.recommendation_date.strftime("%Y-%m-%d %H:%M"),
            "crop": history.crop_name
        })

    context = {
        'profile_picture_url': profile_picture_url,
        'workspace': user_workspaces,
        'selected_workspace': selected_workspace,
        'user': user,
        'crop_history_json': json.dumps(crop_history_data),
    }

    return render(request, 'reports.html', context)

def login(request):
    list(messages.get_messages(request))
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.user
            if not user.is_active:
                messages.error(request, "Your account is not yet approved.")
                return redirect('pending_approval')
            auth_login(request, user)
            profile = user.profile
            if profile.role == 'admin':
                return redirect('admin_page')
            else:
                return redirect('workspace')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def register(request):
    list(messages.get_messages(request))  # Clear old messages

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = False  # Admin will activate it manually
            user.save()

            request.session['just_registered'] = True

            # messages.info(request, "Registration successful. Your account is pending admin approval.")
            return redirect('pending_approval')  # Or redirect to a 'pending approval' page
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

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

def pending_approval(request):   
    return render(request, 'pending_approval.html')

@login_required
def dashboard(request):
    # Clear any messages
    list(messages.get_messages(request))

    user = request.user
    profile = user.profile
    profile_picture_url = profile.get_profile_image()
    user_workspaces = Workspace.objects.filter(user=user)

    selected_workspace = None

    # Priority 1: Check if a workspace is passed via GET parameters
    workspace_id_from_get = request.GET.get('workspace')
    if workspace_id_from_get:
        try:
            selected_workspace = Workspace.objects.get(id=workspace_id_from_get, user=user)
            request.session['selected_workspace_id'] = selected_workspace.id  # Save it to session
        except Workspace.DoesNotExist:
            messages.error(request, "Selected workspace not found.")

    # Priority 2: If no GET param, check session for last selected workspace
    elif request.session.get('selected_workspace_id'):
        try:
            selected_workspace = Workspace.objects.get(id=request.session['selected_workspace_id'], user=user)
        except Workspace.DoesNotExist:
            del request.session['selected_workspace_id']
            selected_workspace = None

    # Priority 3: Fallback to first available workspace
    if not selected_workspace and user_workspaces.exists():
        selected_workspace = user_workspaces.first()
        request.session['selected_workspace_id'] = selected_workspace.id
        
    # Get real crop history from database
    crop_history = crop_service.get_user_crop_history(user, selected_workspace, limit=10)
    crop_history_data = []
    
    for history in crop_history:
        crop_history_data.append({
            "timestamp": history.recommendation_date.strftime("%Y-%m-%d %H:%M"),
            "crop": history.crop_name
        })
    
    # Get crop distribution for bar chart
    crop_distribution = {}
    for history in crop_history:
        crop_name = history.crop_name
        crop_distribution[crop_name] = crop_distribution.get(crop_name, 0) + 1
    
    # Convert to list format for chart
    crop_chart_data = [
        {"crop": crop, "count": count} 
        for crop, count in crop_distribution.items()
    ]

    context = {
        'user_profile': profile,
        'workspace': user_workspaces,
        'profile_picture_url': profile_picture_url,
        'selected_workspace': selected_workspace,
        'crop_history_json': json.dumps(crop_history_data),
        'crop_chart_data': json.dumps(crop_chart_data),
    }

    return render(request, 'dashboard.html', context)

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

            if len(password) < 8:
                passwords_have_error = True
                messages.error(request, 'Password must be at least 8 characters long')

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
    list(messages.get_messages(request))
    logout(request)
    return redirect('index')

@login_required
def workspace(request):
    list(messages.get_messages(request))
    user = request.user
    profile = user.profile

    profile_picture_url = profile.get_profile_image()
    workspace = Workspace.objects.filter(user=request.user)

    return render(request, "workspace.html", {'user': request.user, 'workspace': workspace, 'profile_picture_url': profile_picture_url})

@login_required
def add_workspace(request):
    list(messages.get_messages(request))
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
            # Form validation failed
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
    list(messages.get_messages(request))
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    # Grab the next param from GET or POST
    next_url = request.GET.get("next") or request.POST.get("next") or "/"
    # form_success = False
    # form_submitted = False

    if request.method == "POST":
        # form_submitted = True
        form = UserProfileForm(request.POST, request.FILES, instance=user)

        if form.is_valid():
            form.save()

            if request.FILES.get("profile_image"):
                profile_picture = request.FILES["profile_image"]
                supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

                file_name = f"profile_images/{user.id}_{profile_picture.name}"
                file_data = profile_picture.read()
                response = supabase.storage.from_("soilution-storage").upload(file_name, file_data)

                if hasattr(response, "full_path"):
                    profile.profile_image = f"{settings.SUPABASE_URL}/storage/v1/object/public/{response.full_path}"
                    profile.save()

            messages.success(request, "Your account has been updated successfully!")
            # form_success = True

            # Redirect with the ?next param preserved
            return redirect(f"{reverse('account_settings')}?{urlencode({'next': next_url})}")
        else:
            messages.error(request, "No space allowed. Please try again.")
        
    else:
        form = UserProfileForm(instance=user)

    profile_picture_url = profile.get_profile_image()

    context = {
        'form': form,
        'user': user,
        'profile_picture_url': profile_picture_url,
        'next': next_url,
    }

    # context = {
    #     "form": form,
    #     "user": user,
    #     "profile_picture_url": profile.get_profile_image(),
    #     "next": next_url,
    #     "form_success": form_success,
    #     "form_submitted": form_submitted,
    # }

    return render(request, 'account_settings.html', context)

def dashboard_settings(request):
    list(messages.get_messages(request))
    user = request.user
    profile = user.profile
    profile_picture_url = profile.get_profile_image()

    user_workspaces = Workspace.objects.filter(user=user)

    selected_workspace = None
    selected_workspace_id = request.session.get('selected_workspace_id')

    if selected_workspace_id:
        try:
            selected_workspace = Workspace.objects.get(id=selected_workspace_id, user=user)
        except Workspace.DoesNotExist:
            # Invalid ID — clear it
            del request.session['selected_workspace_id']

    if not selected_workspace:
        # Default to the first workspace if nothing valid is selected
        selected_workspace = user_workspaces.first()
        if selected_workspace:
            request.session['selected_workspace_id'] = selected_workspace.id

    context = {
        'profile_picture_url': profile_picture_url,
        'workspace': user_workspaces,
        'selected_workspace': selected_workspace,
        'user': user,
    }

    return render(request, 'dashboard_settings.html', context)

@login_required
def update_workspace(request):
    list(messages.get_messages(request))
    if request.method == 'POST':
        workspace_id = request.POST.get('workspace')
        name = request.POST.get('name')
        description = request.POST.get('description', '')

        if len(description) > 100:
            messages.error(request, 'Description must not exceed 100 characters.')
            return redirect('dashboard_settings')

        workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)

        workspace.name = name
        workspace.description = description
        workspace.save()

        messages.success(request, 'Workspace updated successfully!')
        return redirect('dashboard_settings')

    return redirect('dashboard_settings')

@login_required
def delete_workspace(request):
    list(messages.get_messages(request))
    if request.method == 'POST':
        workspace_id = request.POST.get('workspace')
        workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)
        workspace.delete()
        messages.success(request, 'Workspace deleted successfully.')
        return redirect('workspace')  # back to workspace list

    return redirect('dashboard_settings')

def set_workspace(request, workspace_id):
    list(messages.get_messages(request))
    workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)
    request.session['selected_workspace_id'] = workspace.id

    next_url = request.GET.get('next')
    host = request.get_host()

    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={host}):
        return redirect(next_url)

    return redirect('dashboard_s')

# ADMIN
@login_required
@user_passes_test(is_admin)
def admin_register(request):
    list(messages.get_messages(request))
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

        if len(password) < 8:
            user_data_has_error = True
            messages.error(request, "Password must be at least 8 characters")

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

            new_user.is_active = True
            new_user.is_staff = True  # Grant staff privileges
            new_user.save()

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

@login_required 
def admin_page(request):
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    pending_users = User.objects.filter(is_active=False).count()
    # New users in the current month
    now = timezone.now()
    start_of_month = now.replace(day=1)
    new_users_this_month = User.objects.filter(date_joined__gte=start_of_month).count()

    # Get messages sent to admin
    received_messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')[:10]
    unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()

    recent_messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')[:5]

    return render(request, 'admin/admin_page.html', {
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'new_users_this_month': new_users_this_month,
        'received_messages': received_messages,
        'unread_count': unread_count,
        'recent_messages': recent_messages,
        'pending_users': pending_users,
    })

@login_required
def admin_workspace(request):
    list(messages.get_messages(request))
    user = request.user
    profile = user.profile

    profile_picture_url = profile.get_profile_image()
    workspace = Workspace.objects.filter(user=request.user)

    return render(request, "admin/admin_workspace.html", {'user': request.user, 'workspace': workspace, 'profile_picture_url': profile_picture_url})

@login_required
def admin_dashboard(request):
    # Clear any messages
    list(messages.get_messages(request))

    user = request.user
    profile = user.profile
    profile_picture_url = profile.get_profile_image()
    user_workspaces = Workspace.objects.filter(user=user)

    selected_workspace = None

    # Priority 1: Check if a workspace is passed via GET parameters
    workspace_id_from_get = request.GET.get('workspace')
    if workspace_id_from_get:
        try:
            selected_workspace = Workspace.objects.get(id=workspace_id_from_get, user=user)
            request.session['selected_workspace_id'] = selected_workspace.id  # Save it to session
        except Workspace.DoesNotExist:
            messages.error(request, "Selected workspace not found.")

    # Priority 2: If no GET param, check session for last selected workspace
    elif request.session.get('selected_workspace_id'):
        try:
            selected_workspace = Workspace.objects.get(id=request.session['selected_workspace_id'], user=user)
        except Workspace.DoesNotExist:
            del request.session['selected_workspace_id']
            selected_workspace = None

    # Priority 3: Fallback to first available workspace
    if not selected_workspace and user_workspaces.exists():
        selected_workspace = user_workspaces.first()
        request.session['selected_workspace_id'] = selected_workspace.id

    context = {
        'user_profile': profile,
        'workspace': user_workspaces,
        'profile_picture_url': profile_picture_url,
        'selected_workspace': selected_workspace,
    }

    return render(request, 'admin/admin_dashboard.html', context)

def admin_insights(request):
    user = request.user
    profile = user.profile
    profile_picture_url = profile.get_profile_image()

    user_workspaces = Workspace.objects.filter(user=user)

    selected_workspace = None
    selected_workspace_id = request.session.get('selected_workspace_id')

    if selected_workspace_id:
        try:
            selected_workspace = Workspace.objects.get(id=selected_workspace_id, user=user)
        except Workspace.DoesNotExist:
            del request.session['selected_workspace_id']

    if not selected_workspace:
        selected_workspace = user_workspaces.first()
        if selected_workspace:
            request.session['selected_workspace_id'] = selected_workspace.id

    context = {
        'profile_picture_url': profile_picture_url,
        'workspace': user_workspaces,
        'selected_workspace': selected_workspace,
        'user': user,
    }

    return render(request, 'admin/admin_insight.html', context)

def admin_crop_details(request):
    user = request.user
    profile = user.profile
    profile_picture_url = profile.get_profile_image()

    user_workspaces = Workspace.objects.filter(user=user)

    selected_workspace = None
    selected_workspace_id = request.session.get('selected_workspace_id')

    if selected_workspace_id:
        try:
            selected_workspace = Workspace.objects.get(id=selected_workspace_id, user=user)
        except Workspace.DoesNotExist:
            del request.session['selected_workspace_id']

    if not selected_workspace:
        selected_workspace = user_workspaces.first()
        if selected_workspace:
            request.session['selected_workspace_id'] = selected_workspace.id

    context = {
        'profile_picture_url': profile_picture_url,
        'workspace': user_workspaces,
        'selected_workspace': selected_workspace,
        'user': user,
    }

    return render(request, 'admin/admin_crop_details.html', context)

def admin_logs(request):
    user = request.user
    profile = user.profile
    profile_picture_url = profile.get_profile_image()

    user_workspaces = Workspace.objects.filter(user=user)

    selected_workspace = None
    selected_workspace_id = request.session.get('selected_workspace_id')

    if selected_workspace_id:
        try:
            selected_workspace = Workspace.objects.get(id=selected_workspace_id, user=user)
        except Workspace.DoesNotExist:
            del request.session['selected_workspace_id']

    if not selected_workspace:
        selected_workspace = user_workspaces.first()
        if selected_workspace:
            request.session['selected_workspace_id'] = selected_workspace.id

    context = {
        'profile_picture_url': profile_picture_url,
        'workspace': user_workspaces,
        'selected_workspace': selected_workspace,
        'user': user,
    }

    return render(request, 'admin/admin_logs.html', context)

def admin_reports(request):
    user = request.user
    profile = user.profile
    profile_picture_url = profile.get_profile_image()

    user_workspaces = Workspace.objects.filter(user=user)

    selected_workspace = None
    selected_workspace_id = request.session.get('selected_workspace_id')

    if selected_workspace_id:
        try:
            selected_workspace = Workspace.objects.get(id=selected_workspace_id, user=user)
        except Workspace.DoesNotExist:
            del request.session['selected_workspace_id']

    if not selected_workspace:
        selected_workspace = user_workspaces.first()
        if selected_workspace:
            request.session['selected_workspace_id'] = selected_workspace.id

    context = {
        'profile_picture_url': profile_picture_url,
        'workspace': user_workspaces,
        'selected_workspace': selected_workspace,
        'user': user,
    }

    return render(request, 'admin/admin_reports.html', context)

def admin_dashboard_settings(request):
    list(messages.get_messages(request))
    user = request.user
    profile = user.profile
    profile_picture_url = profile.get_profile_image()

    user_workspaces = Workspace.objects.filter(user=user)

    selected_workspace = None
    selected_workspace_id = request.session.get('selected_workspace_id')

    if selected_workspace_id:
        try:
            selected_workspace = Workspace.objects.get(id=selected_workspace_id, user=user)
        except Workspace.DoesNotExist:
            # Invalid ID — clear it
            del request.session['selected_workspace_id']

    if not selected_workspace:
        # Default to the first workspace if nothing valid is selected
        selected_workspace = user_workspaces.first()
        if selected_workspace:
            request.session['selected_workspace_id'] = selected_workspace.id

    context = {
        'profile_picture_url': profile_picture_url,
        'workspace': user_workspaces,
        'selected_workspace': selected_workspace,
        'user': user,
    }

    return render(request, 'admin/admin_dashboard_settings.html', context)

@user_passes_test(is_admin)
def pending_users(request):
    if request.user.is_authenticated:
        users_qs = User.objects.filter(is_active=False)
        users = users_qs.values('username', 'email')
        count = users_qs.count()
        return JsonResponse({
            'count': count,
            'users': list(users)
        })
    return JsonResponse({'count': 0, 'users': []}, status=401)

@login_required
@user_passes_test(is_admin)
def pending_accounts(request):
    pending_users = User.objects.filter(is_active=False)
    # return JsonResponse({'users': list(pending_users)})
    return render(request, 'admin/pending_accounts.html', {'users': pending_users})

@login_required
@user_passes_test(is_admin)
def get_pending_accounts(request):
    if request.method == "GET":
        # Fetch users with is_active=False (pending accounts)
        users = User.objects.filter(is_active=False)

        # Prepare data for the response
        data = [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'first_name': u.first_name,
            'last_name': u.last_name,
        } for u in users]

        # Return the response with user details and count
        return JsonResponse({
            'count': len(data),  # Number of pending users
            'users': data         # List of user details
        })

    # Return an error if the method is not GET
    return JsonResponse({'error': 'Invalid request'}, status=400)

@user_passes_test(is_admin)
def approve_account(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = True
    user.save()

    domain = 'localhost:8000'
    subject = "Your account has been approved!"
    message = render_to_string('account_approved.html', {
        'user': user,
        'domain': domain,
    })

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=message
    )

    return redirect('pending_accounts')

@login_required
@user_passes_test(is_admin)
def create_user(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)  # Don't save yet
            user.set_password(form.cleaned_data['password'])  # Hash the password
            user.save()  # Now save the user

            messages.success(request, 'User created successfully.')
            return redirect('user_list')
    else:
        form = CreateUserForm()

    return render(request, 'admin/create_user.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def view_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(Profile, user=user)

    return render(request, 'admin/view_user.html', {
        'user': user,
        'profile': profile,
        'profile_picture_url': profile.get_profile_image(),
    })

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('user_list')

    return render(request, 'admin/user_list.html', {'user': user})

@login_required
@user_passes_test(is_admin)
def user_list(request):
    # users = User.objects.all()
    users = User.objects.filter(profile__role='user')
    return render(request, 'admin/user_list.html', {'users': users})

# @login_required
# def deactivate_user(request, user_id):
#     user = get_object_or_404(User, id=user_id)
    
#     if request.method == 'POST':
#         user.is_active = False
#         user.save()
#         # Return JSON response with the updated status
#         return JsonResponse({'status': 'success', 'is_active': user.is_active})
#     else:
#         # Return an error if method is not POST
#         return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

# @login_required
# def activate_user(request, user_id):
#     user = get_object_or_404(User, id=user_id)
    
#     if request.method == 'POST':
#         user.is_active = True
#         user.save()
#         # Return JSON response with the updated status
#         return JsonResponse({'status': 'success', 'is_active': user.is_active})
#     else:
#         # Return an error if method is not POST
#         return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


#MESSAGES/INBOX
@login_required
def view_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    
    # Ensure user can only view messages they sent or received
    if message.sender != request.user and message.receiver != request.user:
        messages.error(request, "You don't have permission to view this message.")
        return redirect('workspace')

    # Only mark as read if it's the recipient's message and it's unread
    if message.receiver == request.user and not message.is_read:
        message.is_read = True
        message.save()

    return render(request, 'messages/message_details.html', {'message': message})

@login_required
def get_unread_count_and_messages(request):
    unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()

    recent_unread = list(
        Message.objects.filter(receiver=request.user, is_read=False)
        .select_related('sender__profile')  # Include profile
        .order_by('-timestamp')[:3]
    )
    recent_read = list(
        Message.objects.filter(receiver=request.user, is_read=True)
        .select_related('sender__profile')  # Include profile
        .order_by('-timestamp')[:2]
    )

    # Merge and limit total to 5
    recent_messages = recent_unread + recent_read
    recent_messages = recent_messages[:5]

    messages_data = []
    for msg in recent_messages:
        sender_profile = msg.sender.profile
        profile_image_url = sender_profile.get_profile_image()
        
        # Fallback initials if no avatar
        initials = f"{msg.sender.first_name[:1]}{msg.sender.last_name[:1]}".upper() \
            if msg.sender.first_name and msg.sender.last_name else msg.sender.username[:2].upper()

        messages_data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'content': msg.content[:50],
            'timestamp': timesince(msg.timestamp) + " ago",
            'is_read': msg.is_read,
            'sender_avatar': profile_image_url if profile_image_url else None,
            'sender_initials': initials,
        })

    return JsonResponse({
        'unread_count': unread_count,
        'messages': messages_data
    })

@login_required
def get_unread_conversations(request):
    user = request.user

    # Get the latest message per sender (Messenger style)
    latest_ids = (
        Message.objects
        .filter(receiver=user)
        .values('sender')
        .annotate(latest_id=Max('id'))
        .values_list('latest_id', flat=True)
    )

    messages = Message.objects.filter(id__in=latest_ids).select_related('sender__profile').order_by('-timestamp')

    conversations = []
    for msg in messages:
        sender = msg.sender
        sender_profile = getattr(sender, 'profile', None)
        profile_image_url = sender_profile.get_profile_image() if sender_profile else None

        initials = f"{sender.first_name[:1]}{sender.last_name[:1]}".upper() \
            if sender.first_name and sender.last_name else sender.username[:2].upper()

        unread_count = Message.objects.filter(sender=sender, receiver=user, is_read=False).count()

        conversations.append({
            'sender_id': sender.id,
            'sender': sender.username,
            'sender_avatar': profile_image_url,
            'sender_initials': initials,
            'last_message': msg.content[:50],
            'timestamp': timesince(msg.timestamp) + ' ago',
            'unread_count': unread_count
        })

    return JsonResponse({'conversations': conversations})

@login_required
def message_thread(request, user_id):
    user = request.user
    other = get_object_or_404(User, id=user_id)
    
    messages = Message.objects.filter(
        (Q(sender=user, receiver=other) | Q(sender=other, receiver=user))
    ).order_by('timestamp')

    messages_data = []
    for msg in messages:
        sender_profile = getattr(msg.sender, 'profile', None)
        sender_avatar = sender_profile.get_profile_image() if sender_profile else None

        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime("%b %d, %H:%M"),
            'is_sender': msg.sender == user,
            'sender_avatar': sender_avatar
        })

    return JsonResponse({'messages': messages_data})

@csrf_protect
@login_required
def send_message(request, receiver_id):
    if request.method == "POST" and request.user.is_authenticated:
        content = request.POST.get("message", "").strip()
        if not content:
            return JsonResponse({"status": "error", "error": "Empty message"})

        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return JsonResponse({"status": "error", "error": "User not found"})

        msg = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=content
        )

        # Format timestamp
        timestamp = timesince(msg.timestamp) + " ago"

        #  Get sender profile and avatar
        profile = getattr(request.user, 'profile', None)
        avatar_url = None

        if profile and profile.get_profile_image():
            avatar_url = profile.get_profile_image() + "?v=" + str(int(time.time()))

        # WebSocket payload
        message_data = {
            "sender_id": request.user.id,
            "sender": request.user.username,
            "content": msg.content,
            "timestamp": timestamp,
            "sender_avatar": avatar_url,
        }

        # Send to receiver's WebSocket group
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{receiver.id}",  # 👈 Receiver group name
            {
                "type": "new_message",
                "message": message_data,
            }
        )

        return JsonResponse({
            "status": "ok",
            "message": {
                "sender_id": request.user.id,
                "sender": request.user.username,
                "content": msg.content,
                "timestamp": timestamp,
                "sender_avatar": avatar_url,
            }
        })

@login_required
def load_conversation(request, sender_id):
    current_user = request.user
    other_user = get_object_or_404(User, id=sender_id)

    # Get messages between current_user and other_user
    messages = Message.objects.filter(
        (Q(sender=current_user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=current_user))
    ).order_by('timestamp')

    message_data = []
    for msg in messages:
         # Safely get the sender's profile and avatar
        sender_profile = getattr(msg.sender, 'profile', None)
        sender_avatar = sender_profile.get_profile_image() if sender_profile else None

        message_data.append({
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%b %d, %H:%M'),
            'sender_id': msg.sender.id,
            'sender': msg.sender.username,
            'is_sender': msg.sender.id == current_user.id,
            'sender_avatar': sender_avatar
        })

    return JsonResponse({'messages': message_data})

@login_required
def mark_messages_as_read(request, sender_id):
    Message.objects.filter(receiver=request.user, sender_id=sender_id, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})

@login_required
def get_admin_users(request):
    # Get all users with the 'admin' role
    admins = User.objects.filter(profile__role='admin')
    admin_data = []
    
    for admin in admins:
        admin_data.append({
            'id': admin.id,
            'username': admin.username,
            'profile_image': admin.profile.get_profile_image() if admin.profile else None,
        })
    
    return JsonResponse({'admins': admin_data})

@login_required
def analyze_soil(request):
    """
    API endpoint to analyze soil data and provide crop recommendations.
    Expects a POST request with JSON body containing soil parameters.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            # Extract soil parameters
            nitrogen = data.get('nitrogen')
            phosphorus = data.get('phosphorus')
            potassium = data.get('potassium')
            temperature = data.get('temperature')
            moisture = data.get('moisture')
            ph = data.get('ph')
            conductivity = data.get('conductivity')
            
            # Validate required parameters
            if not all([nitrogen, phosphorus, potassium, temperature, moisture, ph, conductivity]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'All soil parameters are required'
                }, status=400)
            
            # Get crop recommendations using the service
            recommendations = crop_service.get_crop_recommendations(
                nitrogen=nitrogen,
                phosphorus=phosphorus,
                potassium=potassium,
                temperature=temperature,
                moisture=moisture,
                ph=ph,
                conductivity=conductivity
            )
            
            # Get soil analysis using the service
            soil_analysis = soil_service.analyze_soil(
                nitrogen=nitrogen,
                phosphorus=phosphorus,
                potassium=potassium,
                temperature=temperature,
                moisture=moisture,
                ph=ph,
                conductivity=conductivity
            )
            
            return JsonResponse({
                'status': 'success',
                'soil_analysis': soil_analysis,
                'crop_recommendations': recommendations
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Only POST requests are allowed'
    }, status=405)

@login_required
def get_crop_history(request):
    """
    API endpoint to get crop recommendation history for the authenticated user.
    """
    try:
        user = request.user
        workspace_id = request.GET.get('workspace_id')
        
        # Get workspace if specified, otherwise use default
        workspace = None
        if workspace_id:
            try:
                workspace = Workspace.objects.get(id=workspace_id, user=user)
            except Workspace.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Workspace not found'
                }, status=404)
        
        # Get crop history using the service
        crop_history = crop_service.get_user_crop_history(user, workspace, limit=50)
        
        # Format the data
        history_data = []
        for history in crop_history:
            history_data.append({
                'id': history.id,
                'crop_name': history.crop_name,
                'confidence': history.confidence,
                'recommendation_date': history.recommendation_date.strftime('%Y-%m-%d %H:%M:%S'),
                'soil_parameters': {
                    'nitrogen': history.nitrogen,
                    'phosphorus': history.phosphorus,
                    'potassium': history.potassium,
                    'temperature': history.temperature,
                    'moisture': history.moisture,
                    'ph': history.ph,
                    'conductivity': history.conductivity
                }
            })
        
        return JsonResponse({
            'status': 'success',
            'crop_history': history_data,
            'total_count': len(history_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
def get_workspace_stats(request):
    """
    API endpoint to get statistics for a specific workspace.
    """
    try:
        user = request.user
        workspace_id = request.GET.get('workspace_id')
        
        if not workspace_id:
            return JsonResponse({
                'status': 'error',
                'message': 'workspace_id parameter is required'
            }, status=400)
        
        # Get workspace
        try:
            workspace = Workspace.objects.get(id=workspace_id, user=user)
        except Workspace.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Workspace not found'
            }, status=404)
        
        # Get statistics using the services
        crop_history = crop_service.get_user_crop_history(user, workspace, limit=100)
        soil_analyses = soil_service.get_user_soil_analyses(user, workspace, limit=100)
        
        # Calculate statistics
        total_analyses = len(crop_history)
        unique_crops = len(set([h.crop_name for h in crop_history]))
        
        # Most recommended crop
        crop_counts = {}
        for history in crop_history:
            crop_counts[history.crop_name] = crop_counts.get(history.crop_name, 0) + 1
        
        most_recommended = max(crop_counts.items(), key=lambda x: x[1]) if crop_counts else None
        
        # Average confidence
        avg_confidence = sum([h.confidence for h in crop_history]) / len(crop_history) if crop_history else 0
        
        # Recent activity (last 7 days)
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)
        recent_analyses = len([h for h in crop_history if h.recommendation_date > week_ago])
        
        stats = {
            'total_analyses': total_analyses,
            'unique_crops': unique_crops,
            'most_recommended_crop': {
                'crop_name': most_recommended[0],
                'count': most_recommended[1]
            } if most_recommended else None,
            'average_confidence': round(avg_confidence, 2),
            'recent_analyses_7_days': recent_analyses,
            'workspace_name': workspace.name,
            'workspace_description': workspace.description
        }
        
        return JsonResponse({
            'status': 'success',
            'workspace_stats': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def esp32_data_api(request):
    """
    API endpoint to receive JSON data from ESP32.
    Expects a POST request with JSON body containing:
    moisture, temperature, conductivity, pH, nitrogen, phosphorus, potassium
    Returns the received data and crop recommendations, and saves to database.
    """
    if request.method == 'POST':
        try:
            # Validate content type
            if request.content_type != 'application/json':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Content-Type must be application/json'
                }, status=400)
            
            # Limit request size to prevent DoS
            if len(request.body) > 1024:  # 1KB limit
                return JsonResponse({
                    'status': 'error',
                    'message': 'Request too large'
                }, status=413)
            
            data = json.loads(request.body.decode('utf-8'))
            
            # Extract fields from the JSON payload
            moisture = data.get('moisture')
            temperature = data.get('temperature')
            conductivity = data.get('conductivity')
            pH = data.get('pH')
            nitrogen = data.get('nitrogen')
            phosphorus = data.get('phosphorus')
            potassium = data.get('potassium')

            # Validate required parameters
            if not all([moisture, temperature, conductivity, pH, nitrogen, phosphorus, potassium]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'All soil parameters are required'
                }, status=400)
            
            # Validate data types and ranges
            try:
                moisture = float(moisture)
                temperature = float(temperature)
                conductivity = float(conductivity)
                pH = float(pH)
                nitrogen = float(nitrogen)
                phosphorus = float(phosphorus)
                potassium = float(potassium)
            except (ValueError, TypeError):
                return JsonResponse({
                    'status': 'error',
                    'message': 'All parameters must be numeric values'
                }, status=400)
            
            # Validate reasonable ranges
            if not (0 <= moisture <= 100):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Moisture must be between 0 and 100'
                }, status=400)
            
            if not (-50 <= temperature <= 100):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Temperature must be between -50 and 100'
                }, status=400)
            
            if not (0 <= pH <= 14):
                return JsonResponse({
                    'status': 'error',
                    'message': 'pH must be between 0 and 14'
                }, status=400)

            # Convert ESP32 data to service format (note: services expect 'humidity' and 'rainfall')
            # For now, we'll map moisture to humidity and set rainfall to 0
            soil_params = {
                'nitrogen': float(nitrogen),
                'phosphorus': float(phosphorus),
                'potassium': float(potassium),
                'temperature': float(temperature),
                'humidity': float(moisture),  # Map moisture to humidity
                'ph': float(pH),
                'rainfall': 0.0  # ESP32 doesn't provide rainfall, set to 0
            }

            # Get crop recommendations using the service
            recommendations = crop_service.get_crop_recommendations(
                nitrogen=soil_params['nitrogen'],
                phosphorus=soil_params['phosphorus'],
                potassium=soil_params['potassium'],
                temperature=soil_params['temperature'],
                moisture=soil_params['humidity'],  # Use humidity as moisture
                ph=soil_params['ph'],
                conductivity=conductivity
            )

            # Get soil analysis using the service
            soil_analysis = soil_service.analyze_soil(
                nitrogen=soil_params['nitrogen'],
                phosphorus=soil_params['phosphorus'],
                potassium=soil_params['potassium'],
                temperature=soil_params['temperature'],
                moisture=soil_params['humidity'],
                ph=soil_params['ph'],
                conductivity=conductivity
            )

            # Respond with success, echo the received data, and add recommendations
            return JsonResponse({
                'status': 'success',
                'received': {
                    'moisture': moisture,
                    'temperature': temperature,
                    'conductivity': conductivity,
                    'pH': pH,
                    'nitrogen': nitrogen,
                    'phosphorus': phosphorus,
                    'potassium': potassium,
                },
                'soil_analysis': soil_analysis,
                'crop_recommendations': recommendations
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON format'
            }, status=400)
        except Exception as e:
            # Log the error but don't expose internal details
            return JsonResponse({
                'status': 'error',
                'message': 'Internal server error'
            }, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed.'}, status=405)
    
