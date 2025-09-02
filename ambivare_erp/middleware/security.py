"""
Security middleware for the application
"""
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.conf import settings
import re


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to responses
    """
    
    def process_response(self, request, response):
        # Content Security Policy
        response['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.stripe.com https://api.razorpay.com"
        
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options (already set by Django's clickjacking middleware)
        # response['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer-Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Strict-Transport-Security (only for HTTPS)
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.cache = {}
        self.rates = {
            'api/auth/login': (5, 300),  # 5 attempts per 5 minutes
            'api/auth/register': (3, 3600),  # 3 attempts per hour
            'api/auth/password-reset': (3, 3600),  # 3 attempts per hour
            'api/': (1000, 3600),  # 1000 API calls per hour (general)
        }
    
    def process_request(self, request):
        # Only apply to specific paths
        path = request.path.strip('/')
        
        # Find matching rate limit rule
        rate_limit = None
        for pattern, limit in self.rates.items():
            if path.startswith(pattern):
                rate_limit = limit
                break
        
        if not rate_limit:
            return None
        
        # Get client identifier
        client_id = self.get_client_id(request)
        cache_key = f"{path}:{client_id}"
        
        # Check rate limit
        max_requests, window = rate_limit
        
        # Simple in-memory rate limiting (use Redis in production)
        import time
        current_time = time.time()
        
        if cache_key not in self.cache:
            self.cache[cache_key] = []
        
        # Remove old entries
        self.cache[cache_key] = [
            timestamp for timestamp in self.cache[cache_key]
            if current_time - timestamp < window
        ]
        
        # Check if limit exceeded
        if len(self.cache[cache_key]) >= max_requests:
            return HttpResponseForbidden('Rate limit exceeded. Please try again later.')
        
        # Add current request
        self.cache[cache_key].append(current_time)
        
        return None
    
    def get_client_id(self, request):
        """Get client identifier for rate limiting"""
        if request.user.is_authenticated:
            return f"user:{request.user.id}"
        
        # Use IP address for anonymous users
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        return f"ip:{ip}"


class IPWhitelistMiddleware(MiddlewareMixin):
    """
    IP whitelist middleware for admin panel
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Get whitelist from settings
        self.whitelist = getattr(settings, 'ADMIN_IP_WHITELIST', [])
        self.whitelist_enabled = getattr(settings, 'ENABLE_IP_WHITELIST', False)
    
    def process_request(self, request):
        # Only apply to admin URLs
        if not request.path.startswith('/admin/'):
            return None
        
        # Skip if whitelist is not enabled
        if not self.whitelist_enabled or not self.whitelist:
            return None
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Check if IP is whitelisted
        if ip not in self.whitelist:
            return HttpResponseForbidden('Access denied. Your IP address is not authorized.')
        
        return None