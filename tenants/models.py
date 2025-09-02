"""
Multi-tenancy models for Ambivare ERP
"""
from django.db import models
from django.contrib.auth import get_user_model
from django_tenants.models import TenantMixin, DomainMixin
from django.utils import timezone
import uuid


class Tenant(TenantMixin):
    """
    Tenant model representing a company/organization
    """
    # Basic Information
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, unique=True)
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, default='India')
    postal_code = models.CharField(max_length=10, blank=True)
    
    # Subscription Information
    SUBSCRIPTION_STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('paused', 'Paused'),
    ]
    
    SUBSCRIPTION_PLAN_CHOICES = [
        ('starter', 'Starter'),
        ('pro', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    
    subscription_status = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_STATUS_CHOICES,
        default='trial'
    )
    subscription_plan = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_PLAN_CHOICES,
        default='starter'
    )
    
    # Billing Information
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    razorpay_customer_id = models.CharField(max_length=255, blank=True)
    razorpay_subscription_id = models.CharField(max_length=255, blank=True)
    
    # Subscription Dates
    trial_end_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    
    # Usage Limits (based on plan)
    max_users = models.IntegerField(default=5)
    max_leads = models.IntegerField(default=500)
    max_storage_mb = models.IntegerField(default=5120)  # 5GB default
    
    # Current Usage
    current_users = models.IntegerField(default=0)
    current_leads = models.IntegerField(default=0)
    current_storage_mb = models.IntegerField(default=0)
    
    # Settings
    timezone = models.CharField(max_length=50, default='UTC')
    currency = models.CharField(max_length=3, default='INR')
    fiscal_year_start = models.IntegerField(default=4)  # April
    
    # Metadata
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Features (JSON field for flexibility)
    enabled_features = models.JSONField(default=dict, blank=True)
    custom_settings = models.JSONField(default=dict, blank=True)
    
    # Company Logo
    logo = models.ImageField(upload_to='tenant_logos/', blank=True, null=True)
    
    # Tax Information
    tax_id = models.CharField(max_length=50, blank=True)  # GST/VAT number
    
    auto_create_schema = True
    auto_drop_schema = True
    
    class Meta:
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['-created_on']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.schema_name:
            self.schema_name = self.slug.replace('-', '_')
        
        # Set trial end date for new tenants
        if not self.pk and not self.trial_end_date:
            from django.conf import settings
            self.trial_end_date = timezone.now() + timezone.timedelta(days=settings.TRIAL_DAYS)
        
        super().save(*args, **kwargs)
    
    @property
    def is_on_trial(self):
        """Check if tenant is on trial"""
        return self.subscription_status == 'trial' and self.trial_end_date > timezone.now()
    
    @property
    def is_trial_expired(self):
        """Check if trial has expired"""
        return self.subscription_status == 'trial' and self.trial_end_date <= timezone.now()
    
    @property
    def can_add_users(self):
        """Check if tenant can add more users"""
        return self.max_users == -1 or self.current_users < self.max_users
    
    @property
    def can_add_leads(self):
        """Check if tenant can add more leads"""
        return self.max_leads == -1 or self.current_leads < self.max_leads
    
    @property
    def storage_usage_percentage(self):
        """Get storage usage percentage"""
        if self.max_storage_mb == 0:
            return 0
        return (self.current_storage_mb / self.max_storage_mb) * 100
    
    def has_feature(self, feature_name):
        """Check if tenant has access to a specific feature"""
        return self.enabled_features.get(feature_name, False)


class Domain(DomainMixin):
    """
    Domain model for tenant access
    """
    is_primary = models.BooleanField(default=True)
    ssl_enabled = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Domain'
        verbose_name_plural = 'Domains'
    
    def __str__(self):
        return self.domain


class TenantSettings(models.Model):
    """
    Additional settings for each tenant
    """
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='settings')
    
    # Email Settings
    email_signature = models.TextField(blank=True)
    auto_send_invoice = models.BooleanField(default=True)
    auto_send_reminder = models.BooleanField(default=True)
    reminder_days_before = models.IntegerField(default=3)
    
    # Invoice Settings
    invoice_prefix = models.CharField(max_length=10, default='INV')
    invoice_starting_number = models.IntegerField(default=1000)
    quote_prefix = models.CharField(max_length=10, default='QT')
    quote_starting_number = models.IntegerField(default=1000)
    
    # Tax Settings
    tax_name = models.CharField(max_length=20, default='GST')
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    
    # Lead Settings
    auto_assign_leads = models.BooleanField(default=False)
    lead_assignment_method = models.CharField(
        max_length=20,
        choices=[
            ('round_robin', 'Round Robin'),
            ('least_loaded', 'Least Loaded'),
            ('random', 'Random'),
        ],
        default='round_robin'
    )
    
    # Notification Settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    whatsapp_notifications = models.BooleanField(default=False)
    
    # Working Hours
    working_days = models.JSONField(default=list, blank=True)  # ['mon', 'tue', 'wed', 'thu', 'fri']
    working_hours_start = models.TimeField(default='09:00:00')
    working_hours_end = models.TimeField(default='18:00:00')
    
    # Theme Settings
    primary_color = models.CharField(max_length=7, default='#4F46E5')
    secondary_color = models.CharField(max_length=7, default='#7C3AED')
    
    class Meta:
        verbose_name = 'Tenant Settings'
        verbose_name_plural = 'Tenant Settings'


class TenantInvitation(models.Model):
    """
    Model to handle tenant invitations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    role = models.CharField(max_length=50)
    invited_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    token = models.CharField(max_length=100, unique=True)
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = 'Tenant Invitation'
        verbose_name_plural = 'Tenant Invitations'
        unique_together = ['tenant', 'email']
    
    def __str__(self):
        return f"Invitation to {self.email} for {self.tenant.name}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid.uuid4())
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)