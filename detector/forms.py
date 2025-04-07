from django import forms
from .models import Profile
from .models import Workspace
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.models import User
from supabase import create_client, Client
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

