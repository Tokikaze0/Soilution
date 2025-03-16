from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email')
        print(f"Authenticating user with email: {username}")  
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
            else:
                print(f"Password mismatch for user: {username}")  
        except User.DoesNotExist:
            print(f"No user found for email: {username}") 
        return None
