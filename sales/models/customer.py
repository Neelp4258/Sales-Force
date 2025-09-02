"""
Customer and Contact models for sales module
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Customer(models.Model):
    """Customer model"""
    
    CUSTOMER_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('company', 'Company'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_code = models.CharField(max_length=20, unique=True, blank=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES, default='company')
    
    # Contact Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    secondary_phone = models.CharField(max_length=20, blank=True)
    
    # Company Information
    company_name = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    
    # Address
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=50)
    billing_state = models.CharField(max_length=50)
    billing_country = models.CharField(max_length=50)
    billing_postal_code = models.CharField(max_length=10)
    
    # Shipping Address (can be different from billing)
    shipping_address = models.TextField(blank=True)
    shipping_city = models.CharField(max_length=50, blank=True)
    shipping_state = models.CharField(max_length=50, blank=True)
    shipping_country = models.CharField(max_length=50, blank=True)
    shipping_postal_code = models.CharField(max_length=10, blank=True)
    same_as_billing = models.BooleanField(default=True)
    
    # Tax Information
    tax_id = models.CharField(max_length=50, blank=True)  # GST/VAT number
    tax_exempt = models.BooleanField(default=False)
    
    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_customers'
    )
    
    # Customer Value
    lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_terms = models.IntegerField(default=30)  # Days
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Source
    lead_source = models.CharField(max_length=20, blank=True)
    
    # Tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_customers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Tags
    tags = models.ManyToManyField('sales.Tag', blank=True)
    
    # Custom fields
    custom_fields = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_code']),
            models.Index(fields=['email']),
            models.Index(fields=['company_name']),
        ]
    
    def __str__(self):
        return f"{self.customer_code} - {self.company_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self):
        if self.customer_type == 'company':
            return self.company_name
        return self.full_name
    
    def save(self, *args, **kwargs):
        if not self.customer_code:
            # Generate customer code
            last_customer = Customer.objects.order_by('-created_at').first()
            if last_customer and last_customer.customer_code:
                try:
                    last_num = int(last_customer.customer_code.split('-')[1])
                    self.customer_code = f"CUST-{last_num + 1:05d}"
                except (IndexError, ValueError):
                    self.customer_code = "CUST-00001"
            else:
                self.customer_code = "CUST-00001"
        
        super().save(*args, **kwargs)


class Contact(models.Model):
    """Contact model for customer contacts"""
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='contacts')
    
    # Contact Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    mobile = models.CharField(max_length=20, blank=True)
    
    # Job Information
    job_title = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True)
    
    # Status
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Communication Preferences
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('whatsapp', 'WhatsApp'),
        ],
        default='email'
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        ordering = ['-is_primary', 'first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.customer.company_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"