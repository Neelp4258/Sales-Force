"""
Serializers for sales app
"""
from rest_framework import serializers
from django.db import transaction
from sales.models import (
    Lead, Customer, Contact, Deal, DealProduct,
    Activity, Tag
)
from products.models import Product
from accounts.api.serializers import UserSerializer


class TagSerializer(serializers.ModelSerializer):
    """Tag serializer"""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class LeadSerializer(serializers.ModelSerializer):
    """Lead serializer"""
    assigned_to_detail = UserSerializer(source='assigned_to', read_only=True)
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        write_only=True,
        source='tags'
    )
    full_name = serializers.CharField(read_only=True)
    days_since_creation = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'secondary_phone', 'company_name', 'job_title', 'industry',
            'company_size', 'annual_revenue', 'status', 'source', 'source_details',
            'lead_score', 'priority', 'assigned_to', 'assigned_to_detail',
            'assigned_date', 'address', 'city', 'state', 'country', 'postal_code',
            'description', 'requirements', 'budget', 'expected_close_date',
            'linkedin', 'twitter', 'facebook', 'created_by', 'created_by_detail',
            'created_at', 'updated_at', 'converted_to_customer', 'converted_date',
            'tags', 'tag_ids', 'custom_fields', 'days_since_creation'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'converted_to_customer',
            'converted_date', 'assigned_date'
        ]
    
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        validated_data['created_by'] = self.context['request'].user
        
        lead = Lead.objects.create(**validated_data)
        lead.tags.set(tags)
        
        return lead
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        
        # Track assignment change
        if 'assigned_to' in validated_data and validated_data['assigned_to'] != instance.assigned_to:
            validated_data['assigned_date'] = timezone.now()
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        if tags is not None:
            instance.tags.set(tags)
        
        return instance


