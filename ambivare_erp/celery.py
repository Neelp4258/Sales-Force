"""
Celery configuration for Ambivare ERP
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ambivare_erp.settings')

app = Celery('ambivare_erp')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Beat Schedule for periodic tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    'send-daily-reports': {
        'task': 'analytics.tasks.send_daily_reports',
        'schedule': crontab(hour=9, minute=0),
    },
    'check-trial-expiry': {
        'task': 'billing.tasks.check_trial_expiry',
        'schedule': crontab(hour=0, minute=0),
    },
    'send-payment-reminders': {
        'task': 'billing.tasks.send_payment_reminders',
        'schedule': crontab(hour=10, minute=0),
    },
    'cleanup-old-exports': {
        'task': 'analytics.tasks.cleanup_old_exports',
        'schedule': crontab(hour=2, minute=0),
    },
}