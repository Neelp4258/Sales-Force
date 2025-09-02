"""
Integration models for Ambivare ERP
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings
import uuid
import json

User = get_user_model()


class Integration(models.Model):
    """Third-party integrations"""
    
    INTEGRATION_TYPE_CHOICES = [
        ('email', 'Email Provider'),
        ('sms', 'SMS Provider'),
        ('whatsapp', 'WhatsApp'),
        ('payment', 'Payment Gateway'),
        ('accounting', 'Accounting Software'),
        ('calendar', 'Calendar'),
        ('storage', 'Cloud Storage'),
        ('crm', 'CRM'),
        ('webhook', 'Webhook'),
        ('custom', 'Custom API'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('pending', 'Pending Setup'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_TYPE_CHOICES)
    provider = models.CharField(max_length=50)  # e.g., 'gmail', 'twilio', 'stripe'
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True)
    
    # Configuration (encrypted)
    config_data = models.TextField()  # Encrypted JSON
    
    # OAuth tokens (if applicable)
    access_token = models.TextField(blank=True)  # Encrypted
    refresh_token = models.TextField(blank=True)  # Encrypted
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Webhooks
    webhook_url = models.URLField(blank=True)
    webhook_secret = models.CharField(max_length=255, blank=True)
    
    # Usage Limits
    api_calls_limit = models.IntegerField(default=0)  # 0 = unlimited
    api_calls_used = models.IntegerField(default=0)
    limit_reset_date = models.DateTimeField(null=True, blank=True)
    
    # Error Tracking
    last_error = models.TextField(blank=True)
    last_error_at = models.DateTimeField(null=True, blank=True)
    error_count = models.IntegerField(default=0)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Integration'
        verbose_name_plural = 'Integrations'
        ordering = ['name']
        unique_together = ['provider', 'integration_type']
    
    def __str__(self):
        return f"{self.name} ({self.provider})"
    
    @property
    def is_token_expired(self):
        """Check if OAuth token is expired"""
        if self.token_expires_at:
            return timezone.now() > self.token_expires_at
        return False
    
    def encrypt_config(self, config_dict):
        """Encrypt configuration data"""
        fernet = Fernet(settings.ENCRYPTION_KEY.encode())
        json_str = json.dumps(config_dict)
        self.config_data = fernet.encrypt(json_str.encode()).decode()
    
    def decrypt_config(self):
        """Decrypt configuration data"""
        if not self.config_data:
            return {}
        fernet = Fernet(settings.ENCRYPTION_KEY.encode())
        decrypted = fernet.decrypt(self.config_data.encode())
        return json.loads(decrypted.decode())
    
    def log_error(self, error_message):
        """Log integration error"""
        self.last_error = error_message
        self.last_error_at = timezone.now()
        self.error_count += 1
        self.status = 'error'
        self.save()


class EmailTemplate(models.Model):
    """Email templates for notifications"""
    
    TEMPLATE_TYPE_CHOICES = [
        ('welcome', 'Welcome Email'),
        ('invoice', 'Invoice Email'),
        ('quotation', 'Quotation Email'),
        ('reminder', 'Payment Reminder'),
        ('task_assigned', 'Task Assignment'),
        ('lead_assigned', 'Lead Assignment'),
        ('password_reset', 'Password Reset'),
        ('custom', 'Custom Template'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    
    # Email Content
    subject = models.CharField(max_length=200)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    
    # Variables
    available_variables = models.JSONField(default=list)  # List of available template variables
    
    # Attachments
    include_pdf = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
        ordering = ['template_type', 'name']
        unique_together = ['template_type', 'is_default']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"
    
    def render(self, context):
        """Render template with context"""
        from django.template import Template, Context
        
        # Render subject
        subject_template = Template(self.subject)
        subject = subject_template.render(Context(context))
        
        # Render HTML content
        html_template = Template(self.html_content)
        html = html_template.render(Context(context))
        
        # Render text content
        text = ''
        if self.text_content:
            text_template = Template(self.text_content)
            text = text_template.render(Context(context))
        
        return {
            'subject': subject,
            'html': html,
            'text': text,
        }


class SMSTemplate(models.Model):
    """SMS templates"""
    
    TEMPLATE_TYPE_CHOICES = [
        ('otp', 'OTP'),
        ('reminder', 'Reminder'),
        ('notification', 'Notification'),
        ('marketing', 'Marketing'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    
    # Content
    message = models.TextField(max_length=160)  # SMS character limit
    
    # DLT Registration (for India)
    dlt_template_id = models.CharField(max_length=50, blank=True)
    
    # Variables
    available_variables = models.JSONField(default=list)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'SMS Template'
        verbose_name_plural = 'SMS Templates'
        ordering = ['template_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"


class WebhookEndpoint(models.Model):
    """Webhook endpoints for external integrations"""
    
    EVENT_CHOICES = [
        ('lead.created', 'Lead Created'),
        ('lead.updated', 'Lead Updated'),
        ('lead.converted', 'Lead Converted'),
        ('customer.created', 'Customer Created'),
        ('customer.updated', 'Customer Updated'),
        ('deal.created', 'Deal Created'),
        ('deal.updated', 'Deal Updated'),
        ('deal.won', 'Deal Won'),
        ('deal.lost', 'Deal Lost'),
        ('invoice.created', 'Invoice Created'),
        ('invoice.paid', 'Invoice Paid'),
        ('task.created', 'Task Created'),
        ('task.completed', 'Task Completed'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    url = models.URLField()
    
    # Events
    events = models.JSONField(default=list)  # List of subscribed events
    
    # Authentication
    secret_key = models.CharField(max_length=255)
    headers = models.JSONField(default=dict, blank=True)  # Additional headers
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Retry Configuration
    max_retries = models.IntegerField(default=3)
    retry_delay = models.IntegerField(default=60)  # seconds
    
    # Statistics
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Webhook Endpoint'
        verbose_name_plural = 'Webhook Endpoints'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def generate_signature(self, payload):
        """Generate webhook signature"""
        import hmac
        import hashlib
        
        return hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()


class WebhookLog(models.Model):
    """Webhook delivery logs"""
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name='logs')
    
    # Event
    event = models.CharField(max_length=50)
    payload = models.JSONField()
    
    # Delivery
    status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    response_headers = models.JSONField(default=dict, blank=True)
    
    # Status
    is_success = models.BooleanField(default=False)
    retry_count = models.IntegerField(default=0)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    response_time = models.IntegerField(null=True, blank=True)  # milliseconds
    
    class Meta:
        verbose_name = 'Webhook Log'
        verbose_name_plural = 'Webhook Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['webhook', '-created_at']),
            models.Index(fields=['event', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.webhook.name} - {self.event} - {self.created_at}"


class APIKey(models.Model):
    """API keys for external access"""
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=255, unique=True)
    
    # Permissions
    scopes = models.JSONField(default=list)  # List of allowed scopes
    
    # Rate Limiting
    rate_limit = models.IntegerField(default=1000)  # requests per hour
    
    # IP Restrictions
    allowed_ips = models.JSONField(default=list, blank=True)  # Empty = all IPs allowed
    
    # Status
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Usage
    last_used_at = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def is_expired(self):
        """Check if API key is expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def generate_key(self):
        """Generate a new API key"""
        import secrets
        self.key = f"ak_{secrets.token_urlsafe(32)}"
    
    def log_usage(self, ip_address=None):
        """Log API key usage"""
        self.last_used_at = timezone.now()
        self.usage_count += 1
        self.save()