"""
Tenant activity tracking middleware
"""
from django.utils.deprecation import MiddlewareMixin
from django_tenants.utils import get_public_schema_name
from accounts.models import UserActivity
import json


class TenantActivityMiddleware(MiddlewareMixin):
    """
    Middleware to track user activities within tenant
    """
    
    # Actions to track
    TRACKED_ACTIONS = {
        'POST': 'create',
        'PUT': 'update',
        'PATCH': 'update',
        'DELETE': 'delete',
    }
    
    # URLs to track
    TRACKED_MODELS = {
        '/sales/leads/': 'Lead',
        '/sales/customers/': 'Customer',
        '/sales/deals/': 'Deal',
        '/products/': 'Product',
        '/billing/invoices/': 'Invoice',
        '/billing/quotations/': 'Quotation',
        '/tasks/': 'Task',
    }
    
    def process_response(self, request, response):
        # Skip for public schema
        if hasattr(request, 'tenant') and request.tenant.schema_name == get_public_schema_name():
            return response
        
        # Skip if no authenticated user
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return response
        
        # Only track specific methods and successful responses
        if request.method not in self.TRACKED_ACTIONS or response.status_code not in [200, 201, 204]:
            return response
        
        # Determine model and action
        model_name = None
        for path_prefix, model in self.TRACKED_MODELS.items():
            if request.path.startswith(path_prefix):
                model_name = model
                break
        
        if not model_name:
            return response
        
        # Extract object ID from response or URL
        object_id = None
        if response.status_code in [200, 201] and hasattr(response, 'data'):
            try:
                data = json.loads(response.content)
                object_id = data.get('id', '')
            except:
                pass
        elif request.method == 'DELETE':
            # Extract from URL for DELETE requests
            path_parts = request.path.strip('/').split('/')
            if len(path_parts) >= 3:
                object_id = path_parts[-1]
        
        # Create activity log
        try:
            activity_type = self.TRACKED_ACTIONS[request.method]
            description = f"{activity_type.capitalize()} {model_name}"
            if object_id:
                description += f" (ID: {object_id})"
            
            UserActivity.objects.create(
                user=request.user,
                activity_type=activity_type,
                description=description,
                model_name=model_name,
                object_id=str(object_id) if object_id else '',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                }
            )
        except Exception as e:
            # Don't let activity tracking break the response
            pass
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TenantContextMiddleware(MiddlewareMixin):
    """
    Middleware to add tenant context to requests
    """
    
    def process_request(self, request):
        # Add tenant to request context for templates
        if hasattr(request, 'tenant'):
            request.tenant_context = {
                'tenant': request.tenant,
                'is_trial': request.tenant.is_on_trial if hasattr(request.tenant, 'is_on_trial') else False,
                'subscription_plan': request.tenant.subscription_plan,
                'features': request.tenant.enabled_features if hasattr(request.tenant, 'enabled_features') else {},
            }
        
        return None