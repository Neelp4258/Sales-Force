.PHONY: help build up down restart logs shell migrate makemigrations test lint format clean

# Default target
help:
	@echo "Ambivare ERP - Development Commands"
	@echo "=================================="
	@echo "make build          - Build Docker images"
	@echo "make up             - Start all services"
	@echo "make down           - Stop all services"
	@echo "make restart        - Restart all services"
	@echo "make logs           - View logs"
	@echo "make shell          - Django shell"
	@echo "make bash           - Bash shell in web container"
	@echo "make migrate        - Run migrations"
	@echo "make makemigrations - Create migrations"
	@echo "make createsuperuser- Create superuser"
	@echo "make test           - Run tests"
	@echo "make lint           - Run linting"
	@echo "make format         - Format code"
	@echo "make clean          - Clean up files"
	@echo "make backup-db      - Backup database"
	@echo "make restore-db     - Restore database"
	@echo "make create-tenant  - Create new tenant"

# Docker commands
build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Ambivare ERP is running!"
	@echo "Access the application at: http://localhost"
	@echo "Admin panel: http://localhost/admin"
	@echo "API docs: http://localhost/api/docs"
	@echo "Flower (Celery monitoring): http://localhost:5555"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-web:
	docker-compose logs -f web

logs-celery:
	docker-compose logs -f celery_worker

# Django commands
shell:
	docker-compose exec web python manage.py shell

bash:
	docker-compose exec web bash

migrate:
	docker-compose exec web python manage.py migrate

makemigrations:
	docker-compose exec web python manage.py makemigrations

createsuperuser:
	docker-compose exec web python manage.py createsuperuser

collectstatic:
	docker-compose exec web python manage.py collectstatic --noinput

# Create new tenant
create-tenant:
	@read -p "Enter tenant name: " name; \
	read -p "Enter tenant slug: " slug; \
	read -p "Enter tenant email: " email; \
	read -p "Enter domain (e.g., tenant.ambivare.com): " domain; \
	docker-compose exec web python manage.py shell -c "\
from tenants.models import Tenant, Domain; \
tenant = Tenant(schema_name='$$slug', name='$$name', slug='$$slug', email='$$email'); \
tenant.save(); \
domain = Domain(domain='$$domain', tenant=tenant, is_primary=True); \
domain.save(); \
print(f'Tenant {tenant.name} created successfully!');"

# Testing
test:
	docker-compose exec web python manage.py test

test-coverage:
	docker-compose exec web coverage run --source='.' manage.py test
	docker-compose exec web coverage report
	docker-compose exec web coverage html

# Code quality
lint:
	docker-compose exec web flake8 .
	docker-compose exec web pylint **/*.py

format:
	docker-compose exec web black .
	docker-compose exec web isort .

# Database management
backup-db:
	@mkdir -p backups
	@filename="backups/ambivare_backup_$$(date +%Y%m%d_%H%M%S).sql"
	docker-compose exec -T postgres pg_dump -U postgres ambivare_erp > $$filename
	@echo "Database backed up to: $$filename"

restore-db:
	@read -p "Enter backup filename: " filename; \
	docker-compose exec -T postgres psql -U postgres ambivare_erp < $$filename
	@echo "Database restored from: $$filename"

# Cleanup
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -delete
	find . -type f -name '.coverage' -delete
	find . -type d -name 'htmlcov' -delete
	find . -type d -name '*.egg-info' -delete

# Production deployment
deploy-production:
	@echo "Deploying to production..."
	# Add your production deployment commands here
	# e.g., git push production main
	# ssh server 'cd /app && docker-compose pull && docker-compose up -d'

# Development setup
dev-setup:
	cp .env.example .env
	@echo "Please edit .env file with your configuration"
	make build
	make up
	make migrate
	make createsuperuser

# Generate secret key
generate-secret:
	@python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Check deployment readiness
check-deploy:
	docker-compose exec web python manage.py check --deploy

# Monitor services
monitor:
	watch -n 2 docker-compose ps

# View Django logs
django-logs:
	docker-compose exec web tail -f logs/debug.log

# Celery commands
celery-status:
	docker-compose exec celery_worker celery -A ambivare_erp inspect stats

celery-purge:
	docker-compose exec celery_worker celery -A ambivare_erp purge -f