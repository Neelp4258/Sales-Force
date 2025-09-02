"""
API URLs for accounts app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import views

router = DefaultRouter()
router.register('users', views.UserViewSet, basename='user')
router.register('team-members', views.TeamMemberViewSet, basename='team-member')
router.register('activities', views.UserActivityViewSet, basename='user-activity')
router.register('invitations', views.TenantInvitationViewSet, basename='invitation')

app_name = 'accounts-api'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('email-verify/', views.EmailVerificationView.as_view(), name='email-verify'),
    path('', include(router.urls)),
]