"""
Activity model for sales module
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Activity(models.Model):
    """Activity tracking for leads, customers, and deals"""
    
    ACTIVITY_TYPE_CHOICES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('task', 'Task'),
        ('note', 'Note'),
        ('demo', 'Demo'),
        ('follow_up', 'Follow Up'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES)
    subject = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Related To (polymorphic)
    lead = models.ForeignKey('sales.Lead', on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    customer = models.ForeignKey('sales.Customer', on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    deal = models.ForeignKey('sales.Deal', on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    contact = models.ForeignKey('sales.Contact', on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    
    # Activity Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        default='medium'
    )
    
    # Schedule
    scheduled_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=30)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_activities'
    )
    
    # Location (for meetings)
    location = models.CharField(max_length=200, blank=True)
    
    # Outcome
    outcome = models.TextField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_activities'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Reminders
    reminder_minutes_before = models.IntegerField(default=15)
    reminder_sent = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['assigned_to', 'status', '-scheduled_date']),
            models.Index(fields=['scheduled_date']),
        ]
    
    def __str__(self):
        return f"{self.activity_type} - {self.subject}"
    
    @property
    def is_overdue(self):
        """Check if activity is overdue"""
        return self.status == 'planned' and self.scheduled_date < timezone.now()
    
    def complete(self):
        """Mark activity as completed"""
        self.status = 'completed'
        self.completed_date = timezone.now()
        self.save()