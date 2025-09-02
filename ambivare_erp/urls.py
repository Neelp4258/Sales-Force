"""
Tenant-specific URLs
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('sales/', include('sales.urls')),
    path('products/', include('products.urls')),
    path('billing/', include('billing.urls')),
    path('tasks/', include('tasks.urls')),
    path('analytics/', include('analytics.urls')),
    path('integrations/', include('integrations.urls')),
    
    # API endpoints
    path('api/auth/', include('accounts.api_urls')),
    path('api/sales/', include('sales.api_urls')),
    path('api/products/', include('products.api_urls')),
    path('api/billing/', include('billing.api_urls')),
    path('api/tasks/', include('tasks.api_urls')),
    path('api/analytics/', include('analytics.api_urls')),
    path('api/integrations/', include('integrations.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)