import secrets
from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

User = get_user_model()

# Token expiration time (default: 7 days)
TOKEN_EXPIRATION = timedelta(days=7)
CACHE_KEY_PREFIX = 'api_token:'
USER_TOKEN_KEY_PREFIX = 'user_token:'


class CacheTokenAuthentication(BaseAuthentication):
    """
    Token authentication using Django cache.
    
    Tokens are stored in cache with format: 'api_token:{token}'
    User tokens are stored with format: 'user_token:{user_id}'
    """
    
    def authenticate(self, request):
        """
        Authenticate the request using token from header.
        
        Token should be in Authorization header: 'Token {token}' or just '{token}'
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None
        
        # Try to extract token
        # Handle formats: "Token <token>", "Bearer <token>", or just "<token>"
        parts = auth_header.split(' ', 1)
        
        if len(parts) == 2:
            # Has prefix: "Token <token>" or "Bearer <token>"
            auth_type, token = parts
            # Accept both 'Token' and 'Bearer' prefixes
            if auth_type.lower() not in ('token', 'bearer'):
                return None
        elif len(parts) == 1:
            # No prefix, just token
            token = parts[0]
        else:
            return None
        
        if not token or not token.strip():
            return None
        
        token = token.strip()
        
        # Get user_id from cache
        cache_key = f'{CACHE_KEY_PREFIX}{token}'
        user_id = cache.get(cache_key)
        
        if not user_id:
            raise AuthenticationFailed('Invalid or expired token.')
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found.')
        
        if not user.is_active:
            raise AuthenticationFailed('User account is disabled.')
        
        return (user, token)
    
    def authenticate_header(self, request):
        """Return a string to be used as the value of the `WWW-Authenticate` header."""
        return 'Token'


def generate_token():
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


def create_token(user):
    """
    Create a new token for user and store it in cache.
    
    Returns the token string.
    """
    # Delete old token if exists
    delete_user_token(user)
    
    # Generate new token
    token = generate_token()
    
    # Store token -> user_id mapping
    cache_key = f'{CACHE_KEY_PREFIX}{token}'
    cache.set(cache_key, user.id, timeout=int(TOKEN_EXPIRATION.total_seconds()))
    
    # Store user_id -> token mapping (for easy deletion)
    user_token_key = f'{USER_TOKEN_KEY_PREFIX}{user.id}'
    cache.set(user_token_key, token, timeout=int(TOKEN_EXPIRATION.total_seconds()))
    
    return token


def get_user_token(user):
    """Get token for user if exists."""
    user_token_key = f'{USER_TOKEN_KEY_PREFIX}{user.id}'
    return cache.get(user_token_key)


def delete_token(token):
    """Delete a token from cache."""
    cache_key = f'{CACHE_KEY_PREFIX}{token}'
    user_id = cache.get(cache_key)
    
    if user_id:
        cache.delete(cache_key)
        user_token_key = f'{USER_TOKEN_KEY_PREFIX}{user_id}'
        cache.delete(user_token_key)


def delete_user_token(user):
    """Delete token for a specific user."""
    user_token_key = f'{USER_TOKEN_KEY_PREFIX}{user.id}'
    token = cache.get(user_token_key)
    
    if token:
        cache_key = f'{CACHE_KEY_PREFIX}{token}'
        cache.delete(cache_key)
        cache.delete(user_token_key)


def refresh_token(token):
    """
    Refresh token expiration time.
    
    Returns True if token was refreshed, False if token doesn't exist.
    """
    cache_key = f'{CACHE_KEY_PREFIX}{token}'
    user_id = cache.get(cache_key)
    
    if not user_id:
        return False
    
    # Refresh both cache entries
    cache.set(cache_key, user_id, timeout=int(TOKEN_EXPIRATION.total_seconds()))
    user_token_key = f'{USER_TOKEN_KEY_PREFIX}{user_id}'
    cache.set(user_token_key, token, timeout=int(TOKEN_EXPIRATION.total_seconds()))
    
    return True

