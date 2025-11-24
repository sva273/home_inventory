# 🏠 Home Inventory Management System

[![GitHub stars](https://img.shields.io/github/stars/sva273/home_inventory.svg?style=social&label=Star)](https://github.com/sva273/home_inventory)
[![GitHub forks](https://img.shields.io/github/forks/sva273/home_inventory.svg?style=social&label=Fork)](https://github.com/sva273/home_inventory/fork)

> ⭐ **If you find this project useful, please consider giving it a star on GitHub!** ⭐

A Django-based web application for managing your home inventory. Organize your items by rooms, boxes, and locations with an intuitive interface and powerful search capabilities.

## Features

- 📦 **Hierarchical Location System**: Organize items by rooms, boxes, and sub-locations
- 🏷️ **Room Types**: Categorize locations by room type (Living Room, Kitchen, Children's Rooms, Office, Attic)
- 📱 **QR Code Generation**: Automatic QR code generation for boxes
- 🔍 **Advanced Search**: Search across locations and items
- 📊 **Statistics Dashboard**: View inventory statistics at a glance
- 🖼️ **Image Support**: Upload images for items
- 📝 **Automatic Activity Logs**: Automatic logging of all item actions via Django signals
- 🎨 **Modern UI**: Beautiful, responsive design with gradient backgrounds
- 🔌 **REST API**: Full REST API with Swagger documentation
- 🔒 **API Security**: Token-based authentication with cache storage
- 🎯 **API Versioning**: Versioned API endpoints (v1)
- 🧪 **Test Coverage**: Comprehensive test suite
- ✅ **Data Validation**: Built-in validation for models and forms
- 🎨 **Enhanced Admin**: Grappelli-powered admin interface
- 🌍 **Multi-language Support**: English, German, and Russian translations

## Tech Stack

- **Backend**: Django 5.2.8
- **API**: Django REST Framework 3.14+
- **API Documentation**: drf-yasg (Swagger/OpenAPI)
- **Admin UI**: django-grappelli
- **Database**: SQLite (default, can be changed to PostgreSQL/MySQL)
- **Environment Variables**: python-decouple
- **Filtering**: django-filter
- **Frontend**: HTML, CSS (no JavaScript framework required)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd home_inventory
```

### Step 2: Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration

Create a `.env` file in the project root:

```bash
SECRET_KEY=your-secret-key-here
```

You can generate a secret key using:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Step 5: Database Setup

```bash
python manage.py migrate
```

### Step 6: Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### Step 7: Generate Test Data (Optional)

```bash
python manage.py generate_test_data
```

To clear existing data and regenerate:

```bash
python manage.py generate_test_data --clear
```

### Step 8: Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## Project Structure

```
home_inventory/
├── home_inventory/          # Django project settings
│   ├── settings.py         # Project configuration
│   ├── urls.py             # URL routing
│   └── wsgi.py             # WSGI configuration
├── inventory/              # Main application
│   ├── models.py          # Database models (Location, Item, ItemLog)
│   ├── views.py           # Web view functions (HTML)
│   ├── api_views.py       # REST API ViewSets
│   ├── serializers.py     # API serializers
│   ├── api_urls.py        # API URL routing
│   ├── admin.py           # Django admin configuration
│   ├── choices.py         # Choice fields (room types, conditions, actions)
│   ├── signals.py         # Django signals for automatic logging
│   ├── services.py        # Business logic services
│   ├── tests/             # Test suite
│   │   └── test_models.py
│   ├── management/
│   │   └── commands/
│   │       └── generate_test_data.py  # Test data generator
│   └── migrations/        # Database migrations
├── services/              # Service modules
│   └── qr_service.py     # QR code generation service
├── templates/             # HTML templates
│   ├── base.html         # Base template with language switcher
│   └── inventory/
│       ├── home.html
│       ├── location_list.html
│       ├── location_detail.html
│       ├── item_list.html
│       ├── item_detail.html
│       ├── room_view.html
│       └── search.html
├── locale/                # Translation files
│   ├── de/               # German translations
│   └── ru/               # Russian translations
├── media/                 # User-uploaded files (images, QR codes)
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── TRANSLATION_GUIDE.md   # Translation guide
└── .env                   # Environment variables (not in git)
```

## Models

### Location
Represents a physical location where items can be stored:
- **Fields**: name, room_type, parent (self-reference), is_box, qr_code
- **Features**: Hierarchical structure, automatic QR code generation for boxes

### Item
Represents an item in the inventory:
- **Fields**: name, description, quantity, condition, location, image, timestamps
- **Features**: Image upload, condition tracking, location assignment
- **Validation**: Quantity must be between 1-10000
- **Condition Choices**: excellent, good, fair, damaged, poor

### ItemLog
Tracks all actions performed on items (automatically created via signals):
- **Fields**: item, action, details, timestamp
- **Actions**: created, moved, deleted, updated
- **Auto-logging**: Automatically logs when items are created, updated, or moved

## URLs

### Web Interface (v1)
- `/` or `/v1/` - Home page with overview (redirects to v1)
- `/v1/locations/` - List all locations with filters
- `/v1/locations/<id>/` - Location detail page
- `/v1/items/` - List all items with filters
- `/v1/items/<id>/` - Item detail page
- `/v1/room/<room_type>/` - View items by room type
- `/v1/search/` - Universal search

### REST API (v1)

**Authentication Required**: All API endpoints require token authentication. See [API_AUTHENTICATION.md](API_AUTHENTICATION.md) for details.

**Authentication Endpoints**:
- `/v1/api/auth/token/` - Obtain authentication token (POST)
- `/v1/api/auth/revoke/` - Revoke current token (POST)
- `/v1/api/auth/refresh/` - Refresh token expiration (POST)
- `/v1/api/auth/info/` - Get current user info (GET)

**Data Endpoints** (require authentication):
- `/v1/api/locations/` - List/Create locations (GET, POST)
- `/v1/api/locations/<id>/` - Location detail (GET, PUT, PATCH, DELETE)
- `/v1/api/locations/<id>/items/` - Items in location (GET)
- `/v1/api/locations/<id>/children/` - Child locations (GET)
- `/v1/api/items/` - List/Create items (GET, POST)
- `/v1/api/items/<id>/` - Item detail (GET, PUT, PATCH, DELETE)
- `/v1/api/items/<id>/logs/` - Item logs (GET)
- `/v1/api/logs/` - List all logs (GET)

### API Documentation
- `/swagger/` - Swagger UI documentation
- `/redoc/` - ReDoc documentation
- `/swagger.json` - OpenAPI JSON schema
- `/swagger.yaml` - OpenAPI YAML schema

### Admin & Utilities
- `/admin/` - Django admin panel (Grappelli)
- `/grappelli/` - Grappelli static files

## API Security

The API uses **token-based authentication** with tokens stored in Django cache. All API endpoints require authentication (except authentication endpoints).

**Quick Start:**
1. Obtain a token: `POST /v1/api/auth/token/` with username and password
2. Include token in requests: `Authorization: Token <your_token>`

See [API_AUTHENTICATION.md](API_AUTHENTICATION.md) for complete authentication guide, examples, and configuration details.

## API Usage Examples

**Basic example with authentication:**

```bash
# 1. Get token
curl -X POST http://127.0.0.1:8000/v1/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 2. Use token in API requests
curl http://127.0.0.1:8000/v1/api/locations/ \
  -H "Authorization: Token <your_token>"
```

For complete examples (Python, JavaScript, curl) and detailed authentication guide, see [API_AUTHENTICATION.md](API_AUTHENTICATION.md).

**API Documentation:**
- `/swagger/` - Swagger UI (interactive API documentation)
- `/redoc/` - ReDoc documentation

## Choices & Enums

### Room Types
- `living_room` - Living Room
- `kitchen` - Kitchen
- `children_room_a` - Children's Room A
- `children_room_n` - Children's Room N
- `office` - Office
- `attic` - Attic

### Item Conditions
- `excellent` - Excellent
- `good` - Good
- `fair` - Fair
- `damaged` - Damaged
- `poor` - Poor

### Log Actions
- `created` - Item was created
- `updated` - Item was updated
- `moved` - Item was moved to different location
- `deleted` - Item was deleted

## Management Commands

### Generate Test Data

```bash
python manage.py generate_test_data
```

This command creates:
- 6 main rooms (one for each room type)
- 8 boxes in different rooms
- 6 sub-locations (shelves, cabinets, etc.)
- 32 sample items
- Activity logs for some items

Options:
- `--clear`: Clear existing data before generating new data

## Admin Panel

Access the enhanced Django admin panel (Grappelli) at `/admin/` to:
- Manage locations and items with modern UI
- View statistics and counts
- See inline related objects (items in locations, children locations)
- Filter and search records
- View QR codes and images
- Bulk actions (mark items as good/damaged condition)
- Custom fieldsets for better organization

## Features in Detail

### Hierarchical Locations
- Create parent-child relationships between locations
- Navigate through location hierarchy with breadcrumbs
- View all items in a location and its children

### QR Code Generation
- Automatic QR code generation for boxes
- QR codes stored in `media/qr/` directory
- Displayed in admin panel and detail pages

### Automatic Logging (Signals)
- Automatic log creation when items are created
- Automatic log creation when items are updated
- Automatic log creation when items are moved
- Prevents circular references in location hierarchy

### REST API
- Full CRUD operations for all models
- **Token-based authentication** with cache storage (see [API_AUTHENTICATION.md](API_AUTHENTICATION.md))
- Filtering, searching, and ordering
- Pagination (20 items per page)
- Nested endpoints (items in location, logs for item)
- OpenAPI/Swagger documentation

### Search Functionality
- Search across location names and room types
- Search across item names and descriptions
- Combined results display
- API search endpoints

### Filtering
- Filter locations by room type, box status
- Filter items by location, condition
- Sort by various fields
- API filtering via query parameters

## Development

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test inventory.tests.test_models

# Run with verbose output
python manage.py test --verbosity=2
```

Test coverage includes:
- Model validation
- Signal handlers (automatic logging)
- Location hierarchy (circular reference prevention)
- Item quantity validation

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files (for production)

```bash
python manage.py collectstatic
```

## Internationalization (i18n)

The application supports three languages:
- 🇬🇧 **English** (en) - Default
- 🇩🇪 **German** (de) - Deutsch
- 🇷🇺 **Russian** (ru) - Русский

### Language Switcher

Users can switch languages using the language switcher in the top-right corner of every page. The language preference is saved in the session.

### Adding Translations

1. Mark strings for translation in code:
   ```python
   from django.utils.translation import gettext_lazy as _
   _('String to translate')
   ```

2. Extract translatable strings:
   ```bash
   python manage.py makemessages -l de  # For German
   python manage.py makemessages -l ru  # For Russian
   ```

3. Edit translation files in `locale/<lang>/LC_MESSAGES/django.po`

4. Compile translations:
   ```bash
   python manage.py compilemessages
   ```

See `TRANSLATION_GUIDE.md` for detailed instructions.

## Production Deployment

Before deploying to production:

1. Set `DEBUG = False` in `settings.py`
2. Configure `ALLOWED_HOSTS`
3. Use a production database (PostgreSQL recommended)
4. Set up proper static file serving
5. Configure media file storage (AWS S3, etc.)
6. Use environment variables for sensitive data
7. Set up SSL/HTTPS
8. Configure proper logging
9. **Configure Redis for token cache** (for distributed systems):
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
       }
   }
   ```
10. Review and configure API security settings

## Environment Variables

Required in `.env`:
- `SECRET_KEY` - Django secret key

Optional (can be added):
- `DEBUG` - Debug mode (default: True)
- `DATABASE_URL` - Database connection string
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the MIT License.

## Author

Created for home inventory management.

## Support

For issues and questions, please open an issue in the repository.

## Key Improvements

- ✅ **Automatic Logging**: Django signals automatically create logs for item actions
- ✅ **Data Validation**: Built-in validation for quantities, conditions, and hierarchy
- ✅ **Test Coverage**: Comprehensive test suite for models and signals
- ✅ **API Versioning**: Versioned API endpoints for future compatibility
- ✅ **Enhanced Admin**: Grappelli provides modern admin interface
- ✅ **API Documentation**: Swagger/OpenAPI for easy API exploration
- ✅ **Multi-language Support**: Full i18n support for 3 languages
- ✅ **API Security**: Token-based authentication with cache storage

## Additional Resources

- See `IMPROVEMENTS.md` for a list of potential future enhancements
- See `API_AUTHENTICATION.md` for complete API authentication guide
- See `TRANSLATION_GUIDE.md` for translation management instructions
- API documentation available at `/swagger/` when server is running
- Check `inventory/tests/` for test examples

---

**Note**: This is a development project. For production use, ensure proper security measures, database backups, and deployment best practices are followed.

