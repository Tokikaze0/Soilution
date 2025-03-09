# from allauth.socialaccount.signals import social_account_added
# from django.contrib.auth import get_user_model
# from django.dispatch import receiver
# from django.shortcuts import redirect

# @receiver(social_account_added)
# def social_account_added_handler(sender, request, sociallogin, **kwargs):
#     user = sociallogin.user
#     if user and user.is_active:
#         # Ensure the user is logged in after linking the social account
#         from django.contrib.auth import login as auth_login
#         auth_login(request, user)
#         return redirect('dashboard')  # Redirect to the dashboard (or your preferred page)


# from allauth.socialaccount.signals import social_account_added
# from django.contrib.auth import login as auth_login
# from django.dispatch import receiver
# from django.shortcuts import redirect

# @receiver(social_account_added)
# def social_account_added_handler(sender, request, sociallogin, **kwargs):
#     user = sociallogin.user
#     if user and user.is_active:
#         # Check if the user already exists and if they are not a new user
#         try:
#             # You can get the user from the sociallogin instance if the email already exists
#             user_instance = user
#             if user_instance:
#                 # Log the user in manually after social login
#                 auth_login(request, user_instance)
#                 return redirect('dashboard')  # Redirect to your preferred page
#         except Exception as e:
#             pass  # You can add custom error handling if needed
#     else:
#         return redirect('login')  # If the user is not found or isn't active, redirect them to the signup page
