"""
Filters for sales app
"""
import django_filters
from django.db.models import Q
from sales.models import Lead, Customer, Deal, Activity


class LeadFilter(django_filters.FilterSet):
    """Lead filter"""
    
    # Status filters
    status = django_filters.MultipleChoiceFilter(choices=Lead.STATUS_CHOICES)
    source = django_filters.MultipleChoiceFilter(choices=Lead.SOURCE_CHOICES)
    priority = django_filters.MultipleChoiceFilter(choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ])
    
    # Score range
    min_score = django_filters.NumberFilter(field_name='lead_score', lookup_expr='gte')
    max_score = django_filters.NumberFilter(field_name='lead_score', lookup_expr='lte')
    
    # Date filters
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    # Assignment
    assigned_to = django_filters.ModelChoiceFilter(
        queryset=lambda request: request.user.get_queryset()
    )
    unassigned = django_filters.BooleanFilter(
        field_name='assigned_to',
        lookup_expr='isnull'
    )
    
    # Location
    city = django_filters.CharFilter(lookup_expr='icontains')
    state = django_filters.CharFilter(lookup_expr='icontains')
    country = django_filters.CharFilter(lookup_expr='icontains')
    
    # Tags
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=lambda request: request.user.get_queryset()
    )
    
    class Meta:
        model = Lead
        fields = [
            'status', 'source', 'priority', 'assigned_to',
            'city', 'state', 'country', 'tags'
        ]


class CustomerFilter(django_filters.FilterSet):
    """Customer filter"""
    
    # Type and status
    customer_type = django_filters.ChoiceFilter(choices=Customer.CUSTOMER_TYPE_CHOICES)
    is_active = django_filters.BooleanFilter()
    
    # Value ranges
    min_lifetime_value = django_filters.NumberFilter(
        field_name='lifetime_value',
        lookup_expr='gte'
    )
    max_lifetime_value = django_filters.NumberFilter(
        field_name='lifetime_value',
        lookup_expr='lte'
    )
    
    # Date filters
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    # Location
    city = django_filters.CharFilter(
        field_name='billing_city',
        lookup_expr='icontains'
    )
    state = django_filters.CharFilter(
        field_name='billing_state',
        lookup_expr='icontains'
    )
    country = django_filters.CharFilter(
        field_name='billing_country',
        lookup_expr='icontains'
    )
    
    # Industry
    industry = django_filters.CharFilter(lookup_expr='icontains')
    
    # Tags
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=lambda request: request.user.get_queryset()
    )
    
    class Meta:
        model = Customer
        fields = [
            'customer_type', 'is_active', 'assigned_to',
            'industry', 'tags'
        ]


class DealFilter(django_filters.FilterSet):
    """Deal filter"""
    
    # Stage and status
    stage = django_filters.MultipleChoiceFilter(choices=Deal.STAGE_CHOICES)
    
    # Amount range
    min_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    
    # Probability
    probability = django_filters.MultipleChoiceFilter(choices=Deal.PROBABILITY_CHOICES)
    
    # Date filters
    expected_close_after = django_filters.DateFilter(
        field_name='expected_close_date',
        lookup_expr='gte'
    )
    expected_close_before = django_filters.DateFilter(
        field_name='expected_close_date',
        lookup_expr='lte'
    )
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    closed_after = django_filters.DateFilter(field_name='closed_date', lookup_expr='gte')
    closed_before = django_filters.DateFilter(field_name='closed_date', lookup_expr='lte')
    
    # Customer
    customer = django_filters.ModelChoiceFilter(
        queryset=lambda request: request.user.get_queryset()
    )
    
    # Tags
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=lambda request: request.user.get_queryset()
    )
    
    # Custom filters
    is_won = django_filters.BooleanFilter(method='filter_is_won')
    is_lost = django_filters.BooleanFilter(method='filter_is_lost')
    is_open = django_filters.BooleanFilter(method='filter_is_open')
    
    def filter_is_won(self, queryset, name, value):
        if value:
            return queryset.filter(stage='closed_won')
        return queryset
    
    def filter_is_lost(self, queryset, name, value):
        if value:
            return queryset.filter(stage='closed_lost')
        return queryset
    
    def filter_is_open(self, queryset, name, value):
        if value:
            return queryset.exclude(stage__in=['closed_won', 'closed_lost'])
        return queryset
    
    class Meta:
        model = Deal
        fields = [
            'stage', 'probability', 'customer', 'assigned_to', 'tags'
        ]


class ActivityFilter(django_filters.FilterSet):
    """Activity filter"""
    
    # Type and status
    activity_type = django_filters.MultipleChoiceFilter(choices=Activity.ACTIVITY_TYPE_CHOICES)
    status = django_filters.MultipleChoiceFilter(choices=Activity.STATUS_CHOICES)
    priority = django_filters.MultipleChoiceFilter(choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ])
    
    # Date filters
    scheduled_after = django_filters.DateTimeFilter(
        field_name='scheduled_date',
        lookup_expr='gte'
    )
    scheduled_before = django_filters.DateTimeFilter(
        field_name='scheduled_date',
        lookup_expr='lte'
    )
    
    # Related objects
    lead = django_filters.ModelChoiceFilter(
        queryset=lambda request: request.user.get_queryset()
    )
    customer = django_filters.ModelChoiceFilter(
        queryset=lambda request: request.user.get_queryset()
    )
    deal = django_filters.ModelChoiceFilter(
        queryset=lambda request: request.user.get_queryset()
    )
    
    # Custom filters
    is_overdue = django_filters.BooleanFilter(method='filter_is_overdue')
    
    def filter_is_overdue(self, queryset, name, value):
        if value:
            from django.utils import timezone
            return queryset.filter(
                scheduled_date__lt=timezone.now(),
                status='planned'
            )
        return queryset
    
    class Meta:
        model = Activity
        fields = [
            'activity_type', 'status', 'priority', 'assigned_to',
            'lead', 'customer', 'deal'
        ]