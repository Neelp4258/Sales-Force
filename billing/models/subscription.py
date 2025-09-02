"""
Subscription model for billing module
"""
from django.db import models
from django.utils import timezone
import uuid


class Subscription(models.Model):
    """Tenant subscription management"""
    
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('cancelled', 'Cancelled'),
        ('paused', 'Paused'),
    ]
    
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField('tenants.Tenant', on_delete=models.CASCADE, related_name='subscription')
    
    # Plan Details
    plan_name = models.CharField(max_length=50)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='monthly')
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    
    # Dates
    start_date = models.DateTimeField(default=timezone.now)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    trial_end_date = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Payment Gateway References
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    razorpay_subscription_id = models.CharField(max_length=255, blank=True)
    razorpay_customer_id = models.CharField(max_length=255, blank=True)
    
    # Payment Method
    payment_gateway = models.CharField(
        max_length=20,
        choices=[('stripe', 'Stripe'), ('razorpay', 'Razorpay')],
        blank=True
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.tenant.name} - {self.plan_name}"
    
    @property
    def is_active(self):
        """Check if subscription is active"""
        return self.status in ['trial', 'active'] and self.current_period_end > timezone.now()
    
    @property
    def days_until_renewal(self):
        """Calculate days until renewal"""
        if self.is_active:
            return (self.current_period_end - timezone.now()).days
        return 0
    
    def cancel(self):
        """Cancel subscription"""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()
        
        # Update tenant status
        self.tenant.subscription_status = 'cancelled'
        self.tenant.save()


class SubscriptionInvoice(models.Model):
    """Subscription invoices"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='invoices')
    
    # Invoice Details
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    
    # Dates
    invoice_date = models.DateField()
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment Gateway References
    stripe_invoice_id = models.CharField(max_length=255, blank=True)
    razorpay_invoice_id = models.CharField(max_length=255, blank=True)
    
    # Period
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Subscription Invoice'
        verbose_name_plural = 'Subscription Invoices'
        ordering = ['-invoice_date']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.subscription.tenant.name}"