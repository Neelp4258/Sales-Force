"""
Forms for accounts app
"""
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import (
    AuthenticationForm, UserCreationForm, UserChangeForm,
    PasswordChangeForm as DjangoPasswordChangeForm
)
from django.contrib.auth import get_user_model
from accounts.models import User

User = get_user_model()


class LoginForm(AuthenticationForm):
    """Custom login form"""
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    error_messages = {
        'invalid_login': 'Invalid email or password. Please try again.',
        'inactive': 'This account is inactive.',
    }


class UserCreateForm(UserCreationForm):
    """User creation form"""
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'role', 'phone',
            'reports_to', 'sales_target', 'commission_percentage'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'reports_to': forms.Select(attrs={'class': 'form-select'}),
            'sales_target': forms.NumberInput(attrs={'class': 'form-control'}),
            'commission_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show managers and above in reports_to field
        self.fields['reports_to'].queryset = User.objects.filter(
            role__in=['admin', 'manager']
        )
        
        # Make some fields optional based on role
        self.fields['sales_target'].required = False
        self.fields['commission_percentage'].required = False
        self.fields['reports_to'].required = False
        
        # Add help text
        self.fields['sales_target'].help_text = 'Monthly sales target (for sales roles)'
        self.fields['commission_percentage'].help_text = 'Commission percentage (0-100)'


class UserUpdateForm(forms.ModelForm):
    """User update form"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'role', 'phone',
            'is_active', 'reports_to', 'sales_target', 'commission_percentage',
            'timezone', 'language'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reports_to': forms.Select(attrs={'class': 'form-select'}),
            'sales_target': forms.NumberInput(attrs={'class': 'form-control'}),
            'commission_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'timezone': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show managers and above in reports_to field
        self.fields['reports_to'].queryset = User.objects.filter(
            role__in=['admin', 'manager']
        ).exclude(pk=self.instance.pk)  # Exclude self
        
        # Add timezone choices
        import pytz
        self.fields['timezone'].choices = [
            (tz, tz) for tz in pytz.common_timezones
        ]
        
        # Add language choices
        self.fields['language'].choices = [
            ('en', 'English'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            ('de', 'German'),
            ('hi', 'Hindi'),
        ]


class ProfileUpdateForm(forms.ModelForm):
    """Profile update form"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'avatar',
            'timezone', 'language'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'timezone': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add timezone choices
        import pytz
        self.fields['timezone'].choices = [
            (tz, tz) for tz in pytz.common_timezones
        ]
        
        # Add language choices
        self.fields['language'].choices = [
            ('en', 'English'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            ('de', 'German'),
            ('hi', 'Hindi'),
        ]


class ChangePasswordForm(DjangoPasswordChangeForm):
    """Change password form"""
    
    old_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current password',
        })
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
        })
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
        })
    )


class NotificationSettingsForm(forms.ModelForm):
    """Notification settings form"""
    
    class Meta:
        model = User
        fields = [
            'email_notifications',
            'sms_notifications',
            'whatsapp_notifications',
        ]
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch',
            }),
            'sms_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch',
            }),
            'whatsapp_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch',
            }),
        }
        labels = {
            'email_notifications': 'Email Notifications',
            'sms_notifications': 'SMS Notifications',
            'whatsapp_notifications': 'WhatsApp Notifications',
        }
        help_texts = {
            'email_notifications': 'Receive notifications via email',
            'sms_notifications': 'Receive notifications via SMS',
            'whatsapp_notifications': 'Receive notifications via WhatsApp',
        }