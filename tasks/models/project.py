"""
Project model for task management
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Project(models.Model):
    """Project model for grouping tasks"""
    
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_projects'
    )
    
    # Team
    team_members = models.ManyToManyField(
        User,
        related_name='projects',
        blank=True
    )
    
    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Color for UI
    color = models.CharField(max_length=7, default='#4F46E5')
    
    # Budget
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Client/Customer
    customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects'
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def progress_percentage(self):
        """Calculate project progress based on tasks"""
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        
        completed_tasks = self.tasks.filter(status='done').count()
        return int((completed_tasks / total_tasks) * 100)
    
    @property
    def is_overdue(self):
        """Check if project is overdue"""
        return (
            self.end_date and
            self.end_date < timezone.now().date() and
            self.status not in ['completed', 'cancelled']
        )
    
    @property
    def budget_usage_percentage(self):
        """Calculate budget usage percentage"""
        if self.budget and self.budget > 0:
            return (self.spent_amount / self.budget) * 100
        return 0
    
    @property
    def days_remaining(self):
        """Calculate days remaining"""
        if self.end_date:
            delta = self.end_date - timezone.now().date()
            return max(0, delta.days)
        return None