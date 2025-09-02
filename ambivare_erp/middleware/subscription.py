"""
Subscription middleware to enforce plan limits
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django_tenants.utils import get_tenant_model, get_public_schema_name


class SubscriptionMiddleware(MiddlewareMixin):
    """
    Middleware to check subscription status and enforce limits
    """
    
    # URLs that should be accessible regardless of subscription status
    EXEMPT_URLS = [
        '/admin/',
        '/api/auth/login/',
        '/api/auth/logout/',
        '/billing/subscription/',
        '/billing/upgrade/',
        '/static/',
        '/media/',
    ]
    
    def process_request(self, request):
        # Skip for public schema
        if hasattr(request, 'tenant') and request.tenant.schema_name == get_public_schema_name():
            return None
        
        # Skip for exempt URLs
        for exempt_url in self.EXEMPT_URLS:
            if request.path.startswith(exempt_url):
                return None
        
        # Skip if no tenant
        if not hasattr(request, 'tenant'):
            return None
        
        tenant = request.tenant
        
        # Check subscription status
        if tenant.subscription_status == 'cancelled':
            return self._handle_cancelled_subscription(request)
        
        if tenant.subscription_status == 'past_due':
            return self._handle_past_due_subscription(request)
        
        # Check trial expiry
        if tenant.is_trial_expired:
            return self._handle_expired_trial(request)
        
        # Check resource limits for specific actions
        if request.method == 'POST':
            return self._check_resource_limits(request, tenant)
        
        return None
    
    def _handle_cancelled_subscription(self, request):
        """Handle cancelled subscription"""
        if request.is_ajax() or request.path.startswith('/api/'):
            return JsonResponse({
                'error': 'Your subscription has been cancelled. Please contact support.',
                'code': 'SUBSCRIPTION_CANCELLED'
            }, status=403)
        
        messages.error(request, 'Your subscription has been cancelled. Please contact support.')
        return redirect('billing:subscription')
    
    def _handle_past_due_subscription(self, request):
        """Handle past due subscription"""
        if request.is_ajax() or request.path.startswith('/api/'):
            return JsonResponse({
                'error': 'Your subscription payment is past due. Please update your payment method.',
                'code': 'SUBSCRIPTION_PAST_DUE'
            }, status=403)
        
        messages.warning(request, 'Your subscription payment is past due. Please update your payment method.')
        # Allow read-only access
        if request.method != 'GET':
            return redirect('billing:subscription')
        
        return None
    
    def _handle_expired_trial(self, request):
        """Handle expired trial"""
        if request.is_ajax() or request.path.startswith('/api/'):
            return JsonResponse({
                'error': 'Your trial has expired. Please upgrade to continue.',
                'code': 'TRIAL_EXPIRED'
            }, status=403)
        
        messages.warning(request, 'Your trial has expired. Please upgrade to continue using our services.')
        return redirect('billing:upgrade')
    
    def _check_resource_limits(self, request, tenant):
        """Check resource limits based on the action"""
        
        # Check user limit
        if request.path.startswith('/accounts/users/create/') or \
           request.path.startswith('/api/users/'):
            if not tenant.can_add_users:
                return self._handle_limit_exceeded(request, 'users', tenant.max_users)
        
        # Check lead limit
        if request.path.startswith('/sales/leads/create/') or \
           request.path.startswith('/api/leads/'):
            if not tenant.can_add_leads:
                return self._handle_limit_exceeded(request, 'leads', tenant.max_leads)
        
        # Check storage limit (for file uploads)
        if 'file' in request.FILES or 'attachment' in request.FILES:
            file_size = sum(f.size for f in request.FILES.values())
            file_size_mb = file_size / (1024 * 1024)
            
            if tenant.current_storage_mb + file_size_mb > tenant.max_storage_mb:
                return self._handle_limit_exceeded(request, 'storage', f"{tenant.max_storage_mb}MB")
        
        return None
    
    def _handle_limit_exceeded(self, request, resource_type, limit):
        """Handle resource limit exceeded"""
        if request.is_ajax() or request.path.startswith('/api/'):
            return JsonResponse({
                'error': f'You have reached your {resource_type} limit ({limit}). Please upgrade your plan.',
                'code': 'LIMIT_EXCEEDED',
                'resource': resource_type,
                'limit': limit
            }, status=403)
        
        messages.error(
            request,
            f'You have reached your {resource_type} limit ({limit}). Please upgrade your plan to continue.'
        )
        return redirect('billing:upgrade')


class UsageTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track tenant resource usage
    """
    
    def process_response(self, request, response):
        # Only track for tenant requests
        if not hasattr(request, 'tenant') or request.tenant.schema_name == get_public_schema_name():
            return response
        
        # Track successful resource creation
        if request.method == 'POST' and response.status_code in [200, 201]:
            tenant = request.tenant
            
            # Update user count
            if request.path.startswith('/accounts/users/') or request.path.startswith('/api/users/'):
                from accounts.models import User
                tenant.current_users = User.objects.count()
                tenant.save(update_fields=['current_users'])
            
            # Update lead count
            elif request.path.startswith('/sales/leads/') or request.path.startswith('/api/leads/'):
                from sales.models import Lead
                tenant.current_leads = Lead.objects.count()
                tenant.save(update_fields=['current_leads'])
            
            # Update storage usage
            elif 'file' in request.FILES or 'attachment' in request.FILES:
                file_size_mb = sum(f.size for f in request.FILES.values()) / (1024 * 1024)
                tenant.current_storage_mb += file_size_mb
                tenant.save(update_fields=['current_storage_mb'])
        
        return response