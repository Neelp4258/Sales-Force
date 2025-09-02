"""
Lead model for sales module
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()


class Lead(models.Model):
    """Lead/Prospect model"""
    
    # Lead Status
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('unqualified', 'Unqualified'),
        ('converted', 'Converted'),
        ('lost', 'Lost'),
    ]
    
    # Lead Source
    SOURCE_CHOICES = [
        ('website', 'Website'),
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('social_media', 'Social Media'),
        ('referral', 'Referral'),
        ('advertisement', 'Advertisement'),
        ('trade_show', 'Trade Show'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    secondary_phone = models.CharField(max_length=20, blank=True)
    
    # Company Information
    company_name = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=50, blank=True)
    annual_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Lead Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    source_details = models.CharField(max_length=200, blank=True)
    
    # Score and Priority
    lead_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='medium'
    )
    
    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads'
    )
    assigned_date = models.DateTimeField(null=True, blank=True)
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    
    # Additional Information
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_close_date = models.DateField(null=True, blank=True)
    
    # Social Media
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_leads'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Conversion
    converted_to_customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='original_lead'
    )
    converted_date = models.DateTimeField(null=True, blank=True)
    
    # Tags for categorization
    tags = models.ManyToManyField('sales.Tag', blank=True)
    
    # Custom fields (JSON for flexibility)
    custom_fields = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.company_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def days_since_creation(self):
        return (timezone.now() - self.created_at).days
    
    def convert_to_customer(self, user):
        """Convert lead to customer"""
        if self.status == 'converted':
            raise ValueError("Lead is already converted")
        
        from .customer import Customer
        
        customer = Customer.objects.create(
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            phone=self.phone,
            secondary_phone=self.secondary_phone,
            company_name=self.company_name,
            job_title=self.job_title,
            industry=self.industry,
            billing_address=self.address,
            billing_city=self.city,
            billing_state=self.state,
            billing_country=self.country,
            billing_postal_code=self.postal_code,
            created_by=user,
            lead_source=self.source,
            assigned_to=self.assigned_to,
        )
        
        self.converted_to_customer = customer
        self.converted_date = timezone.now()
        self.status = 'converted'
        self.save()
        
        return customer