"""
Deal and DealProduct models for sales module
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Deal(models.Model):
    """Deal/Opportunity model for sales pipeline"""
    
    STAGE_CHOICES = [
        ('prospect', 'Prospect'),
        ('qualification', 'Qualification'),
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('closed_won', 'Closed Won'),
        ('closed_lost', 'Closed Lost'),
    ]
    
    PROBABILITY_CHOICES = [
        (10, '10%'),
        (25, '25%'),
        (50, '50%'),
        (75, '75%'),
        (90, '90%'),
        (100, '100%'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deal_number = models.CharField(max_length=20, unique=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Relationships
    lead = models.ForeignKey('sales.Lead', on_delete=models.SET_NULL, null=True, blank=True, related_name='deals')
    customer = models.ForeignKey('sales.Customer', on_delete=models.CASCADE, related_name='deals')
    contact = models.ForeignKey(
        'sales.Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals'
    )
    
    # Deal Details
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='prospect')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    probability = models.IntegerField(choices=PROBABILITY_CHOICES, default=10)
    expected_close_date = models.DateField()
    
    # Competition
    competitors = models.TextField(blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_deals'
    )
    
    # Products/Services
    products = models.ManyToManyField('products.Product', through='DealProduct')
    
    # Tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_deals'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_date = models.DateTimeField(null=True, blank=True)
    
    # Lost Reason
    lost_reason = models.CharField(max_length=200, blank=True)
    lost_to_competitor = models.CharField(max_length=100, blank=True)
    
    # Tags
    tags = models.ManyToManyField('sales.Tag', blank=True)
    
    # Custom fields
    custom_fields = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Deal'
        verbose_name_plural = 'Deals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stage', '-created_at']),
            models.Index(fields=['assigned_to', 'stage']),
            models.Index(fields=['customer', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.deal_number} - {self.title}"
    
    @property
    def weighted_amount(self):
        """Calculate weighted amount based on probability"""
        return self.amount * (self.probability / 100)
    
    @property
    def days_in_pipeline(self):
        """Calculate days in pipeline"""
        if self.closed_date:
            return (self.closed_date - self.created_at).days
        return (timezone.now() - self.created_at).days
    
    def save(self, *args, **kwargs):
        if not self.deal_number:
            # Generate deal number
            last_deal = Deal.objects.order_by('-created_at').first()
            if last_deal and last_deal.deal_number:
                try:
                    last_num = int(last_deal.deal_number.split('-')[1])
                    self.deal_number = f"DEAL-{last_num + 1:05d}"
                except (IndexError, ValueError):
                    self.deal_number = "DEAL-00001"
            else:
                self.deal_number = "DEAL-00001"
        
        # Update closed date
        if self.stage in ['closed_won', 'closed_lost'] and not self.closed_date:
            self.closed_date = timezone.now()
        
        super().save(*args, **kwargs)


class DealProduct(models.Model):
    """Through model for Deal-Product relationship"""
    
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    
    class Meta:
        verbose_name = 'Deal Product'
        verbose_name_plural = 'Deal Products'
        unique_together = ['deal', 'product']
    
    @property
    def subtotal(self):
        return self.quantity * self.unit_price
    
    @property
    def discount_amount(self):
        return self.subtotal * (self.discount_percentage / 100)
    
    @property
    def taxable_amount(self):
        return self.subtotal - self.discount_amount
    
    @property
    def tax_amount(self):
        return self.taxable_amount * (self.tax_percentage / 100)
    
    @property
    def total(self):
        return self.taxable_amount + self.tax_amount