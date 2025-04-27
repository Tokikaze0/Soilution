from django import forms
from .models import Profile
from .models import Workspace
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.models import User
from supabase import create_client, Client
from allauth.socialaccount.models import SocialAccount
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from .models import Message
import logging

logger = logging.getLogger(__name__)

class WorkspaceForm(forms.ModelForm):
    class Meta:
        model = Workspace
        fields = ['name', 'description']

        description = forms.CharField(required=False, widget=forms.Textarea, max_length=100)

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']

    profile_picture = forms.ImageField(required=False) 

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()

        profile_picture = self.cleaned_data.get('profile_picture')

        if profile_picture:
            profile, created = Profile.objects.get_or_create(user=user)
            
            supabase_url = settings.SUPABASE_URL
            supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY
            supabase: Client = create_client(supabase_url, supabase_key)

            # Generate a unique file name for the profile image
            bucket_name = "soilution-storage"
            file_name = f"profile_image/{user.id}_{profile_picture.name}"

            # Upload the image to Supabase Storage
            file_data = profile_picture.read()
            response = supabase.storage.from_(bucket_name).upload(file_name, file_data)

            logger.error(f"Supabase upload response: {response}")

            if not hasattr(response, 'full_path') or response.full_path is None:
                raise ValueError(f"Error uploading profile picture to Supabase! Response: {response}")

            file_path = response.full_path if isinstance(response.full_path, str) else None
            if not file_path:
                raise ValueError(f"Error uploading profile picture to Supabase! Response: {response}")

            # Construct the public URL of the uploaded image
            public_url = f"{supabase_url}/storage/v1/object/public/{file_path}"

            # Save the image URL in the profile model
            profile.profile_image = public_url
            profile.save()

        return user 

class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'autocomplete': 'off',
            'required': True,
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'off',
            'required': True,
            'id': 'password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise forms.ValidationError({'email': "Invalid email"})

            social_account = SocialAccount.objects.filter(user=user, provider='google').first()
            if social_account:
                raise forms.ValidationError({'email': "This email is associated with google. Please log in using Google or reset your password."})

            user = authenticate(username=email, password=password)
            if user is None:
                raise forms.ValidationError({'password': "Invalid password"})

            if not user.is_active:
                raise forms.ValidationError("This account is inactive.")

            self.user = user  # attach user to the form for login in view
        return cleaned_data

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
        min_length=8,
        label="Password"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password') 
        if len(password) < 5:
            raise forms.ValidationError("Password must be at least 5 characters long.")

        # Add more custom rules if needed:
        # if not any(char.isdigit() for char in password):
        #     raise forms.ValidationError("Password must include at least one number.")

        return password

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Type your message...'})
        }

class CreateUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists.")
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 5:
            raise ValidationError("Password must be at least 5 characters long.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")

        return cleaned_data

class UpdateUserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    profile_image = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('instance', None)
        self.profile_instance = kwargs.pop('profile_instance', None)  # save profile instance
        super(UpdateUserForm, self).__init__(*args, instance=self.user_instance, **kwargs)

        if self.profile_instance:
            self.fields['profile_image'].initial = self.profile_instance.profile_image

    def clean_username(self):
        username = self.cleaned_data.get('username')
        existing_user = User.objects.filter(username=username).exclude(pk=self.user_instance.pk)
        if existing_user.exists():
            raise ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.user_instance.pk).exists():
            raise ValidationError("Email already in use.")
        return email

