#!/bin/bash

# Ambivare ERP Setup Script
# This script sets up the initial deployment

set -e

echo "========================================"
echo "Ambivare ERP - Initial Setup"
echo "========================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before proceeding."
    echo "Press any key to continue after editing..."
    read -n 1
fi

# Generate secret key if needed
if grep -q "your-secret-key-here" .env; then
    echo "Generating new SECRET_KEY..."
    SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    sed -i "s/your-secret-key-here/$SECRET_KEY/g" .env
fi

# Generate encryption key if needed
if grep -q "your-32-byte-encryption-key-here" .env; then
    echo "Generating new ENCRYPTION_KEY..."
    ENCRYPTION_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32)[:32])')
    sed -i "s/your-32-byte-encryption-key-here/$ENCRYPTION_KEY/g" .env
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p logs media/uploads media/exports static staticfiles backups

# Build Docker images
echo "Building Docker images..."
docker-compose build

# Start PostgreSQL and Redis first
echo "Starting database services..."
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Run migrations
echo "Running database migrations..."
docker-compose run --rm web python manage.py migrate

# Create public schema
echo "Creating public tenant..."
docker-compose run --rm web python manage.py shell << EOF
from django_tenants.utils import get_tenant_model
from tenants.models import Domain

TenantModel = get_tenant_model()

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
    
    domain = Domain()
    domain.domain = 'localhost'
    domain.tenant = public_tenant
    domain.is_primary = True
    domain.save()
    
    print("Public tenant created successfully!")
EOF

# Create superuser
echo "Creating superuser account..."
docker-compose run --rm web python manage.py shell << EOF
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
    print("Superuser created!")
    print("Email: admin@ambivare.com")
    print("Password: admin123")
    print("IMPORTANT: Change this password immediately!")
EOF

# Collect static files
echo "Collecting static files..."
docker-compose run --rm web python manage.py collectstatic --noinput

# Start all services
echo "Starting all services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check service status
echo "Checking service status..."
docker-compose ps

# Create first tenant (optional)
echo ""
echo "========================================"
echo "Setup completed successfully!"
echo "========================================"
echo ""
echo "Access the application at:"
echo "- Main App: http://localhost"
echo "- Admin Panel: http://localhost/admin"
echo "- API Docs: http://localhost/api/docs"
echo "- Celery Monitor: http://localhost:5555"
echo ""
echo "Default credentials:"
echo "- Email: admin@ambivare.com"
echo "- Password: admin123"
echo ""
echo "IMPORTANT: Change the default password immediately!"
echo ""
echo "To create a new tenant, run:"
echo "make create-tenant"
echo ""
echo "For production deployment:"
echo "1. Update .env with production values"
echo "2. Set up SSL certificates"
echo "3. Configure your domain DNS"
echo "4. Run: docker-compose -f docker-compose.prod.yml up -d"
echo ""