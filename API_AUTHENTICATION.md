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

### Step 1: Obtain a Token

1. Navigate to `/swagger/` in your browser
2. Find the `POST /v1/api/auth/token/` endpoint
3. Click "Try it out"
4. Enter your credentials in the request body:
   ```json
   {
       "username": "your_username",
       "password": "your_password"
   }
   ```
5. Click "Execute"
6. Copy the `token` value from the response (e.g., `"token": "abc123def456..."`)

### Step 2: Authorize in Swagger

1. Click the "Authorize" button (🔒) at the top right of the Swagger UI
2. In the "Value" field, enter: `Token <your_token>` (replace `<your_token>` with the actual token you copied)
   - **Important**: You MUST include the word "Token" followed by a space, then your token
   - Example: `Token abc123def456ghi789...`
   - **NOT**: `abc123def456...` (missing "Token " prefix)
   - **NOT**: `Tokenabc123...` (missing space after "Token")
3. Click "Authorize"
4. Click "Close"
5. You should see a green checkmark (✓) next to "Authorize" button indicating you're authenticated

### Step 3: Use Protected Endpoints

Now all API requests will automatically include your token. You can:
- Test any endpoint by clicking "Try it out"
- The token will be automatically included in the Authorization header
- You'll see a green "Authorized" indicator next to the "Authorize" button

### Troubleshooting

**Problem: Can't create token**
- Make sure you're using the correct username and password
- Check that the user account is active
- Verify the endpoint URL is correct: `/v1/api/auth/token/`

**Problem: Token not working / "Authentication credentials were not provided"**
- **Most common issue**: Make sure you entered the token in the correct format: `Token <your_token>` (with space after "Token")
  - Correct: `Token abc123def456...`
  - Wrong: `abc123def456...` (missing "Token " prefix)
  - Wrong: `Tokenabc123...` (missing space)
- Check that you clicked "Authorize" and "Close" after entering the token
- Verify the token is visible in the "Authorize" dialog (you should see it listed)
- Check that the token hasn't expired (tokens expire after 7 days)
- Try obtaining a new token
- Open browser Developer Tools (F12) → Network tab → Check the request headers to see if "Authorization: Token ..." is being sent

**Problem: "Authorize" button not visible**
- Refresh the Swagger UI page
- Check browser console for errors
- Make sure you're accessing `/swagger/` (not `/redoc/`)

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

