#!/bin/bash
set -e

echo "Starting Ambivare ERP..."

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z ${DB_HOST:-localhost} ${DB_PORT:-5432}; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create public schema tenant if it doesn't exist
echo "Setting up public tenant..."
python manage.py shell << EOF
from django_tenants.utils import get_tenant_model
from tenants.models import Domain

TenantModel = get_tenant_model()

# Create public tenant
if not TenantModel.objects.filter(schema_name='public').exists():
    public_tenant = TenantModel(
        schema_name='public',
        name='Public',
        slug='public',
        email='admin@ambivare.com',
        subscription_status='active',
        subscription_plan='enterprise'
    )
    public_tenant.save()
    
    # Add domain
    domain = Domain()
    domain.domain = 'localhost'
    domain.tenant = public_tenant
    domain.is_primary = True
    domain.save()
    
    print("Public tenant created successfully!")
else:
    print("Public tenant already exists.")
EOF

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(email='admin@ambivare.com').exists():
    User.objects.create_superuser(
        email='admin@ambivare.com',
        password='admin123',
        first_name='Admin',
        last_name='User',
        role='super_admin'
    )
    print("Superuser created successfully!")
    print("Email: admin@ambivare.com")
    print("Password: admin123")
else:
    print("Superuser already exists.")
EOF

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create necessary directories
mkdir -p /app/logs /app/media/uploads /app/media/exports

# Start the application
echo "Starting application..."
exec "$@"