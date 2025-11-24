# API Authentication Guide

## Overview

The Home Inventory API uses token-based authentication with tokens stored in Django cache. This provides a fast and scalable authentication mechanism without requiring database queries for token validation.

## Getting Started

### 1. Obtain a Token

To use the API, you first need to obtain an authentication token by providing your username and password.

**Endpoint:** `POST /v1/api/auth/token/`

**Request:**
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "token": "abc123def456...",
    "user_id": 1,
    "username": "your_username",
    "email": "user@example.com"
}
```

**Example using curl:**
```bash
curl -X POST http://localhost:8000/v1/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 2. Use the Token

Include the token in the `Authorization` header of all API requests:

**Header Format:**
```
Authorization: Token <your_token>
```

**Example using curl:**
```bash
curl -X GET http://localhost:8000/v1/api/locations/ \
  -H "Authorization: Token abc123def456..."
```

## API Endpoints

### Authentication Endpoints

#### Obtain Token
- **URL:** `/v1/api/auth/token/`
- **Method:** `POST`
- **Authentication:** Not required
- **Description:** Get an authentication token

#### Revoke Token
- **URL:** `/v1/api/auth/revoke/`
- **Method:** `POST`
- **Authentication:** Required
- **Description:** Revoke your current token (logout)

#### Refresh Token
- **URL:** `/v1/api/auth/refresh/`
- **Method:** `POST`
- **Authentication:** Required
- **Description:** Extend token expiration time

#### Token Info
- **URL:** `/v1/api/auth/info/`
- **Method:** `GET`
- **Authentication:** Required
- **Description:** Get information about current authenticated user

### Protected Endpoints

All other API endpoints require authentication:
- `/v1/api/locations/` - Location management
- `/v1/api/items/` - Item management
- `/v1/api/logs/` - Item log viewing

## Token Expiration

- Tokens expire after **7 days** by default
- Use the refresh endpoint to extend expiration
- Tokens are stored in cache and automatically cleaned up when expired

## Error Responses

### 401 Unauthorized
```json
{
    "error": "Invalid or expired token."
}
```

### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```

## Using Swagger UI

1. Navigate to `/swagger/` in your browser
2. Click the "Authorize" button
3. Enter your token in the format: `Token <your_token>`
4. Click "Authorize" to authenticate
5. All API requests will now include your token

## Python Example

```python
import requests

# Get token
response = requests.post(
    'http://localhost:8000/v1/api/auth/token/',
    json={'username': 'admin', 'password': 'admin123'}
)
token = response.json()['token']

# Use token for API requests
headers = {'Authorization': f'Token {token}'}
locations = requests.get(
    'http://localhost:8000/v1/api/locations/',
    headers=headers
)
print(locations.json())
```

## JavaScript Example

```javascript
// Get token
const tokenResponse = await fetch('http://localhost:8000/v1/api/auth/token/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: 'admin', password: 'admin123'})
});
const {token} = await tokenResponse.json();

// Use token for API requests
const locationsResponse = await fetch('http://localhost:8000/v1/api/locations/', {
    headers: {'Authorization': `Token ${token}`}
});
const locations = await locationsResponse.json();
```

## Security Notes

- Tokens are stored in Django cache (in-memory by default)
- For production, consider using Redis for distributed caching
- Tokens automatically expire after 7 days
- Always use HTTPS in production
- Never commit tokens to version control
- Store tokens securely on the client side

## Cache Configuration

By default, tokens are stored in local memory cache. For production with multiple servers, configure Redis:

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

