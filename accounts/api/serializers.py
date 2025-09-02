"""
Serializers for accounts app
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from accounts.models import UserActivity, PasswordResetToken, EmailVerificationToken
from tenants.models import Tenant, TenantInvitation

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User serializer"""
    full_name = serializers.CharField(read_only=True)
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone', 'avatar', 'is_active', 'is_verified',
            'date_joined', 'last_login', 'timezone', 'language',
            'email_notifications', 'sms_notifications', 'whatsapp_notifications',
            'sales_target', 'commission_percentage', 'reports_to',
            'permissions'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_verified']
    
    def get_permissions(self, obj):
        """Get user permissions"""
        return obj.get_permissions()


class UserCreateSerializer(serializers.ModelSerializer):
    """User creation serializer"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password2', 'first_name', 'last_name',
            'role', 'phone', 'reports_to'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """User update serializer"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'timezone', 'language',
            'email_notifications', 'sms_notifications', 'whatsapp_notifications',
            'sales_target', 'commission_percentage', 'reports_to'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Change password serializer"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class LoginSerializer(serializers.Serializer):
    """Login serializer"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include "email" and "password".')


class PasswordResetRequestSerializer(serializers.Serializer):
    """Password reset request serializer"""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            # Don't reveal if email exists
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirm serializer"""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    
    def validate_token(self, value):
        try:
            token = PasswordResetToken.objects.get(
                token=value,
                is_used=False
            )
            if token.is_expired:
                raise serializers.ValidationError("Reset token has expired.")
            self.context['token'] = token
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid reset token.")
        return value
    
    def save(self):
        token = self.context['token']
        user = token.user
        user.set_password(self.validated_data['new_password'])
        user.save()
        
        token.is_used = True
        token.save()
        
        return user


class EmailVerificationSerializer(serializers.Serializer):
    """Email verification serializer"""
    token = serializers.CharField(required=True)
    
    def validate_token(self, value):
        try:
            token = EmailVerificationToken.objects.get(
                token=value,
                is_used=False
            )
            if token.is_expired:
                raise serializers.ValidationError("Verification token has expired.")
            self.context['token'] = token
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token.")
        return value
    
    def save(self):
        token = self.context['token']
        user = token.user
        user.is_verified = True
        user.save()
        
        token.is_used = True
        token.save()
        
        return user


class UserActivitySerializer(serializers.ModelSerializer):
    """User activity serializer"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'user_email', 'activity_type', 'description',
            'model_name', 'object_id', 'ip_address', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TenantInvitationSerializer(serializers.ModelSerializer):
    """Tenant invitation serializer"""
    invited_by_email = serializers.CharField(source='invited_by.email', read_only=True)
    
    class Meta:
        model = TenantInvitation
        fields = [
            'id', 'email', 'role', 'invited_by', 'invited_by_email',
            'is_accepted', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'invited_by', 'is_accepted', 'created_at', 'expires_at']
    
    def create(self, validated_data):
        # Generate token and set expiry
        invitation = TenantInvitation.objects.create(
            tenant=self.context['request'].tenant,
            invited_by=self.context['request'].user,
            **validated_data
        )
        
        # Send invitation email
        from accounts.tasks import send_invitation_email
        send_invitation_email.delay(invitation.id)
        
        return invitation


class ProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    subscription_plan = serializers.CharField(source='tenant.subscription_plan', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone', 'avatar', 'timezone', 'language',
            'email_notifications', 'sms_notifications', 'whatsapp_notifications',
            'date_joined', 'last_login', 'tenant_name', 'subscription_plan'
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'last_login']


class TeamMemberSerializer(serializers.ModelSerializer):
    """Team member serializer for managers"""
    performance_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone', 'avatar', 'is_active', 'sales_target',
            'performance_summary'
        ]
    
    def get_performance_summary(self, obj):
        """Get performance summary for team member"""
        from sales.models import Deal
        from django.utils import timezone
        from datetime import timedelta
        
        # Get current month deals
        start_date = timezone.now().replace(day=1)
        deals = Deal.objects.filter(
            assigned_to=obj,
            closed_date__gte=start_date,
            stage='closed_won'
        )
        
        return {
            'deals_closed': deals.count(),
            'revenue_generated': sum(deal.amount for deal in deals),
            'target_achievement': (sum(deal.amount for deal in deals) / obj.sales_target * 100) if obj.sales_target else 0
        }