from allauth.socialaccount.models import SocialAccount
from PIL import Image, ImageDraw, ImageFont
from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.dispatch import receiver
from supabase import create_client
from django.conf import settings
from .models import Profile
import random
import time
import io
import os

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Check if the user logged in via Google
        try:
            # Get the social account associated with the user
            social_account = SocialAccount.objects.get(user=instance)
            
            # If the provider is 'google', skip profile creation with initials
            if social_account.provider == 'google':
                print("User authenticated via Google. Skipping profile image creation.")
                
                # Get the Google profile image URL from the extra_data
                google_profile_image_url = social_account.extra_data.get('picture', None)

                # If there's a Google profile image, set it in the user's profile
                if google_profile_image_url:
                    profile = Profile.objects.create(user=instance)
                    profile.profile_image = google_profile_image_url  # Set Google profile image URL
                    profile.save()
                    print(f"Profile image set from Google: {google_profile_image_url}")
                    return  # Skip the rest of the profile creation process for Google users
                
        except SocialAccount.DoesNotExist:
            # If the user doesn't have a social account, continue with profile creation
            pass
        
        # Create the profile for non-Google users
        profile = Profile.objects.create(user=instance)
        
        # Handle initials more safely (this part will now only run for non-Google users)
        first_name_initial = instance.first_name[0] if instance.first_name else ''  # Check if first_name is not empty
        last_name_initial = instance.last_name[0] if instance.last_name else ''  # Check if last_name is not empty
        
        # Combine the initials and make them uppercase
        initials = (first_name_initial + last_name_initial).upper()
        
        # Create a profile image based on the initials
        img = Image.new('RGB', (100, 100), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        d = ImageDraw.Draw(img)
        font_path = os.path.join(settings.BASE_DIR, 'static/fonts/CheyenneSans-ExtraBold.otf')  # Path to your font file
        try:
            font = ImageFont.truetype(font_path, 40)  # Set a larger font size (e.g., 40)
        except IOError:
            font = ImageFont.load_default()

        # Position the initials at the center of the image
        width, height = d.textbbox((0, 0), initials, font=font)[2:4]  # Updated line
        d.text(((100 - width) / 2, (100 - height) / 2), initials, font=font, fill=(255, 255, 255))

        # Save the image to a file-like object
        img_byte_array = io.BytesIO()
        img.save(img_byte_array, format='PNG')
        img_byte_array.seek(0)

        # Now upload the image to Supabase Storage
        timestamp = int(time.time())
        file_name = f'profile_image/{instance.id}_{timestamp}_profile.png'
        bucket_name = 'soilution-storage'  # Replace with your bucket name

        # Upload image to Supabase storage bucket
        file_data = img_byte_array.read()
        response = supabase.storage.from_(bucket_name).upload(
            file_name, 
            file_data, 
        )

        # Print the response to debug its structure
        print(f"Supabase Response: {response}")

        # Check if the response contains necessary information
        if hasattr(response, 'full_path'):
            # Generate the public URL
            public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{response.full_path}"
            print(f"Generated Public URL: {public_url}")
            profile.profile_image = public_url  # Save the public URL of the image to the profile
            profile.save()
            print(f"Profile image uploaded successfully: {public_url}")
        else:
            # Handle error or unexpected response
            print(f"Error: {response}")

# @receiver(post_save, sender=User)
# def notify_user_approved(sender, instance, created, **kwargs):
#     if not created and instance.is_active:
#         # Assuming they weren't active before, to avoid repeat notifications
#         if instance._previous_is_active is False:
#             subject = "Your account has been approved!"
#             message = f"""
#                 Hi {instance.first_name},

#                 Good news! Your account has been approved by the admin. You can now log in using your email and password.

#                 Login here: http://localhost:8000/login

#                 Thanks,
#                 The Team
#                 """
#             send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email])

# @receiver(pre_save, sender=User)
# def store_previous_is_active(sender, instance, **kwargs):
#     if instance.pk:
#         previous = User.objects.get(pk=instance.pk)
#         instance._previous_is_active = previous.is_active
#     else:
#         instance._previous_is_active = None

