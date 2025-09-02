"""
Celery tasks for accounts app
"""
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from accounts.models import (
    User, PasswordResetToken, EmailVerificationToken,
    UserActivity
)
from tenants.models import TenantInvitation


@shared_task
def send_welcome_email(user_id):
    """Send welcome email to new user"""
    try:
        user = User.objects.get(id=user_id)
        
        subject = f'Welcome to {user.tenant.name} - Ambivare ERP'
        
        html_message = render_to_string('emails/welcome.html', {
            'user': user,
            'tenant': user.tenant,
            'login_url': f'https://{user.tenant.domains.first().domain}/login/',
        })
        
        send_mail(
            subject=subject,
            message='',  # Plain text version
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return f"Welcome email sent to {user.email}"
    except Exception as e:
        return f"Failed to send welcome email: {str(e)}"


@shared_task
def send_password_reset_email(token_id):
    """Send password reset email"""
    try:
        token = PasswordResetToken.objects.get(id=token_id)
        user = token.user
        
        subject = 'Password Reset Request - Ambivare ERP'
        
        reset_url = f'https://{user.tenant.domains.first().domain}/password-reset/{token.token}/'
        
        html_message = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_url': reset_url,
            'expires_in_hours': 24,
        })
        
        send_mail(
            subject=subject,
            message='',  # Plain text version
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return f"Password reset email sent to {user.email}"
    except Exception as e:
        return f"Failed to send password reset email: {str(e)}"


@shared_task
def send_invitation_email(invitation_id):
    """Send tenant invitation email"""
    try:
        invitation = TenantInvitation.objects.get(id=invitation_id)
        
        subject = f'Invitation to join {invitation.tenant.name} - Ambivare ERP'
        
        accept_url = f'https://{invitation.tenant.domains.first().domain}/accept-invitation/{invitation.token}/'
        
        html_message = render_to_string('emails/invitation.html', {
            'invitation': invitation,
            'tenant': invitation.tenant,
            'accept_url': accept_url,
            'expires_in_days': 7,
        })
        
        send_mail(
            subject=subject,
            message='',  # Plain text version
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return f"Invitation email sent to {invitation.email}"
    except Exception as e:
        return f"Failed to send invitation email: {str(e)}"


@shared_task
def send_email_verification(user_id):
    """Send email verification"""
    try:
        user = User.objects.get(id=user_id)
        
        # Create verification token
        token = EmailVerificationToken.objects.create(user=user)
        
        subject = 'Verify your email - Ambivare ERP'
        
        verify_url = f'https://{user.tenant.domains.first().domain}/verify-email/{token.token}/'
        
        html_message = render_to_string('emails/email_verification.html', {
            'user': user,
            'verify_url': verify_url,
        })
        
        send_mail(
            subject=subject,
            message='',  # Plain text version
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return f"Verification email sent to {user.email}"
    except Exception as e:
        return f"Failed to send verification email: {str(e)}"


@shared_task
def cleanup_expired_tokens():
    """Clean up expired tokens"""
    try:
        # Delete expired password reset tokens
        expired_password_tokens = PasswordResetToken.objects.filter(
            expires_at__lt=timezone.now()
        )
        password_count = expired_password_tokens.count()
        expired_password_tokens.delete()
        
        # Delete expired email verification tokens
        expired_email_tokens = EmailVerificationToken.objects.filter(
            expires_at__lt=timezone.now()
        )
        email_count = expired_email_tokens.count()
        expired_email_tokens.delete()
        
        # Delete expired invitations
        expired_invitations = TenantInvitation.objects.filter(
            expires_at__lt=timezone.now(),
            is_accepted=False
        )
        invitation_count = expired_invitations.count()
        expired_invitations.delete()
        
        return f"Cleaned up {password_count} password tokens, {email_count} email tokens, {invitation_count} invitations"
    except Exception as e:
        return f"Failed to cleanup tokens: {str(e)}"


@shared_task
def archive_old_activities():
    """Archive old user activities"""
    try:
        # Archive activities older than 90 days
        cutoff_date = timezone.now() - timezone.timedelta(days=90)
        
        old_activities = UserActivity.objects.filter(
            created_at__lt=cutoff_date
        )
        
        count = old_activities.count()
        
        # In a real implementation, you might want to:
        # 1. Export to a data warehouse
        # 2. Create summary statistics
        # 3. Move to archive tables
        
        # For now, just delete
        old_activities.delete()
        
        return f"Archived {count} old activities"
    except Exception as e:
        return f"Failed to archive activities: {str(e)}"


@shared_task
def update_user_stats():
    """Update user statistics cache"""
    try:
        from django.core.cache import cache
        from sales.models import Lead, Deal, Customer
        from tasks.models import Task
        from django.db.models import Count, Sum, Q
        
        users_updated = 0
        
        for user in User.objects.filter(is_active=True):
            # Calculate statistics
            stats = {
                'total_leads': Lead.objects.filter(assigned_to=user).count(),
                'active_leads': Lead.objects.filter(
                    assigned_to=user,
                    status__in=['new', 'contacted', 'qualified']
                ).count(),
                'total_customers': Customer.objects.filter(assigned_to=user).count(),
                'active_deals': Deal.objects.filter(
                    assigned_to=user
                ).exclude(stage__in=['closed_won', 'closed_lost']).count(),
                'won_deals': Deal.objects.filter(
                    assigned_to=user,
                    stage='closed_won'
                ).count(),
                'total_revenue': Deal.objects.filter(
                    assigned_to=user,
                    stage='closed_won'
                ).aggregate(total=Sum('amount'))['total'] or 0,
                'pending_tasks': Task.objects.filter(
                    assigned_to=user,
                    status__in=['todo', 'in_progress']
                ).count(),
            }
            
            # Cache for 1 hour
            cache_key = f'user_stats_{user.id}'
            cache.set(cache_key, stats, 3600)
            
            users_updated += 1
        
        return f"Updated statistics for {users_updated} users"
    except Exception as e:
        return f"Failed to update user stats: {str(e)}"


@shared_task
def check_inactive_users():
    """Check for inactive users and notify admins"""
    try:
        # Find users who haven't logged in for 30 days
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        
        inactive_users = User.objects.filter(
            is_active=True,
            last_login__lt=cutoff_date
        ).exclude(role='super_admin')
        
        if inactive_users.exists():
            # Group by tenant
            from collections import defaultdict
            tenant_users = defaultdict(list)
            
            for user in inactive_users:
                tenant_users[user.tenant].append(user)
            
            # Send notification to tenant admins
            for tenant, users in tenant_users.items():
                admins = User.objects.filter(
                    tenant=tenant,
                    role='admin',
                    is_active=True
                )
                
                for admin in admins:
                    subject = f'Inactive Users Report - {tenant.name}'
                    
                    html_message = render_to_string('emails/inactive_users.html', {
                        'admin': admin,
                        'inactive_users': users,
                        'tenant': tenant,
                    })
                    
                    send_mail(
                        subject=subject,
                        message='',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[admin.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
        
        return f"Checked {inactive_users.count()} inactive users"
    except Exception as e:
        return f"Failed to check inactive users: {str(e)}"