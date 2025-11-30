"""
Cache utilities for Home Inventory application.
"""
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from functools import wraps
import hashlib
import json


# Cache timeouts (in seconds)
CACHE_TIMEOUT_SHORT = 60  # 1 minute
CACHE_TIMEOUT_MEDIUM = 300  # 5 minutes
CACHE_TIMEOUT_LONG = 3600  # 1 hour
CACHE_TIMEOUT_STATS = 600  # 10 minutes


def get_cache_key(prefix, *args, **kwargs):
    """
    Generate a cache key from prefix and arguments.
    
    Args:
        prefix: Cache key prefix
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key
    
    Returns:
        str: Cache key
    """
    key_parts = [prefix]
    
    # Add positional arguments
    for arg in args:
        # Check if it's a user-like object with is_authenticated
        if hasattr(arg, 'is_authenticated'):
            # For authenticated users, use their ID
            if arg.is_authenticated and hasattr(arg, 'id'):
                try:
                    key_parts.append(str(arg.id))
                except (TypeError, AttributeError):
                    # Fallback for objects that have id but it's not accessible
                    key_parts.append('anonymous')
            else:
                # For anonymous users, use 'anonymous'
                key_parts.append('anonymous')
        elif hasattr(arg, 'id'):
            # For other objects with id (UUID, etc.)
            try:
                key_parts.append(str(arg.id))
            except (TypeError, AttributeError):
                key_parts.append(str(arg))
        else:
            key_parts.append(str(arg))
    
    # Add keyword arguments
    if kwargs:
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        key_parts.append(hashlib.md5(json.dumps(sorted_kwargs, sort_keys=True).encode()).hexdigest())
    
    return ':'.join(key_parts)


def cache_statistics(func):
    """
    Decorator to cache function results with statistics key.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Generate cache key based on function name and arguments
        cache_key = get_cache_key(f'stats:{func.__name__}', *args, **kwargs)
        
        # Try to get from cache
        result = cache.get(cache_key)
        if result is not None:
            return result
        
        # Call function and cache result
        result = func(*args, **kwargs)
        cache.set(cache_key, result, CACHE_TIMEOUT_STATS)
        return result
    
    return wrapper


def invalidate_cache_pattern(pattern):
    """
    Invalidate all cache keys matching a pattern.
    Note: This works best with Redis. For LocMemCache, it clears all.
    
    Args:
        pattern: Pattern to match (e.g., 'stats:*', 'location:*')
    """
    if pattern.endswith('*'):
        # For LocMemCache, we can't pattern match, so clear all
        # In production with Redis, you would use: cache.delete_pattern(pattern)
        cache.clear()
    else:
        cache.delete(pattern)


def invalidate_location_cache(location_id=None):
    """
    Invalidate cache related to locations.
    
    Args:
        location_id: Specific location ID, or None for all locations
    """
    if location_id:
        cache.delete(f'location:{location_id}')
        cache.delete(f'location:{location_id}:items')
        cache.delete(f'location:{location_id}:children')
    else:
        # Invalidate all location-related cache
        invalidate_cache_pattern('location:*')
        invalidate_cache_pattern('stats:*')


def invalidate_item_cache(item_id=None):
    """
    Invalidate cache related to items.
    
    Args:
        item_id: Specific item ID, or None for all items
    """
    if item_id:
        cache.delete(f'item:{item_id}')
        cache.delete(f'item:{item_id}:logs')
    else:
        # Invalidate all item-related cache
        invalidate_cache_pattern('item:*')
        invalidate_cache_pattern('stats:*')


def invalidate_user_cache(user_id=None):
    """
    Invalidate cache related to a specific user.
    
    Args:
        user_id: Specific user ID, or None for all users
    """
    if user_id:
        cache.delete(f'user:{user_id}:locations')
        cache.delete(f'user:{user_id}:items')
    else:
        invalidate_cache_pattern('user:*')
        invalidate_cache_pattern('stats:*')


def get_cached_or_set(key, callable_func, timeout=CACHE_TIMEOUT_MEDIUM):
    """
    Get value from cache or set it using callable.
    
    Args:
        key: Cache key
        callable_func: Function to call if cache miss
        timeout: Cache timeout in seconds
    
    Returns:
        Cached or computed value
    """
    value = cache.get(key)
    if value is None:
        value = callable_func()
        cache.set(key, value, timeout)
    return value


# Cache key prefixes
CACHE_KEY_STATS = 'stats'
CACHE_KEY_LOCATION = 'location'
CACHE_KEY_ITEM = 'item'
CACHE_KEY_USER = 'user'
CACHE_KEY_CATEGORY = 'category'
CACHE_KEY_TAG = 'tag'

