"""
API views for sales app
"""
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from sales.models import (
    Lead, Customer, Contact, Deal, DealProduct,
    Activity, Tag
)
from .serializers import (
    LeadSerializer, CustomerSerializer, ContactSerializer,
    DealSerializer, DealProductSerializer, ActivitySerializer,
    TagSerializer, LeadConvertSerializer, DealStageUpdateSerializer,
    BulkAssignSerializer
)
from .filters import (
    LeadFilter, CustomerFilter, DealFilter, ActivityFilter
)
from .permissions import CanAssignLeads, CanManageDeals
from accounts.models import User


class LeadViewSet(viewsets.ModelViewSet):
    """Lead management viewset"""
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LeadFilter
    search_fields = ['first_name', 'last_name', 'email', 'company_name', 'phone']
    ordering_fields = ['created_at', 'lead_score', 'expected_close_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter based on user role
        if user.is_manager:
            # Managers see their team's leads
            team_users = User.objects.filter(reports_to=user)
            queryset = queryset.filter(
                Q(assigned_to=user) | Q(assigned_to__in=team_users)
            )
        elif not user.is_tenant_admin:
            # Others see only their own leads
            queryset = queryset.filter(assigned_to=user)
        
        return queryset.select_related(
            'assigned_to', 'created_by', 'converted_to_customer'
        ).prefetch_related('tags')
    
    def perform_create(self, serializer):
        # Check lead limit
        tenant = self.request.tenant
        if not tenant.can_add_leads:
            raise serializers.ValidationError({
                'detail': f'Lead limit reached. Maximum allowed: {tenant.max_leads}'
            })
        
        # Auto-assign if configured
        tenant_settings = getattr(tenant, 'settings', None)
        if tenant_settings and tenant_settings.auto_assign_leads:
            assigned_to = self._get_auto_assigned_user(tenant_settings)
            serializer.save(assigned_to=assigned_to)
        else:
            serializer.save()
    
    def _get_auto_assigned_user(self, tenant_settings):
        """Get user for auto-assignment based on method"""
        method = tenant_settings.lead_assignment_method
        sales_users = User.objects.filter(
            role__in=['manager', 'executive'],
            is_active=True
        )
        
        if method == 'round_robin':
            # Get user with least recent lead assignment
            return sales_users.annotate(
                last_lead=Max('assigned_leads__assigned_date')
            ).order_by('last_lead').first()
        
        elif method == 'least_loaded':
            # Get user with fewest active leads
            return sales_users.annotate(
                active_leads=Count('assigned_leads', filter=Q(
                    assigned_leads__status__in=['new', 'contacted', 'qualified']
                ))
            ).order_by('active_leads').first()
        
        else:  # random
            return sales_users.order_by('?').first()
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def convert(self, request, pk=None):
        """Convert lead to customer"""
        lead = self.get_object()
        serializer = LeadConvertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Convert lead to customer
            customer = lead.convert_to_customer(request.user)
            
            # Create deal if requested
            if serializer.validated_data.get('create_deal'):
                deal = Deal.objects.create(
                    lead=lead,
                    customer=customer,
                    title=serializer.validated_data['deal_title'],
                    amount=serializer.validated_data.get('deal_amount', 0),
                    expected_close_date=serializer.validated_data.get('expected_close_date'),
                    assigned_to=lead.assigned_to,
                    created_by=request.user,
                )
            
            return Response({
                'customer': CustomerSerializer(customer).data,
                'deal': DealSerializer(deal).data if 'deal' in locals() else None
            })
        
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], permission_classes=[CanAssignLeads])
    def bulk_assign(self, request):
        """Bulk assign leads"""
        serializer = BulkAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        leads = Lead.objects.filter(
            id__in=serializer.validated_data['ids']
        )
        
        # Update assignment
        updated = leads.update(
            assigned_to=serializer.validated_data['assigned_to'],
            assigned_date=timezone.now()
        )
        
        return Response({
            'detail': f'{updated} leads assigned successfully.'
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get lead statistics"""
        queryset = self.get_queryset()
        
        # Status distribution
        status_dist = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Source distribution
        source_dist = queryset.values('source').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Priority distribution
        priority_dist = queryset.values('priority').annotate(
            count=Count('id')
        ).order_by('priority')
        
        # Conversion rate
        total_leads = queryset.count()
        converted_leads = queryset.filter(status='converted').count()
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        return Response({
            'total_leads': total_leads,
            'conversion_rate': round(conversion_rate, 2),
            'status_distribution': status_dist,
            'source_distribution': source_dist,
            'priority_distribution': priority_dist,
        })
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export leads to CSV/Excel"""
        # Check permission
        if not request.user.can_export_data:
            return Response(
                {'detail': 'You do not have permission to export data.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create export task
        from analytics.tasks import export_leads
        task = export_leads.delay(
            user_id=request.user.id,
            filters=request.query_params.dict()
        )
        
        return Response({
            'task_id': task.id,
            'detail': 'Export started. You will receive an email when ready.'
        })


class CustomerViewSet(viewsets.ModelViewSet):
    """Customer management viewset"""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CustomerFilter
    search_fields = ['customer_code', 'first_name', 'last_name', 'email', 'company_name']
    ordering_fields = ['created_at', 'lifetime_value', 'company_name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter based on user role
        if user.is_manager:
            # Managers see their team's customers
            team_users = User.objects.filter(reports_to=user)
            queryset = queryset.filter(
                Q(assigned_to=user) | Q(assigned_to__in=team_users)
            )
        elif not user.is_tenant_admin:
            # Others see only their own customers
            queryset = queryset.filter(assigned_to=user)
        
        return queryset.select_related(
            'assigned_to', 'created_by'
        ).prefetch_related('tags', 'contacts')
    
    @action(detail=True, methods=['post'])
    def add_contact(self, request, pk=None):
        """Add contact to customer"""
        customer = self.get_object()
        serializer = ContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contact = serializer.save(customer=customer)
        
        return Response(
            ContactSerializer(contact).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def top_customers(self, request):
        """Get top customers by revenue"""
        queryset = self.get_queryset()
        
        # Calculate revenue from closed deals
        top_customers = queryset.annotate(
            total_revenue=Sum(
                'deals__amount',
                filter=Q(deals__stage='closed_won')
            )
        ).exclude(
            total_revenue__isnull=True
        ).order_by('-total_revenue')[:20]
        
        return Response(
            CustomerSerializer(top_customers, many=True).data
        )
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get customer timeline (activities, deals, etc.)"""
        customer = self.get_object()
        
        # Get all related activities
        activities = Activity.objects.filter(
            customer=customer
        ).order_by('-scheduled_date')[:50]
        
        # Get all deals
        deals = Deal.objects.filter(
            customer=customer
        ).order_by('-created_at')
        
        return Response({
            'activities': ActivitySerializer(activities, many=True).data,
            'deals': DealSerializer(deals, many=True).data,
        })


class ContactViewSet(viewsets.ModelViewSet):
    """Contact management viewset"""
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by customer if provided
        customer_id = self.request.query_params.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        return queryset.select_related('customer')


class DealViewSet(viewsets.ModelViewSet):
    """Deal management viewset"""
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DealFilter
    search_fields = ['deal_number', 'title', 'customer__company_name']
    ordering_fields = ['created_at', 'amount', 'expected_close_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter based on user role
        if user.is_manager:
            # Managers see their team's deals
            team_users = User.objects.filter(reports_to=user)
            queryset = queryset.filter(
                Q(assigned_to=user) | Q(assigned_to__in=team_users)
            )
        elif not user.is_tenant_admin:
            # Others see only their own deals
            queryset = queryset.filter(assigned_to=user)
        
        return queryset.select_related(
            'lead', 'customer', 'contact', 'assigned_to', 'created_by'
        ).prefetch_related('tags', 'products')
    
    @action(detail=True, methods=['post'])
    def update_stage(self, request, pk=None):
        """Update deal stage"""
        deal = self.get_object()
        serializer = DealStageUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update deal
        deal.stage = serializer.validated_data['stage']
        
        if deal.stage == 'closed_lost':
            deal.lost_reason = serializer.validated_data.get('lost_reason', '')
            deal.lost_to_competitor = serializer.validated_data.get('lost_to_competitor', '')
        
        deal.save()
        
        return Response(DealSerializer(deal).data)
    
    @action(detail=True, methods=['post'])
    def add_product(self, request, pk=None):
        """Add product to deal"""
        deal = self.get_object()
        serializer = DealProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        deal_product = serializer.save(deal=deal)
        
        return Response(
            DealProductSerializer(deal_product).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def pipeline(self, request):
        """Get deals pipeline view"""
        queryset = self.get_queryset()
        
        # Get deals by stage
        pipeline = {}
        for stage, stage_name in Deal.STAGE_CHOICES:
            deals = queryset.filter(stage=stage)
            pipeline[stage] = {
                'name': stage_name,
                'deals': DealSerializer(deals, many=True).data,
                'total_value': deals.aggregate(total=Sum('amount'))['total'] or 0,
                'count': deals.count(),
            }
        
        return Response(pipeline)
    
    @action(detail=False, methods=['get'])
    def forecast(self, request):
        """Get sales forecast"""
        queryset = self.get_queryset()
        
        # Get deals closing in next 3 months
        end_date = timezone.now().date() + timezone.timedelta(days=90)
        
        forecast_deals = queryset.filter(
            expected_close_date__lte=end_date,
            stage__in=['proposal', 'negotiation']
        )
        
        # Calculate weighted forecast
        forecast_data = []
        for month in range(3):
            month_start = timezone.now().date().replace(day=1) + timezone.timedelta(days=month*30)
            month_end = (month_start + timezone.timedelta(days=32)).replace(day=1)
            
            month_deals = forecast_deals.filter(
                expected_close_date__gte=month_start,
                expected_close_date__lt=month_end
            )
            
            month_data = {
                'month': month_start.strftime('%B %Y'),
                'deals_count': month_deals.count(),
                'total_value': month_deals.aggregate(total=Sum('amount'))['total'] or 0,
                'weighted_value': sum(deal.weighted_amount for deal in month_deals),
            }
            forecast_data.append(month_data)
        
        return Response(forecast_data)


class ActivityViewSet(viewsets.ModelViewSet):
    """Activity management viewset"""
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ActivityFilter
    ordering_fields = ['scheduled_date', 'created_at']
    ordering = ['scheduled_date']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by user
        if not self.request.user.is_manager:
            queryset = queryset.filter(assigned_to=self.request.user)
        else:
            # Managers see their team's activities
            team_users = User.objects.filter(reports_to=self.request.user)
            queryset = queryset.filter(
                Q(assigned_to=self.request.user) | Q(assigned_to__in=team_users)
            )
        
        return queryset.select_related(
            'lead', 'customer', 'deal', 'contact',
            'assigned_to', 'created_by'
        )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark activity as completed"""
        activity = self.get_object()
        
        # Update activity
        activity.complete()
        
        # Add outcome if provided
        outcome = request.data.get('outcome')
        if outcome:
            activity.outcome = outcome
            activity.save()
        
        return Response(ActivitySerializer(activity).data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's activities"""
        today = timezone.now().date()
        
        activities = self.get_queryset().filter(
            scheduled_date__date=today
        )
        
        return Response(ActivitySerializer(activities, many=True).data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue activities"""
        activities = self.get_queryset().filter(
            scheduled_date__lt=timezone.now(),
            status='planned'
        )
        
        return Response(ActivitySerializer(activities, many=True).data)


class TagViewSet(viewsets.ModelViewSet):
    """Tag management viewset"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most used tags"""
        # Count usage across different models
        tags = Tag.objects.annotate(
            usage_count=Count('lead') + Count('customer') + Count('deal')
        ).order_by('-usage_count')[:20]
        
        return Response(TagSerializer(tags, many=True).data)