class ContactSerializer(serializers.ModelSerializer):
    """Contact serializer"""
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'customer', 'customer_name', 'first_name', 'last_name',
            'email', 'phone', 'mobile', 'job_title', 'department',
            'is_primary', 'is_active', 'preferred_contact_method',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomerSerializer(serializers.ModelSerializer):
    """Customer serializer"""
    assigned_to_detail = UserSerializer(source='assigned_to', read_only=True)
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        write_only=True,
        source='tags'
    )
    full_name = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'customer_code', 'customer_type', 'first_name', 'last_name',
            'full_name', 'display_name', 'email', 'phone', 'secondary_phone',
            'company_name', 'job_title', 'industry', 'website',
            'billing_address', 'billing_city', 'billing_state', 'billing_country',
            'billing_postal_code', 'shipping_address', 'shipping_city',
            'shipping_state', 'shipping_country', 'shipping_postal_code',
            'same_as_billing', 'tax_id', 'tax_exempt', 'assigned_to',
            'assigned_to_detail', 'lifetime_value', 'credit_limit',
            'payment_terms', 'is_active', 'lead_source', 'created_by',
            'created_by_detail', 'created_at', 'updated_at', 'notes',
            'contacts', 'tags', 'tag_ids', 'custom_fields'
        ]
        read_only_fields = ['id', 'customer_code', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        validated_data['created_by'] = self.context['request'].user
        
        customer = Customer.objects.create(**validated_data)
        customer.tags.set(tags)
        
        return customer
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        if tags is not None:
            instance.tags.set(tags)
        
        return instance


class DealProductSerializer(serializers.ModelSerializer):
    """Deal product serializer"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    taxable_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = DealProduct
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'quantity',
            'unit_price', 'discount_percentage', 'tax_percentage',
            'subtotal', 'discount_amount', 'taxable_amount', 'tax_amount', 'total'
        ]


class DealSerializer(serializers.ModelSerializer):
    """Deal serializer"""
    lead_name = serializers.CharField(source='lead.full_name', read_only=True)
    customer_name = serializers.CharField(source='customer.display_name', read_only=True)
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    assigned_to_detail = UserSerializer(source='assigned_to', read_only=True)
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    products = DealProductSerializer(source='dealproduct_set', many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        write_only=True,
        source='tags'
    )
    weighted_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    days_in_pipeline = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Deal
        fields = [
            'id', 'deal_number', 'title', 'description', 'lead', 'lead_name',
            'customer', 'customer_name', 'contact', 'contact_name', 'stage',
            'amount', 'currency', 'probability', 'expected_close_date',
            'competitors', 'assigned_to', 'assigned_to_detail', 'products',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'closed_date', 'lost_reason', 'lost_to_competitor', 'tags',
            'tag_ids', 'custom_fields', 'weighted_amount', 'days_in_pipeline'
        ]
        read_only_fields = ['id', 'deal_number', 'created_at', 'updated_at', 'closed_date']
    
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        validated_data['created_by'] = self.context['request'].user
        
        deal = Deal.objects.create(**validated_data)
        deal.tags.set(tags)
        
        return deal
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        if tags is not None:
            instance.tags.set(tags)
        
        return instance


class ActivitySerializer(serializers.ModelSerializer):
    """Activity serializer"""
    assigned_to_detail = UserSerializer(source='assigned_to', read_only=True)
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    # Related object details
    lead_detail = serializers.SerializerMethodField()
    customer_detail = serializers.SerializerMethodField()
    deal_detail = serializers.SerializerMethodField()
    contact_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = Activity
        fields = [
            'id', 'activity_type', 'subject', 'description', 'lead', 'lead_detail',
            'customer', 'customer_detail', 'deal', 'deal_detail', 'contact',
            'contact_detail', 'status', 'priority', 'scheduled_date',
            'duration_minutes', 'completed_date', 'assigned_to', 'assigned_to_detail',
            'location', 'outcome', 'created_by', 'created_by_detail',
            'created_at', 'updated_at', 'reminder_minutes_before', 'reminder_sent',
            'is_overdue'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'reminder_sent']
    
    def get_lead_detail(self, obj):
        if obj.lead:
            return {'id': obj.lead.id, 'name': obj.lead.full_name}
        return None
    
    def get_customer_detail(self, obj):
        if obj.customer:
            return {'id': obj.customer.id, 'name': obj.customer.display_name}
        return None
    
    def get_deal_detail(self, obj):
        if obj.deal:
            return {'id': obj.deal.id, 'title': obj.deal.title}
        return None
    
    def get_contact_detail(self, obj):
        if obj.contact:
            return {'id': obj.contact.id, 'name': obj.contact.full_name}
        return None
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return Activity.objects.create(**validated_data)


class LeadConvertSerializer(serializers.Serializer):
    """Lead conversion serializer"""
    create_deal = serializers.BooleanField(default=True)
    deal_title = serializers.CharField(required=False)
    deal_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    expected_close_date = serializers.DateField(required=False)
    
    def validate(self, attrs):
        if attrs.get('create_deal') and not attrs.get('deal_title'):
            raise serializers.ValidationError({
                'deal_title': 'Deal title is required when creating a deal.'
            })
        return attrs


class DealStageUpdateSerializer(serializers.Serializer):
    """Deal stage update serializer"""
    stage = serializers.ChoiceField(choices=Deal.STAGE_CHOICES)
    lost_reason = serializers.CharField(required=False, allow_blank=True)
    lost_to_competitor = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        if attrs['stage'] == 'closed_lost':
            if not attrs.get('lost_reason'):
                raise serializers.ValidationError({
                    'lost_reason': 'Lost reason is required when marking deal as lost.'
                })
        return attrs


class BulkAssignSerializer(serializers.Serializer):
    """Bulk assignment serializer"""
    ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    
    def validate_assigned_to(self, value):
        # Ensure user has appropriate role
        if value.role not in ['admin', 'manager', 'executive']:
            raise serializers.ValidationError('User must have sales role.')
        return value