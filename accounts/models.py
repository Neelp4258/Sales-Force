"""
User and authentication models for Ambivare ERP
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class UserManager(BaseUserManager):
    """Custom user manager"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'super_admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model"""
    
    # Remove username field
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    # User roles
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),  # Platform admin
        ('admin', 'Admin'),              # Tenant admin
        ('manager', 'Manager'),          # Sales manager
        ('executive', 'Sales Executive'), # Sales executive
        ('viewer', 'Viewer'),            # Read-only access
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='executive')
    
    # Profile fields
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    # Settings
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    whatsapp_notifications = models.BooleanField(default=False)
    
    # Sales specific fields
    sales_target = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Manager relationship for sales hierarchy
    reports_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_members'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    @property
    def is_tenant_admin(self):
        return self.role in ['super_admin', 'admin']
    
    @property
    def is_manager(self):
        return self.role in ['super_admin', 'admin', 'manager']
    
    @property
    def can_manage_users(self):
        return self.role in ['super_admin', 'admin']
    
    @property
    def can_manage_billing(self):
        return self.role in ['super_admin', 'admin']
    
    @property
    def can_export_data(self):
        return self.role in ['super_admin', 'admin', 'manager']
    
    def has_module_perms(self, app_label):
        """Check if user has permissions for a specific module"""
        if self.is_superuser:
            return True
        
        # Define module permissions based on role
        module_permissions = {
            'admin': ['tenants', 'accounts', 'sales', 'products', 'billing', 'tasks', 'analytics', 'integrations'],
            'manager': ['accounts', 'sales', 'products', 'tasks', 'analytics'],
            'executive': ['sales', 'products', 'tasks'],
            'viewer': ['sales', 'products', 'analytics'],
        }
        
        return app_label in module_permissions.get(self.role, [])
    
    def get_permissions(self):
        """Get all permissions for the user based on role"""
        permissions = {
            'super_admin': {
                'users': ['create', 'read', 'update', 'delete'],
                'leads': ['create', 'read', 'update', 'delete', 'assign'],
                'customers': ['create', 'read', 'update', 'delete'],
                'deals': ['create', 'read', 'update', 'delete'],
                'products': ['create', 'read', 'update', 'delete'],
                'invoices': ['create', 'read', 'update', 'delete', 'send'],
                'reports': ['view', 'export'],
                'settings': ['view', 'update'],
                'billing': ['view', 'update'],
            },
            'admin': {
                'users': ['create', 'read', 'update', 'delete'],
                'leads': ['create', 'read', 'update', 'delete', 'assign'],
                'customers': ['create', 'read', 'update', 'delete'],
                'deals': ['create', 'read', 'update', 'delete'],
                'products': ['create', 'read', 'update', 'delete'],
                'invoices': ['create', 'read', 'update', 'delete', 'send'],
                'reports': ['view', 'export'],
                'settings': ['view', 'update'],
                'billing': ['view', 'update'],
            },
            'manager': {
                'users': ['read'],
                'leads': ['create', 'read', 'update', 'delete', 'assign'],
                'customers': ['create', 'read', 'update', 'delete'],
                'deals': ['create', 'read', 'update', 'delete'],
                'products': ['read'],
                'invoices': ['create', 'read', 'update', 'send'],
                'reports': ['view', 'export'],
                'settings': ['view'],
            },
            'executive': {
                'users': [],
                'leads': ['create', 'read', 'update'],
                'customers': ['create', 'read', 'update'],
                'deals': ['create', 'read', 'update'],
                'products': ['read'],
                'invoices': ['create', 'read'],
                'reports': ['view'],
                'settings': [],
            },
            'viewer': {
                'users': [],
                'leads': ['read'],
                'customers': ['read'],
                'deals': ['read'],
                'products': ['read'],
                'invoices': ['read'],
                'reports': ['view'],
                'settings': [],
            },
        }
        
        return permissions.get(self.role, {})


class UserActivity(models.Model):
    """Track user activities for audit trail"""
    
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('view', 'View'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    
    # Track what was affected
    model_name = models.CharField(max_length=50, blank=True)
    object_id = models.CharField(max_length=50, blank=True)
    
    # Request information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} - {self.created_at}"


class PasswordResetToken(models.Model):
    """Custom password reset token model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
    
    def __str__(self):
        return f"Password reset for {self.user.email}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid.uuid4())
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)


class EmailVerificationToken(models.Model):
    """Email verification token model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verification_tokens')
    token = models.CharField(max_length=100, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = 'Email Verification Token'
        verbose_name_plural = 'Email Verification Tokens'
    
    def __str__(self):
        return f"Email verification for {self.user.email}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid.uuid4())
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)