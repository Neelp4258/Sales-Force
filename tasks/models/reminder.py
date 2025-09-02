"""
Reminder model for task management
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid

User = get_user_model()


class Reminder(models.Model):
    """Reminders for various objects"""
    
    REMINDER_TYPE_CHOICES = [
        ('task', 'Task Reminder'),
        ('activity', 'Activity Reminder'),
        ('invoice', 'Invoice Reminder'),
        ('custom', 'Custom Reminder'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Type
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE_CHOICES)
    
    # User
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    
    # Schedule
    remind_at = models.DateTimeField()
    
    # Related Object (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.CharField(max_length=255, null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Status
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Notification Channels
    send_email = models.BooleanField(default=True)
    send_sms = models.BooleanField(default=False)
    send_whatsapp = models.BooleanField(default=False)
    send_push = models.BooleanField(default=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Reminder'
        verbose_name_plural = 'Reminders'
        ordering = ['remind_at']
        indexes = [
            models.Index(fields=['user', 'is_sent', 'remind_at']),
            models.Index(fields=['remind_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def mark_as_sent(self):
        """Mark reminder as sent"""
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save()
    
    def mark_as_read(self):
        """Mark reminder as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()