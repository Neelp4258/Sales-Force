"""
Custom permissions for sales app
"""
from rest_framework import permissions


class CanAssignLeads(permissions.BasePermission):
    """Permission to check if user can assign leads"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['super_admin', 'admin', 'manager']
        )


class CanManageDeals(permissions.BasePermission):
    """Permission to check if user can manage deals"""
    
    def has_permission(self, request, view):
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions based on role
        return (
            request.user.is_authenticated and
            request.user.role in ['super_admin', 'admin', 'manager', 'executive']
        )
    
    def has_object_permission(self, request, view, obj):
        # Read permissions
        if request.method in permissions.SAFE_METHODS:
            # Users can see their own deals
            if obj.assigned_to == request.user:
                return True
            
            # Managers can see their team's deals
            if request.user.is_manager and obj.assigned_to.reports_to == request.user:
                return True
            
            # Admins can see all deals
            if request.user.is_tenant_admin:
                return True
            
            return False
        
        # Write permissions
        # Users can edit their own deals
        if obj.assigned_to == request.user:
            return True
        
        # Managers can edit their team's deals
        if request.user.is_manager and obj.assigned_to.reports_to == request.user:
            return True
        
        # Admins can edit all deals
        if request.user.is_tenant_admin:
            return True
        
        return False


class IsOwnerOrManager(permissions.BasePermission):
    """Permission to check if user is owner or manager"""
    
    def has_object_permission(self, request, view, obj):
        # Check if user is owner
        if hasattr(obj, 'assigned_to') and obj.assigned_to == request.user:
            return True
        
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        # Check if user is manager of owner
        if request.user.is_manager:
            if hasattr(obj, 'assigned_to') and obj.assigned_to.reports_to == request.user:
                return True
            
            if hasattr(obj, 'created_by') and obj.created_by.reports_to == request.user:
                return True
        
        # Admins have full access
        if request.user.is_tenant_admin:
            return True
        
        return False