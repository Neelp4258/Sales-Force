"""
API URLs for sales app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import views

router = DefaultRouter()
router.register('leads', views.LeadViewSet, basename='lead')
router.register('customers', views.CustomerViewSet, basename='customer')
router.register('contacts', views.ContactViewSet, basename='contact')
router.register('deals', views.DealViewSet, basename='deal')
router.register('activities', views.ActivityViewSet, basename='activity')
router.register('tags', views.TagViewSet, basename='tag')

app_name = 'sales-api'

urlpatterns = [
    path('', include(router.urls)),
]