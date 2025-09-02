"""
URLs for sales app
"""
from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Dashboard
    path('', views.SalesDashboardView.as_view(), name='dashboard'),
    
    # Leads
    path('leads/', views.LeadListView.as_view(), name='lead-list'),
    path('leads/create/', views.LeadCreateView.as_view(), name='lead-create'),
    path('leads/<uuid:pk>/', views.LeadDetailView.as_view(), name='lead-detail'),
    path('leads/<uuid:pk>/edit/', views.LeadUpdateView.as_view(), name='lead-edit'),
    path('leads/<uuid:pk>/delete/', views.LeadDeleteView.as_view(), name='lead-delete'),
    path('leads/<uuid:pk>/convert/', views.LeadConvertView.as_view(), name='lead-convert'),
    path('leads/kanban/', views.LeadKanbanView.as_view(), name='lead-kanban'),
    
    # Customers
    path('customers/', views.CustomerListView.as_view(), name='customer-list'),
    path('customers/create/', views.CustomerCreateView.as_view(), name='customer-create'),
    path('customers/<uuid:pk>/', views.CustomerDetailView.as_view(), name='customer-detail'),
    path('customers/<uuid:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer-edit'),
    path('customers/<uuid:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer-delete'),
    path('customers/<uuid:pk>/add-contact/', views.ContactCreateView.as_view(), name='contact-create'),
    
    # Deals
    path('deals/', views.DealListView.as_view(), name='deal-list'),
    path('deals/create/', views.DealCreateView.as_view(), name='deal-create'),
    path('deals/<uuid:pk>/', views.DealDetailView.as_view(), name='deal-detail'),
    path('deals/<uuid:pk>/edit/', views.DealUpdateView.as_view(), name='deal-edit'),
    path('deals/<uuid:pk>/delete/', views.DealDeleteView.as_view(), name='deal-delete'),
    path('deals/pipeline/', views.DealPipelineView.as_view(), name='deal-pipeline'),
    
    # Activities
    path('activities/', views.ActivityListView.as_view(), name='activity-list'),
    path('activities/create/', views.ActivityCreateView.as_view(), name='activity-create'),
    path('activities/<uuid:pk>/', views.ActivityDetailView.as_view(), name='activity-detail'),
    path('activities/<uuid:pk>/edit/', views.ActivityUpdateView.as_view(), name='activity-edit'),
    path('activities/<uuid:pk>/complete/', views.ActivityCompleteView.as_view(), name='activity-complete'),
    path('activities/calendar/', views.ActivityCalendarView.as_view(), name='activity-calendar'),
    
    # Reports
    path('reports/', views.SalesReportsView.as_view(), name='reports'),
    path('reports/lead-analytics/', views.LeadAnalyticsView.as_view(), name='lead-analytics'),
    path('reports/sales-forecast/', views.SalesForecastView.as_view(), name='sales-forecast'),
    path('reports/team-performance/', views.TeamPerformanceView.as_view(), name='team-performance'),
]