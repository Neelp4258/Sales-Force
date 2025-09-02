"""
Product management models for Ambivare ERP
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator
import uuid

User = get_user_model()


class ProductCategory(models.Model):
    """Product category model"""
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    image = models.ImageField(upload_to='product_categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    @property
    def full_path(self):
        """Get full category path"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class Product(models.Model):
    """Product model"""
    
    PRODUCT_TYPE_CHOICES = [
        ('physical', 'Physical Product'),
        ('service', 'Service'),
        ('digital', 'Digital Product'),
        ('subscription', 'Subscription'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    # Product Type
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='physical')
    
    # Categorization
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    
    # Pricing
    base_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    
    # Tax
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18.00,
        help_text="Tax rate in percentage"
    )
    hsn_code = models.CharField(max_length=20, blank=True, help_text="HSN/SAC Code")
    
    # Inventory (for physical products)
    track_inventory = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    
    # Units
    unit_of_measure = models.CharField(max_length=20, default='Unit')
    
    # Images
    featured_image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Service Specific
    service_duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Duration in hours for service products"
    )
    
    # Tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_products'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Tags
    tags = models.ManyToManyField('sales.Tag', blank=True)
    
    # Custom fields
    custom_fields = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'name']),
        ]
    
    def __str__(self):
        return f"{self.sku} - {self.name}"
    
    @property
    def selling_price(self):
        """Get selling price including tax"""
        return self.base_price * (1 + self.tax_rate / 100)
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.cost_price and self.cost_price > 0:
            return ((self.base_price - self.cost_price) / self.cost_price) * 100
        return 0
    
    @property
    def is_low_stock(self):
        """Check if product is low on stock"""
        return self.track_inventory and self.stock_quantity <= self.low_stock_threshold
    
    @property
    def is_out_of_stock(self):
        """Check if product is out of stock"""
        return self.track_inventory and self.stock_quantity <= 0
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
            
            # Ensure unique slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exists():
                self.slug = f"{slugify(self.name)}-{counter}"
                counter += 1
        
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    """Additional product images"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['order', 'created_at']


class ProductVariant(models.Model):
    """Product variants (size, color, etc.)"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100)
    sku_suffix = models.CharField(max_length=20)
    
    # Variant attributes
    attributes = models.JSONField(default=dict)  # e.g., {"size": "XL", "color": "Blue"}
    
    # Pricing override
    price_adjustment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Price adjustment from base product price"
    )
    
    # Stock
    stock_quantity = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'
        unique_together = ['product', 'sku_suffix']
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    @property
    def full_sku(self):
        return f"{self.product.sku}-{self.sku_suffix}"
    
    @property
    def price(self):
        return self.product.base_price + self.price_adjustment


class PriceList(models.Model):
    """Price list for different customer segments or time periods"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Validity
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    
    # Applicability
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Higher priority lists override lower ones")
    
    # Customer segment
    customer_tags = models.ManyToManyField('sales.Tag', blank=True, help_text="Apply to customers with these tags")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Price List'
        verbose_name_plural = 'Price Lists'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def is_valid(self):
        """Check if price list is currently valid"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from > now:
            return False
        if self.valid_to and self.valid_to < now:
            return False
        return True


class PriceListItem(models.Model):
    """Individual product prices in a price list"""
    
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    # Pricing options
    fixed_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Fixed price override"
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Discount percentage from base price"
    )
    
    # Quantity breaks
    min_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    
    class Meta:
        verbose_name = 'Price List Item'
        verbose_name_plural = 'Price List Items'
        unique_together = ['price_list', 'product', 'min_quantity']
    
    def get_price(self, quantity=1):
        """Calculate price for given quantity"""
        if quantity < self.min_quantity:
            return None
        
        if self.fixed_price:
            return self.fixed_price
        elif self.discount_percentage:
            return self.product.base_price * (1 - self.discount_percentage / 100)
        else:
            return self.product.base_price


class ProductBundle(models.Model):
    """Product bundles"""
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    # Bundle pricing
    bundle_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Fixed bundle price (leave empty to calculate from products)"
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Discount on total product prices"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product Bundle'
        verbose_name_plural = 'Product Bundles'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def calculated_price(self):
        """Calculate bundle price from products"""
        if self.bundle_price:
            return self.bundle_price
        
        total = sum(
            item.product.base_price * item.quantity
            for item in self.items.all()
        )
        
        if self.discount_percentage:
            total = total * (1 - self.discount_percentage / 100)
        
        return total


class ProductBundleItem(models.Model):
    """Items in a product bundle"""
    
    bundle = models.ForeignKey(ProductBundle, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    
    class Meta:
        verbose_name = 'Bundle Item'
        verbose_name_plural = 'Bundle Items'
        unique_together = ['bundle', 'product']