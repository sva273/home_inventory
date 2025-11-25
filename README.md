# 🏠 Home Inventory Management System

[![GitHub stars](https://img.shields.io/github/stars/sva273/home_inventory.svg?style=social&label=Star)](https://github.com/sva273/home_inventory)
[![GitHub forks](https://img.shields.io/github/forks/sva273/home_inventory.svg?style=social&label=Fork)](https://github.com/sva273/home_inventory/fork)

> ⭐ **If you find this project useful, please consider giving it a star on GitHub!** ⭐

A Django-based web application for managing your home inventory. Organize your items by rooms, boxes, and locations with an intuitive interface and powerful search capabilities.

## Features

- 📦 Hierarchical location system (rooms, boxes, sub-locations)
- 🏷️ Room types (Living Room, Kitchen, Children's Rooms, Office, Attic)
- 📱 Automatic QR code generation for boxes
- 🔍 Advanced search across locations and items
- 📊 Statistics dashboard
- 🖼️ Image support for items
- 📝 Automatic activity logs via Django signals
- 🎨 Modern, responsive UI
- 🔌 REST API with Swagger documentation
- 🔒 Token-based authentication
- 🌍 Multi-language support (English, German, Russian)

## Tech Stack

- **Backend**: Django 5.2.8, Django REST Framework
- **API Docs**: drf-yasg (Swagger/OpenAPI)
- **Admin**: django-grappelli
- **Database**: SQLite (default, PostgreSQL/MySQL supported)

## Quick Start

```bash
# Clone repository
git clone https://github.com/sva273/home_inventory
cd home_inventory

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with SECRET_KEY
echo "SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" > .env

# Setup database
python manage.py migrate
python manage.py createsuperuser  # Optional
python manage.py generate_test_data  # Optional

# Run server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## Project Structure

```
home_inventory/
├── home_inventory/          # Django project settings
│   ├── settings.py         # Project configuration
│   ├── urls.py             # URL routing
│   ├── wsgi.py             # WSGI configuration
│   └── asgi.py             # ASGI configuration
├── inventory/              # Main application
│   ├── models.py          # Location, Item, ItemLog models
│   ├── views.py           # Web view functions
│   ├── api_views.py       # REST API ViewSets
│   ├── api_auth_views.py  # API authentication endpoints
│   ├── api_urls.py        # API URL routing
│   ├── serializers.py     # API serializers
│   ├── admin.py           # Admin configuration
│   ├── authentication.py  # Token authentication
│   ├── choices.py         # Choice fields
│   ├── signals.py         # Django signals
│   ├── services.py        # Business logic
│   ├── tests/             # Test suite
│   │   └── test_models.py
│   ├── management/
│   │   └── commands/
│   │       └── generate_test_data.py
│   └── migrations/        # Database migrations
├── services/              # Service modules
│   └── qr_service.py     # QR code generation
├── templates/            # HTML templates
│   ├── base.html
│   └── inventory/
├── locale/               # Translation files
│   ├── de/               # German
│   └── ru/               # Russian
├── media/                # User-uploaded files
├── manage.py             # Django management script
└── requirements.txt      # Python dependencies
```

## Models

- **Location**: Physical locations (rooms, boxes) with hierarchical structure
- **Item**: Inventory items with quantity, condition, images
- **ItemLog**: Automatic activity logs (created, updated, moved, deleted)

## URLs

### Web Interface
- `/v1/` - Home page
- `/v1/locations/` - List locations
- `/v1/items/` - List items
- `/v1/search/` - Universal search

### REST API
- `/v1/api/auth/token/` - Obtain token (POST)
- `/v1/api/locations/` - Locations CRUD
- `/v1/api/items/` - Items CRUD
- `/v1/api/logs/` - Activity logs

**API Documentation**: `/swagger/` (Swagger UI), `/redoc/` (ReDoc)

## API Authentication

All API endpoints require token authentication:

```bash
# 1. Get token
curl -X POST http://127.0.0.1:8000/v1/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 2. Use token
curl http://127.0.0.1:8000/v1/api/locations/ \
  -H "Authorization: Token <your_token>"
```

See [API_AUTHENTICATION.md](API_AUTHENTICATION.md) for complete guide.

## Management Commands

```bash
# Generate test data
python manage.py generate_test_data
python manage.py generate_test_data --clear  # Clear existing data first

# Run tests
python manage.py test

# Translations
python manage.py makemessages -l de  # German
python manage.py makemessages -l ru  # Russian
python manage.py compilemessages
```

## Production Deployment

1. Set `DEBUG = False` and configure `ALLOWED_HOSTS`
2. Use production database (PostgreSQL recommended)
3. Configure static/media file serving
4. Set up SSL/HTTPS
5. Configure Redis for token cache (distributed systems):
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
       }
   }
   ```

## Additional Resources

- [API_AUTHENTICATION.md](API_AUTHENTICATION.md) - Complete API authentication guide
- [TRANSLATION_GUIDE.md](TRANSLATION_GUIDE.md) - Translation management
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Future enhancements
- API docs: `/swagger/` when server is running

## Author

**Wjatscheslaw Schwab**

- GitHub: [@sva273](https://github.com/sva273)
- LinkedIn: [wjatscheslaw-schwab-15216a310](https://www.linkedin.com/in/wjatscheslaw-schwab-15216a310)

## License

MIT License

---

**Note**: For production use, ensure proper security measures, database backups, and deployment best practices are followed.
