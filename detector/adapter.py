from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.contrib.auth import get_user_model

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def is_email_taken(self, email):
        """
        Return True if the email is already taken by a non-social user.
        """
        User = get_user_model()
        return User.objects.filter(email=email).exists()

    def pre_social_login(self, request, sociallogin):
        """
        Handle the logic before a social login is completed.
        """
        # If email is already taken, try to log the user in
        email = sociallogin.user.email
        if self.is_email_taken(email):
            # This will log the user in using the existing account if they are found
            existing_user = get_user_model().objects.get(email=email)
            sociallogin.user = existing_user  # Link the social login with the existing user
            return redirect('login')  # Redirect to login page if already linked
