"""
Invoice model for billing module
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class Invoice(models.Model):
    """Invoice model"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True)
    
    # References
    customer = models.ForeignKey('sales.Customer', on_delete=models.PROTECT, related_name='invoices')
    deal = models.ForeignKey('sales.Deal', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    quotation = models.ForeignKey('billing.Quotation', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    
    # Dates
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Financial Details
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_type = models.CharField(
        max_length=10,
        choices=[('fixed', 'Fixed'), ('percentage', 'Percentage')],
        default='percentage'
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Payment Information
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Currency
    currency = models.CharField(max_length=3, default='INR')
    
    # Terms and Notes
    payment_terms = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Billing Address
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=50)
    billing_state = models.CharField(max_length=50)
    billing_country = models.CharField(max_length=50)
    billing_postal_code = models.CharField(max_length=10)
    
    # Shipping Address
    shipping_address = models.TextField(blank=True)
    shipping_city = models.CharField(max_length=50, blank=True)
    shipping_state = models.CharField(max_length=50, blank=True)
    shipping_country = models.CharField(max_length=50, blank=True)
    shipping_postal_code = models.CharField(max_length=10, blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Email Tracking
    sent_date = models.DateTimeField(null=True, blank=True)
    viewed_date = models.DateTimeField(null=True, blank=True)
    reminder_count = models.IntegerField(default=0)
    last_reminder_date = models.DateTimeField(null=True, blank=True)
    
    # Custom fields
    custom_fields = models.JSONField(default=dict, blank=True)
    
    # PDF
    pdf_file = models.FileField(upload_to='invoices/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['status', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer.display_name}"
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return self.status not in ['paid', 'cancelled', 'refunded'] and self.due_date < timezone.now().date()
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0
    
    @property
    def payment_percentage(self):
        """Calculate payment percentage"""
        if self.total_amount > 0:
            return (self.amount_paid / self.total_amount) * 100
        return 0
    
    def calculate_totals(self):
        """Calculate invoice totals"""
        # Calculate subtotal from items
        self.subtotal = sum(item.total for item in self.items.all())
        
        # Calculate discount
        if self.discount_type == 'fixed':
            self.discount_amount = min(self.discount_value, self.subtotal)
        else:
            self.discount_amount = self.subtotal * (self.discount_value / 100)
        
        # Calculate tax
        taxable_amount = self.subtotal - self.discount_amount
        self.tax_amount = sum(item.tax_amount for item in self.items.all())
        
        # Calculate total
        self.total_amount = taxable_amount + self.tax_amount
        self.amount_due = self.total_amount - self.amount_paid
        
        # Update status based on payment
        if self.amount_paid >= self.total_amount:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        elif self.is_overdue and self.status not in ['draft', 'cancelled']:
            self.status = 'overdue'
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number
            prefix = 'INV'
            
            # Get the last invoice number
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=prefix
            ).order_by('-created_at').first()
            
            if last_invoice:
                try:
                    last_num = int(last_invoice.invoice_number.split('-')[-1])
                    new_num = last_num + 1
                except (IndexError, ValueError):
                    new_num = 1001
            else:
                new_num = 1001
            
            self.invoice_number = f"{prefix}-{new_num:06d}"
        
        super().save(*args, **kwargs)


class InvoiceItem(models.Model):
    """Invoice line items"""
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, null=True, blank=True)
    
    # Item details
    description = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Discount
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Tax
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Total
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Order
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'
        ordering = ['order', 'id']
    
    def save(self, *args, **kwargs):
        # Calculate amounts
        subtotal = self.quantity * self.unit_price
        self.discount_amount = subtotal * (self.discount_percentage / 100)
        taxable_amount = subtotal - self.discount_amount
        self.tax_amount = taxable_amount * (self.tax_rate / 100)
        self.total = taxable_amount + self.tax_amount
        
        super().save(*args, **kwargs)