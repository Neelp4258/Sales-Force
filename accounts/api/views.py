"""
API views for accounts app
"""
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, login, logout
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from accounts.models import UserActivity, PasswordResetToken, EmailVerificationToken
from tenants.models import TenantInvitation
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, LoginSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, EmailVerificationSerializer,
    UserActivitySerializer, TenantInvitationSerializer, ProfileSerializer,
    TeamMemberSerializer
)
from .permissions import IsTenantAdmin, IsManager, IsOwner

User = get_user_model()


class LoginView(APIView):
    """Login view"""
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        login(request, user)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            description='User logged in',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """Logout view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='logout',
            description='User logged out',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logout(request)
        return Response({'detail': 'Successfully logged out.'})
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RegisterView(generics.CreateAPIView):
    """Register view for public tenant creation"""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        # This would be used for public registration
        # Creating a new tenant and admin user
        # For now, return method not allowed
        return Response(
            {'detail': 'Public registration not available. Please contact sales.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile view"""
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """Change password view"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set the new password
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response({'detail': 'Password updated successfully.'})


class PasswordResetRequestView(generics.GenericAPIView):
    """Password reset request view"""
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            
            # Create reset token
            token = PasswordResetToken.objects.create(user=user)
            
            # Send reset email
            from accounts.tasks import send_password_reset_email
            send_password_reset_email.delay(token.id)
        except User.DoesNotExist:
            # Don't reveal if email exists
            pass
        
        return Response({
            'detail': 'If an account exists with this email, a password reset link has been sent.'
        })


class PasswordResetConfirmView(generics.GenericAPIView):
    """Password reset confirm view"""
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({'detail': 'Password reset successfully.'})


class EmailVerificationView(generics.GenericAPIView):
    """Email verification view"""
    serializer_class = EmailVerificationSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({'detail': 'Email verified successfully.'})


class UserViewSet(viewsets.ModelViewSet):
    """User management viewset"""
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset.order_by('-date_joined')
    
    def perform_create(self, serializer):
        # Check user limit
        tenant = self.request.tenant
        if not tenant.can_add_users:
            raise serializers.ValidationError({
                'detail': f'User limit reached. Maximum allowed: {tenant.max_users}'
            })
        
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate user"""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'detail': 'User activated successfully.'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate user"""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'detail': 'User deactivated successfully.'})
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Send password reset email to user"""
        user = self.get_object()
        
        # Create reset token
        token = PasswordResetToken.objects.create(user=user)
        
        # Send reset email
        from accounts.tasks import send_password_reset_email
        send_password_reset_email.delay(token.id)
        
        return Response({'detail': 'Password reset email sent.'})
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export users to CSV"""
        # Check permission
        if not request.user.can_export_data:
            return Response(
                {'detail': 'You do not have permission to export data.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create export task
        from analytics.tasks import export_users
        task = export_users.delay(
            user_id=request.user.id,
            filters=request.query_params.dict()
        )
        
        return Response({
            'task_id': task.id,
            'detail': 'Export started. You will receive an email when ready.'
        })


class TeamMemberViewSet(viewsets.ReadOnlyModelViewSet):
    """Team member viewset for managers"""
    serializer_class = TeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsManager]
    
    def get_queryset(self):
        # Managers can see their team members
        return User.objects.filter(reports_to=self.request.user)


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """User activity viewset"""
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by activity type
        activity_type = self.request.query_params.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset.select_related('user').order_by('-created_at')


class TenantInvitationViewSet(viewsets.ModelViewSet):
    """Tenant invitation viewset"""
    queryset = TenantInvitation.objects.all()
    serializer_class = TenantInvitationSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantAdmin]
    
    def get_queryset(self):
        return super().get_queryset().filter(
            tenant=self.request.tenant
        ).select_related('invited_by')
    
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Resend invitation email"""
        invitation = self.get_object()
        
        if invitation.is_accepted:
            return Response(
                {'detail': 'Invitation already accepted.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Send invitation email
        from accounts.tasks import send_invitation_email
        send_invitation_email.delay(invitation.id)
        
        return Response({'detail': 'Invitation email resent.'})
    
    @action(detail=True, methods=['delete'])
    def cancel(self, request, pk=None):
        """Cancel invitation"""
        invitation = self.get_object()
        
        if invitation.is_accepted:
            return Response(
                {'detail': 'Cannot cancel accepted invitation.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invitation.delete()
        return Response({'detail': 'Invitation cancelled.'})