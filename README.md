# Ambivare ERP - Multi-Enterprise SaaS Sales ERP Platform

A comprehensive, production-ready multi-tenant SaaS Sales ERP system built with Django, Django REST Framework, PostgreSQL, Redis, Celery, and Docker.

## 🚀 Features

### Core Modules

#### 🏢 Multi-Tenancy
- Subdomain-based tenant isolation (company1.ambivare.com)
- Complete data isolation between tenants
- Tenant-specific settings and customization
- Automated tenant provisioning

#### 👥 User & Role Management
- Role-based access control (Admin, Manager, Sales Executive, Viewer)
- Email invitation system
- Team hierarchy management
- Activity tracking and audit logs

#### 💼 Sales CRM
- **Lead Management**: Capture, track, score, and convert leads
- **Customer Management**: 360° customer view with contacts and history
- **Deal Pipeline**: Visual Kanban board with customizable stages
- **Activities**: Tasks, calls, meetings, and follow-ups
- **Sales Analytics**: Real-time dashboards and reports

#### 💰 Billing & Invoicing
- Professional quotations with PDF generation
- Automated invoicing with payment tracking
- Multiple tax configurations
- Payment gateway integration (Stripe & Razorpay)

#### 📦 Product Management
- Product catalog with variants
- Category management
- Dynamic pricing rules
- Inventory tracking

#### 📊 Analytics & Reporting
- Sales performance dashboards
- Revenue forecasting
- Team performance metrics
- Custom report builder
- Data export capabilities

### SaaS Platform Features

#### 💳 Subscription Management
- Flexible pricing tiers (Starter, Pro, Enterprise)
- Usage-based limits and metering
- Free trial management
- Automated billing cycles

#### 🔔 Notifications & Automation
- Multi-channel notifications (Email, SMS, WhatsApp)
- Rule-based workflow automation
- Scheduled reminders and follow-ups
- Email templates with personalization

#### 🔌 Integrations
- REST API with OpenAPI documentation
- Webhook support for real-time events
- Email provider integration (SMTP, Gmail, Outlook)
- SMS/WhatsApp via Twilio
- Accounting software connectors

## 📋 Prerequisites

- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- 4GB RAM minimum
- 20GB disk space

## 🛠️ Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/ambivare-erp.git
cd ambivare-erp
```

### 2. Set up environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start with Docker
```bash
make dev-setup  # First time setup
# OR
make up         # Start services
```

### 4. Access the application
- Main App: http://localhost
- Admin Panel: http://localhost/admin
- API Docs: http://localhost/api/docs
- Celery Monitor: http://localhost:5555

Default credentials:
- Email: admin@ambivare.com
- Password: admin123

## 🏗️ Architecture

### Technology Stack
- **Backend**: Django 5.0, Django REST Framework
- **Database**: PostgreSQL with django-tenants
- **Cache/Queue**: Redis
- **Task Processing**: Celery with Beat scheduler
- **Web Server**: Nginx + Gunicorn
- **Frontend**: HTMX + Alpine.js + Bootstrap 5
- **Container**: Docker & Docker Compose

### Project Structure
```
ambivare_erp/
├── accounts/          # User authentication and management
├── sales/            # CRM and sales pipeline
├── products/         # Product catalog
├── billing/          # Invoicing and payments
├── tasks/            # Task management
├── analytics/        # Reports and dashboards
├── integrations/     # Third-party integrations
├── tenants/          # Multi-tenancy management
├── templates/        # HTML templates
├── static/           # CSS, JS, images
├── docker/           # Docker configurations
└── requirements.txt  # Python dependencies
```

## 📝 API Documentation

### Authentication
```bash
# Login
curl -X POST http://localhost/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Returns JWT tokens
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### API Endpoints
- `/api/auth/` - Authentication endpoints
- `/api/sales/` - Sales CRM endpoints
- `/api/products/` - Product management
- `/api/billing/` - Billing and invoicing
- `/api/tasks/` - Task management
- `/api/analytics/` - Analytics and reports

Full API documentation available at `/api/docs/`

## 🔧 Development

### Running locally without Docker
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Running tests
```bash
make test                 # Run all tests
make test-coverage       # Run with coverage report
```

### Code quality
```bash
make lint                # Run linting
make format              # Format code
```

## 🚀 Deployment

### Production with Docker
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Environment Variables
Key environment variables for production:
- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to False
- `ALLOWED_HOSTS`: Your domains
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Redis connection
- `STRIPE_SECRET_KEY`: Stripe API key
- `RAZORPAY_KEY_SECRET`: Razorpay API key
- `EMAIL_HOST_PASSWORD`: SMTP password

## 📊 Usage Limits by Plan

| Feature | Starter | Professional | Enterprise |
|---------|---------|--------------|------------|
| Users | 5 | 20 | Unlimited |
| Leads | 500 | 5,000 | Unlimited |
| Storage | 5 GB | 25 GB | 100 GB |
| API Calls | 10k/month | 100k/month | Unlimited |
| Support | Email | Priority | Dedicated |

## 🔐 Security

- HTTPS enforced in production
- CSRF protection
- XSS protection
- SQL injection prevention
- Rate limiting on sensitive endpoints
- Regular security updates
- GDPR compliant data handling

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

- Documentation: [docs.ambivare.com](https://docs.ambivare.com)
- Email: support@ambivare.com
- Issues: GitHub Issues

## 🙏 Acknowledgments

Built with love using:
- Django & Django REST Framework
- PostgreSQL & Redis
- Bootstrap & HTMX
- All the amazing open-source libraries

---

**Made with ❤️ by Ambivare Team**