from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    Profile, Workspace, Message, PasswordReset, 
    SoilAnalysis, CropRecommendation, CropHistory, SystemLog
)

# Unregister the default User admin to customize it
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined', 'get_role', 'get_workspace_count')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'profile__role')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Information', {'fields': ('profile',)}),
    )
    
    def get_role(self, obj):
        try:
            return obj.profile.role
        except Profile.DoesNotExist:
            return 'No Profile'
    get_role.short_description = 'Role'
    
    def get_workspace_count(self, obj):
        return obj.workspaces.count()
    get_workspace_count.short_description = 'Workspaces'
    
    actions = ['activate_users', 'deactivate_users', 'make_admin', 'make_user']
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users have been activated.')
        
        # Log the action
        for user in queryset:
            SystemLog.objects.create(
                log_type='user_activation',
                admin_user=request.user,
                user=user,
                description=f'User {user.username} activated by admin {request.user.username}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users have been deactivated.')
        
        # Log the action
        for user in queryset:
            SystemLog.objects.create(
                log_type='user_deactivation',
                admin_user=request.user,
                user=user,
                description=f'User {user.username} deactivated by admin {request.user.username}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
    deactivate_users.short_description = "Deactivate selected users"
    
    def make_admin(self, request, queryset):
        for user in queryset:
            profile, created = Profile.objects.get_or_create(user=user)
            profile.role = 'admin'
            profile.save()
        self.message_user(request, f'{queryset.count()} users have been made admin.')
    make_admin.short_description = "Make selected users admin"
    
    def make_user(self, request, queryset):
        for user in queryset:
            profile, created = Profile.objects.get_or_create(user=user)
            profile.role = 'user'
            profile.save()
        self.message_user(request, f'{queryset.count()} users have been made regular users.')
    make_user.short_description = "Make selected users regular users"

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'get_profile_image_display', 'get_user_status')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    ordering = ('user__username',)
    
    def get_profile_image_display(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.profile_image)
        return "No Image"
    get_profile_image_display.short_description = 'Profile Image'
    
    def get_user_status(self, obj):
        if obj.user.is_active:
            return format_html('<span style="color: green;">Active</span>')
        return format_html('<span style="color: red;">Inactive</span>')
    get_user_status.short_description = 'Status'

@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'description', 'created_at', 'get_analysis_count')
    list_filter = ('created_at',)
    search_fields = ('name', 'user__username', 'description')
    ordering = ('-created_at',)
    
    def get_analysis_count(self, obj):
        return obj.soil_analyses.count()
    get_analysis_count.short_description = 'Soil Analyses'

@admin.register(SoilAnalysis)
class SoilAnalysisAdmin(admin.ModelAdmin):
    list_display = ('user', 'workspace', 'nitrogen', 'phosphorus', 'potassium', 'temperature', 'humidity', 'ph', 'rainfall', 'analysis_date', 'location')
    list_filter = ('analysis_date', 'workspace', 'user')
    search_fields = ('user__username', 'workspace__name', 'location')
    ordering = ('-analysis_date',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'workspace', 'location', 'notes')
        }),
        ('Soil Parameters', {
            'fields': ('nitrogen', 'phosphorus', 'potassium', 'temperature', 'humidity', 'ph', 'rainfall')
        }),
        ('Metadata', {
            'fields': ('analysis_date',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('analysis_date',)
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Log the action
        SystemLog.objects.create(
            log_type='soil_analysis',
            admin_user=request.user if request.user.is_staff else None,
            user=obj.user,
            description=f'Soil analysis created/updated for {obj.user.username}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )

@admin.register(CropRecommendation)
class CropRecommendationAdmin(admin.ModelAdmin):
    list_display = ('soil_analysis', 'recommended_crop', 'confidence_score', 'get_confidence_percentage', 'is_implemented', 'created_at')
    list_filter = ('is_implemented', 'created_at', 'recommended_crop')
    search_fields = ('soil_analysis__user__username', 'recommended_crop')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Recommendation Details', {
            'fields': ('soil_analysis', 'recommended_crop', 'confidence_score', 'alternative_crops')
        }),
        ('Implementation', {
            'fields': ('is_implemented', 'implementation_notes')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Create or update crop history
        CropHistory.objects.update_or_create(
            soil_analysis=obj.soil_analysis,
            defaults={
                'user': obj.soil_analysis.user,
                'workspace': obj.soil_analysis.workspace,
                'crop_name': obj.recommended_crop,
            }
        )
        
        # Log the action
        SystemLog.objects.create(
            log_type='crop_recommendation',
            admin_user=request.user if request.user.is_staff else None,
            user=obj.soil_analysis.user,
            description=f'Crop recommendation created/updated: {obj.recommended_crop}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )

@admin.register(CropHistory)
class CropHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'workspace', 'crop_name', 'recommendation_date', 'get_soil_analysis_link')
    list_filter = ('recommendation_date', 'workspace', 'crop_name')
    search_fields = ('user__username', 'workspace__name', 'crop_name')
    ordering = ('-recommendation_date',)
    
    def get_soil_analysis_link(self, obj):
        if obj.soil_analysis:
            url = reverse('admin:detector_soilanalysis_change', args=[obj.soil_analysis.id])
            return format_html('<a href="{}">View Analysis</a>', url)
        return "No Analysis"
    get_soil_analysis_link.short_description = 'Soil Analysis'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content_preview', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'content')
    ordering = ('-timestamp',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ('user', 'reset_id', 'created_when')
    list_filter = ('created_when',)
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_when',)
    readonly_fields = ('reset_id', 'created_when')

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('log_type', 'user', 'admin_user', 'description_preview', 'ip_address', 'timestamp')
    list_filter = ('log_type', 'timestamp', 'admin_user')
    search_fields = ('user__username', 'admin_user__username', 'description')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
    
    def description_preview(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_preview.short_description = 'Description'
    
    def has_add_permission(self, request):
        return False  # Logs should only be created by the system
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs should not be editable

# Customize admin site
admin.site.site_header = "Soilution Admin Panel"
admin.site.site_title = "Soilution Admin"
admin.site.index_title = "Welcome to Soilution Administration"

# Add custom admin actions
def get_admin_stats():
    """Get statistics for admin dashboard"""
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    pending_users = User.objects.filter(is_active=False).count()
    total_analyses = SoilAnalysis.objects.count()
    total_recommendations = CropRecommendation.objects.count()
    
    # Recent activity (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_analyses = SoilAnalysis.objects.filter(analysis_date__gte=week_ago).count()
    recent_recommendations = CropRecommendation.objects.filter(created_at__gte=week_ago).count()
    
    return {
        'total_users': total_users,
        'active_users': active_users,
        'pending_users': pending_users,
        'total_analyses': total_analyses,
        'total_recommendations': total_recommendations,
        'recent_analyses': recent_analyses,
        'recent_recommendations': recent_recommendations,
    }
