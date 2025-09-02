"""
Admin configuration for tenants app
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from django_tenants.admin import TenantAdminMixin
from tenants.models import Tenant, Domain, TenantSettings, TenantInvitation


@admin.register(Tenant)
class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Tenant admin"""
    list_display = [
        'name', 'slug', 'schema_name', 'subscription_status_badge',
        'subscription_plan_badge', 'created_on', 'is_active'
    ]
    list_filter = [
        'subscription_status', 'subscription_plan', 'is_active',
        'country', 'created_on'
    ]
    search_fields = ['name', 'slug', 'email', 'schema_name']
    readonly_fields = [
        'schema_name', 'created_on', 'updated_on',
        'current_users', 'current_leads', 'current_storage_mb'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'schema_name', 'email', 'phone')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Subscription', {
            'fields': (
                'subscription_status', 'subscription_plan',
                'trial_end_date', 'subscription_end_date'
            )
        }),
        ('Payment Gateway', {
            'fields': (
                'stripe_customer_id', 'stripe_subscription_id',
                'razorpay_customer_id', 'razorpay_subscription_id'
            ),
            'classes': ('collapse',)
        }),
        ('Usage Limits', {
            'fields': ('max_users', 'max_leads', 'max_storage_mb')
        }),
        ('Current Usage', {
            'fields': ('current_users', 'current_leads', 'current_storage_mb')
        }),
        ('Settings', {
            'fields': (
                'timezone', 'currency', 'fiscal_year_start',
                'tax_id', 'logo'
            )
        }),
        ('Status', {
            'fields': ('is_active', 'created_on', 'updated_on')
        }),
    )
    
    actions = ['activate_tenants', 'deactivate_tenants', 'extend_trial']
    
    def subscription_status_badge(self, obj):
        """Display subscription status as badge"""
        colors = {
            'trial': 'warning',
            'active': 'success',
            'past_due': 'danger',
            'cancelled': 'secondary',
            'paused': 'info',
        }
        color = colors.get(obj.subscription_status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_subscription_status_display()
        )
    subscription_status_badge.short_description = 'Status'
    
    def subscription_plan_badge(self, obj):
        """Display subscription plan as badge"""
        colors = {
            'starter': 'primary',
            'pro': 'success',
            'enterprise': 'danger',
        }
        color = colors.get(obj.subscription_plan, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_subscription_plan_display()
        )
    subscription_plan_badge.short_description = 'Plan'
    
    def activate_tenants(self, request, queryset):
        """Activate selected tenants"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} tenants activated.')
    activate_tenants.short_description = 'Activate selected tenants'
    
    def deactivate_tenants(self, request, queryset):
        """Deactivate selected tenants"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} tenants deactivated.')
    deactivate_tenants.short_description = 'Deactivate selected tenants'
    
    def extend_trial(self, request, queryset):
        """Extend trial by 7 days"""
        for tenant in queryset.filter(subscription_status='trial'):
            if tenant.trial_end_date:
                tenant.trial_end_date += timezone.timedelta(days=7)
                tenant.save()
        self.message_user(request, 'Trial extended by 7 days.')
    extend_trial.short_description = 'Extend trial by 7 days'


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Domain admin"""
    list_display = ['domain', 'tenant', 'is_primary', 'ssl_enabled']
    list_filter = ['is_primary', 'ssl_enabled']
    search_fields = ['domain', 'tenant__name']
    readonly_fields = ['id']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'domain', 'tenant', 'is_primary', 'ssl_enabled')
        }),
    )


@admin.register(TenantSettings)
class TenantSettingsAdmin(admin.ModelAdmin):
    """Tenant settings admin"""
    list_display = ['tenant', 'invoice_prefix', 'quote_prefix', 'tax_name', 'tax_percentage']
    search_fields = ['tenant__name']
    
    fieldsets = (
        ('Email Settings', {
            'fields': (
                'email_signature', 'auto_send_invoice',
                'auto_send_reminder', 'reminder_days_before'
            )
        }),
        ('Document Settings', {
            'fields': (
                'invoice_prefix', 'invoice_starting_number',
                'quote_prefix', 'quote_starting_number'
            )
        }),
        ('Tax Settings', {
            'fields': ('tax_name', 'tax_percentage')
        }),
        ('Lead Management', {
            'fields': ('auto_assign_leads', 'lead_assignment_method')
        }),
        ('Notifications', {
            'fields': (
                'email_notifications', 'sms_notifications',
                'whatsapp_notifications'
            )
        }),
        ('Working Hours', {
            'fields': (
                'working_days', 'working_hours_start',
                'working_hours_end'
            )
        }),
        ('Theme', {
            'fields': ('primary_color', 'secondary_color')
        }),
    )


@admin.register(TenantInvitation)
class TenantInvitationAdmin(admin.ModelAdmin):
    """Tenant invitation admin"""
    list_display = [
        'email', 'tenant', 'role', 'invited_by',
        'is_accepted', 'created_at', 'expires_at'
    ]
    list_filter = ['is_accepted', 'role', 'created_at']
    search_fields = ['email', 'tenant__name']
    readonly_fields = ['id', 'token', 'created_at', 'expires_at']
    
    fieldsets = (
        (None, {
            'fields': (
                'id', 'tenant', 'email', 'role',
                'invited_by', 'token', 'is_accepted'
            )
        }),
        ('Dates', {
            'fields': ('created_at', 'expires_at')
        }),
    )
    
    actions = ['resend_invitations']
    
    def resend_invitations(self, request, queryset):
        """Resend invitation emails"""
        from accounts.tasks import send_invitation_email
        
        count = 0
        for invitation in queryset.filter(is_accepted=False):
            send_invitation_email.delay(invitation.id)
            count += 1
        
        self.message_user(request, f'{count} invitation emails queued.')
    resend_invitations.short_description = 'Resend invitation emails'


# Inline for domain in tenant admin
class DomainInline(admin.TabularInline):
    model = Domain
    extra = 1
    fields = ['domain', 'is_primary', 'ssl_enabled']


# Add inline to TenantAdmin
TenantAdmin.inlines = [DomainInline]