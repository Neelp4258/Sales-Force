"""
Custom permissions for accounts app
"""
from rest_framework import permissions


class IsTenantAdmin(permissions.BasePermission):
    """
    Permission class to check if user is tenant admin
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_tenant_admin


class IsManager(permissions.BasePermission):
    """
    Permission class to check if user is manager or above
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_manager


class IsOwner(permissions.BasePermission):
    """
    Permission class to check if user is owner of object
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if object has user field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object has created_by field
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        # Check if object has assigned_to field
        if hasattr(obj, 'assigned_to'):
            return obj.assigned_to == request.user
        
        return False


class CanManageUsers(permissions.BasePermission):
    """
    Permission class to check if user can manage other users
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_manage_users


class CanExportData(permissions.BasePermission):
    """
    Permission class to check if user can export data
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_export_data