"""
Task model for task management
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid

User = get_user_model()


class Task(models.Model):
    """Task model for task management"""
    
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Status and Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_tasks'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks'
    )
    
    # Dates
    due_date = models.DateTimeField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    # Time Tracking
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Related Object (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.CharField(max_length=255, null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Project/Category
    project = models.ForeignKey(
        'tasks.Project',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tasks'
    )
    
    # Labels/Tags
    labels = models.ManyToManyField('tasks.TaskLabel', blank=True)
    
    # Recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True)  # daily, weekly, monthly
    recurrence_end_date = models.DateField(null=True, blank=True)
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_instances'
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Progress
    progress_percentage = models.IntegerField(default=0)
    
    # Notifications
    reminder_before_hours = models.IntegerField(default=24)
    reminder_sent = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-priority', 'due_date', '-created_at']
        indexes = [
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        return (
            self.due_date and
            self.due_date < timezone.now() and
            self.status not in ['done', 'cancelled']
        )
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        if self.due_date:
            delta = self.due_date - timezone.now()
            return delta.days
        return None
    
    def complete(self):
        """Mark task as completed"""
        self.status = 'done'
        self.completed_date = timezone.now()
        self.progress_percentage = 100
        self.save()
    
    def create_next_recurrence(self):
        """Create next recurring task instance"""
        if not self.is_recurring:
            return None
        
        # Calculate next due date based on pattern
        if self.recurrence_pattern == 'daily':
            next_due = self.due_date + timezone.timedelta(days=1)
        elif self.recurrence_pattern == 'weekly':
            next_due = self.due_date + timezone.timedelta(weeks=1)
        elif self.recurrence_pattern == 'monthly':
            next_due = self.due_date + timezone.timedelta(days=30)
        else:
            return None
        
        # Check if within recurrence end date
        if self.recurrence_end_date and next_due.date() > self.recurrence_end_date:
            return None
        
        # Create new task
        new_task = Task.objects.create(
            title=self.title,
            description=self.description,
            status='todo',
            priority=self.priority,
            assigned_to=self.assigned_to,
            assigned_by=self.assigned_by,
            due_date=next_due,
            estimated_hours=self.estimated_hours,
            project=self.project,
            is_recurring=True,
            recurrence_pattern=self.recurrence_pattern,
            recurrence_end_date=self.recurrence_end_date,
            parent_task=self.parent_task or self,
        )
        
        # Copy labels
        new_task.labels.set(self.labels.all())
        
        return new_task


class TaskComment(models.Model):
    """Comments on tasks"""
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    
    # Comment
    text = models.TextField()
    
    # Author
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Mentions
    mentions = models.ManyToManyField(User, related_name='mentioned_in_comments', blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Task Comment'
        verbose_name_plural = 'Task Comments'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.email} on {self.task.title}"


class TaskAttachment(models.Model):
    """Attachments for tasks and comments"""
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='task_attachments/')
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField()  # in bytes
    mime_type = models.CharField(max_length=100)
    
    # Uploader
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Task Attachment'
        verbose_name_plural = 'Task Attachments'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.filename


class TaskLabel(models.Model):
    """Labels for categorizing tasks"""
    
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6B7280')
    icon = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=200, blank=True)
    
    class Meta:
        verbose_name = 'Task Label'
        verbose_name_plural = 'Task Labels'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TaskTemplate(models.Model):
    """Task templates for recurring task types"""
    
    # Basic Information
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Template Details
    title_template = models.CharField(max_length=200)
    description_template = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10,
        choices=Task.PRIORITY_CHOICES,
        default='medium'
    )
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Default Assignment
    default_assignee_role = models.CharField(max_length=50, blank=True)
    
    # Labels
    labels = models.ManyToManyField(TaskLabel, blank=True)
    
    # Checklist
    checklist_items = models.JSONField(default=list, blank=True)
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Task Template'
        verbose_name_plural = 'Task Templates'
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return self.name
    
    def create_task(self, assigned_to, **kwargs):
        """Create a task from this template"""
        task = Task.objects.create(
            title=kwargs.get('title', self.title_template),
            description=kwargs.get('description', self.description_template),
            priority=kwargs.get('priority', self.priority),
            estimated_hours=kwargs.get('estimated_hours', self.estimated_hours),
            assigned_to=assigned_to,
            assigned_by=kwargs.get('assigned_by'),
            due_date=kwargs.get('due_date'),
            project=kwargs.get('project'),
        )
        
        # Copy labels
        task.labels.set(self.labels.all())
        
        # Increment usage count
        self.usage_count += 1
        self.save()
        
        return task