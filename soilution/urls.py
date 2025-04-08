from django.contrib import admin
from django.urls import path, include
from detector import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('social_django.urls', namespace='social')),
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('workspace/dashboard/insights/', views.insights, name='insights'),
    path('workspace/dashboard/crop_details/', views.crop_details, name='crop_details'),
    path('workspace/dashboard/logs/', views.logs, name='logs'),
    path('workspace/dashboard/reports/', views.reports, name='reports'),
    path('workspace/dashboard_settings/', views.dashboard_s, name='dashboard_s'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('admin_register/', views.admin_register, name='admin_register'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', views.logoutView, name='logout'),
    path('confirm-email/<uidb64>/<token>/', views.confirm_email, name='confirm_email'),
    path('verification_email/', views.verification_email, name='verification_email'),
    path('workspace/dashboard/', views.dashboard, name='dashboard'),
    path('workspace/', views.workspace, name='workspace'),
    path('add_workspace/', views.add_workspace, name='add_workspace'),
    # path('workspace/data/<int:id>/', views.workspace_data, name='workspace_data'),
    # path('profile/', views.profile, name='profile'),
    path('workspace/account/settings/', views.update_account, name='account_settings'),
    path('update_account/', views.update_account, name='update_account'),
    path('forgot-password/', views.ForgotPassword, name='forgot-password'),
    path('password-reset-sent/<str:reset_id>/', views.PasswordResetSent, name='password-reset-sent'),
    path('reset-password/<str:reset_id>/', views.ResetPassword, name='reset-password'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)