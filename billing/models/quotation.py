"""
Quotation model for billing module
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Quotation(models.Model):
    """Quotation/Proposal model"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote_number = models.CharField(max_length=50, unique=True)
    
    # References
    customer = models.ForeignKey('sales.Customer', on_delete=models.PROTECT, related_name='quotations')
    lead = models.ForeignKey('sales.Lead', on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations')
    deal = models.ForeignKey('sales.Deal', on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations')
    
    # Dates
    quote_date = models.DateField(default=timezone.now)
    valid_until = models.DateField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Financial Details (same as Invoice)
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
    
    # Currency
    currency = models.CharField(max_length=3, default='INR')
    
    # Terms and Notes
    terms_conditions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Addresses
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=50)
    billing_state = models.CharField(max_length=50)
    billing_country = models.CharField(max_length=50)
    billing_postal_code = models.CharField(max_length=10)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_quotations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Acceptance
    accepted_date = models.DateTimeField(null=True, blank=True)
    accepted_by = models.CharField(max_length=100, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Email Tracking
    sent_date = models.DateTimeField(null=True, blank=True)
    viewed_date = models.DateTimeField(null=True, blank=True)
    
    # PDF
    pdf_file = models.FileField(upload_to='quotations/', null=True, blank=True)
    
    # Custom fields
    custom_fields = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Quotation'
        verbose_name_plural = 'Quotations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['quote_number']),
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['status', 'valid_until']),
        ]
    
    def __str__(self):
        return f"{self.quote_number} - {self.customer.display_name}"
    
    @property
    def is_expired(self):
        """Check if quotation is expired"""
        return self.valid_until < timezone.now().date() and self.status not in ['accepted', 'rejected']
    
    def calculate_totals(self):
        """Calculate quotation totals"""
        # Same logic as Invoice
        self.subtotal = sum(item.total for item in self.items.all())
        
        if self.discount_type == 'fixed':
            self.discount_amount = min(self.discount_value, self.subtotal)
        else:
            self.discount_amount = self.subtotal * (self.discount_value / 100)
        
        taxable_amount = self.subtotal - self.discount_amount
        self.tax_amount = sum(item.tax_amount for item in self.items.all())
        self.total_amount = taxable_amount + self.tax_amount
    
    def convert_to_invoice(self):
        """Convert accepted quotation to invoice"""
        if self.status != 'accepted':
            raise ValueError("Only accepted quotations can be converted to invoices")
        
        from .invoice import Invoice, InvoiceItem
        
        invoice = Invoice.objects.create(
            customer=self.customer,
            deal=self.deal,
            quotation=self,
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=self.customer.payment_terms or 30),
            subtotal=self.subtotal,
            discount_type=self.discount_type,
            discount_value=self.discount_value,
            discount_amount=self.discount_amount,
            tax_amount=self.tax_amount,
            total_amount=self.total_amount,
            currency=self.currency,
            payment_terms=self.terms_conditions,
            notes=self.notes,
            billing_address=self.billing_address,
            billing_city=self.billing_city,
            billing_state=self.billing_state,
            billing_country=self.billing_country,
            billing_postal_code=self.billing_postal_code,
            created_by=self.created_by,
        )
        
        # Copy items
        for item in self.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                product=item.product,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_percentage=item.discount_percentage,
                tax_rate=item.tax_rate,
                order=item.order,
            )
        
        invoice.calculate_totals()
        invoice.save()
        
        return invoice
    
    def save(self, *args, **kwargs):
        if not self.quote_number:
            # Generate quote number
            prefix = 'QT'
            
            # Get the last quote number
            last_quote = Quotation.objects.filter(
                quote_number__startswith=prefix
            ).order_by('-created_at').first()
            
            if last_quote:
                try:
                    last_num = int(last_quote.quote_number.split('-')[-1])
                    new_num = last_num + 1
                except (IndexError, ValueError):
                    new_num = 1001
            else:
                new_num = 1001
            
            self.quote_number = f"{prefix}-{new_num:06d}"
        
        # Check if expired
        if self.is_expired and self.status not in ['accepted', 'rejected', 'expired']:
            self.status = 'expired'
        
        super().save(*args, **kwargs)


class QuotationItem(models.Model):
    """Quotation line items"""
    
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
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
        verbose_name = 'Quotation Item'
        verbose_name_plural = 'Quotation Items'
        ordering = ['order', 'id']
    
    def save(self, *args, **kwargs):
        # Calculate amounts
        subtotal = self.quantity * self.unit_price
        self.discount_amount = subtotal * (self.discount_percentage / 100)
        taxable_amount = subtotal - self.discount_amount
        self.tax_amount = taxable_amount * (self.tax_rate / 100)
        self.total = taxable_amount + self.tax_amount
        
        super().save(*args, **kwargs)