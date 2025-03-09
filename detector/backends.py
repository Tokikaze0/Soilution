# from django.contrib.auth.models import User
# from django.contrib.auth.backends import ModelBackend

# class EmailBackend(ModelBackend):
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         try:
#             user = User.objects.get(email=username)
#             if user.check_password(password):
#                 return user
#         except User.DoesNotExist:
#             return None


from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend

# class EmailBackend(ModelBackend):
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         if username is None:
#             username = kwargs.get('email')
#         try:
#             user = User.objects.get(email=username)
#             if user.check_password(password):
#                 return user
#         except User.DoesNotExist:
#             return None

# in your custom backend, add debugging
class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email')
        print(f"Authenticating user with email: {username}")  # Debugging line
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
            else:
                print(f"Password mismatch for user: {username}")  # Debugging line
        except User.DoesNotExist:
            print(f"No user found for email: {username}")  # Debugging line
        return None

