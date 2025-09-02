"""
URLs for accounts app
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile-edit'),
    
    # User Management
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/create/', views.UserCreateView.as_view(), name='user-create'),
    path('users/<uuid:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<uuid:pk>/edit/', views.UserUpdateView.as_view(), name='user-edit'),
    path('users/<uuid:pk>/delete/', views.UserDeleteView.as_view(), name='user-delete'),
    
    # Team Management
    path('team/', views.TeamListView.as_view(), name='team-list'),
    path('team/<uuid:pk>/', views.TeamMemberDetailView.as_view(), name='team-member-detail'),
    
    # Activity Log
    path('activity/', views.ActivityLogView.as_view(), name='activity-log'),
    
    # Settings
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('settings/password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('settings/notifications/', views.NotificationSettingsView.as_view(), name='notification-settings'),
]