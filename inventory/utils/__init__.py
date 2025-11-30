"""
Utility modules for Home Inventory application.

This module contains:
- Cache utilities (cache.py)
- Query optimization utilities (queries.py)
"""
from .cache import (
    get_cache_key,
    cache_statistics,
    invalidate_cache_pattern,
    invalidate_location_cache,
    invalidate_item_cache,
    invalidate_user_cache,
    get_cached_or_set,
    CACHE_TIMEOUT_SHORT,
    CACHE_TIMEOUT_MEDIUM,
    CACHE_TIMEOUT_LONG,
    CACHE_TIMEOUT_STATS,
    CACHE_KEY_STATS,
    CACHE_KEY_LOCATION,
    CACHE_KEY_ITEM,
    CACHE_KEY_USER,
    CACHE_KEY_CATEGORY,
    CACHE_KEY_TAG,
)
from .queries import (
    optimize_location_queryset,
    optimize_item_queryset,
    optimize_itemlog_queryset,
    optimize_category_queryset,
    optimize_tag_queryset,
    get_optimized_statistics,
)

__all__ = [
    # Cache utilities
    'get_cache_key',
    'cache_statistics',
    'invalidate_cache_pattern',
    'invalidate_location_cache',
    'invalidate_item_cache',
    'invalidate_user_cache',
    'get_cached_or_set',
    'CACHE_TIMEOUT_SHORT',
    'CACHE_TIMEOUT_MEDIUM',
    'CACHE_TIMEOUT_LONG',
    'CACHE_TIMEOUT_STATS',
    'CACHE_KEY_STATS',
    'CACHE_KEY_LOCATION',
    'CACHE_KEY_ITEM',
    'CACHE_KEY_USER',
    'CACHE_KEY_CATEGORY',
    'CACHE_KEY_TAG',
    # Query utilities
    'optimize_location_queryset',
    'optimize_item_queryset',
    'optimize_itemlog_queryset',
    'optimize_category_queryset',
    'optimize_tag_queryset',
    'get_optimized_statistics',
]

