from django.db import models
from django.contrib.auth.models import User
# from django.contrib.auth.models import AbstractUser
from django.conf import settings
import uuid

class PasswordReset(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reset_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Password reset for {self.user.username} at {self.created_when}"
    
    class Meta:
        app_label = 'detector'

class Workspace(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, related_name='workspaces', on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-id']

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    profile_image = models.URLField(max_length=200, blank=True, null=True)
    role = models.CharField(max_length=50, choices=[('admin', 'Admin'), ('user', 'User')], default='user')

    def __str__(self):
        return f"Profile for {self.user.username} - {self.role}"

    def get_profile_image(self):
        return self.profile_image

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'Message from {self.sender} to {self.receiver}'

class SoilAnalysis(models.Model):
    """Model to store soil analysis data"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='soil_analyses')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='soil_analyses')
    
    # Soil parameters
    nitrogen = models.FloatField(help_text="Nitrogen content in soil (kg/ha)")
    phosphorus = models.FloatField(help_text="Phosphorus content in soil (kg/ha)")
    potassium = models.FloatField(help_text="Potassium content in soil (kg/ha)")
    temperature = models.FloatField(help_text="Temperature in Celsius")
    humidity = models.FloatField(help_text="Humidity percentage")
    ph = models.FloatField(help_text="pH value of soil")
    rainfall = models.FloatField(help_text="Rainfall in mm")
    
    # Analysis metadata
    analysis_date = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-analysis_date']
        verbose_name_plural = "Soil Analyses"
    
    def __str__(self):
        return f"Soil analysis for {self.user.username} on {self.analysis_date.strftime('%Y-%m-%d %H:%M')}"

class CropRecommendation(models.Model):
    """Model to store crop recommendations based on soil analysis"""
    soil_analysis = models.OneToOneField(SoilAnalysis, on_delete=models.CASCADE, related_name='crop_recommendation')
    recommended_crop = models.CharField(max_length=100)
    confidence_score = models.FloatField(help_text="ML model confidence score (0-1)")
    alternative_crops = models.JSONField(default=list, help_text="List of alternative crop recommendations")
    
    # Recommendation metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_implemented = models.BooleanField(default=False, help_text="Whether the recommendation was followed")
    implementation_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recommended_crop} recommendation for {self.soil_analysis.user.username}"
    
    def get_confidence_percentage(self):
        """Return confidence as percentage"""
        return round(self.confidence_score * 100, 1)

class CropHistory(models.Model):
    """Model to store historical crop recommendations for easy access"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crop_history')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='crop_history')
    crop_name = models.CharField(max_length=100)
    recommendation_date = models.DateTimeField(auto_now_add=True)
    soil_analysis = models.ForeignKey(SoilAnalysis, on_delete=models.CASCADE, related_name='crop_history')
    
    class Meta:
        ordering = ['-recommendation_date']
        verbose_name_plural = "Crop Histories"
    
    def __str__(self):
        return f"{self.crop_name} - {self.user.username} - {self.recommendation_date.strftime('%Y-%m-%d')}"

class SystemLog(models.Model):
    """Model to track system activities and admin actions"""
    LOG_TYPES = [
        ('user_registration', 'User Registration'),
        ('user_activation', 'User Activation'),
        ('user_deactivation', 'User Deactivation'),
        ('crop_recommendation', 'Crop Recommendation'),
        ('soil_analysis', 'Soil Analysis'),
        ('admin_action', 'Admin Action'),
        ('system_error', 'System Error'),
    ]
    
    log_type = models.CharField(max_length=50, choices=LOG_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='system_logs', null=True, blank=True)
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_actions', null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_log_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
