"""
Analytics module for tracking usage statistics and popular items/locations.
"""
from .services import (
    track_event,
    get_popular_items,
    get_popular_locations,
    get_usage_statistics,
    get_user_activity,
    get_item_analytics,
    get_location_analytics,
)
from .decorators import track_view

__all__ = [
    'track_event',
    'get_popular_items',
    'get_popular_locations',
    'get_usage_statistics',
    'get_user_activity',
    'get_item_analytics',
    'get_location_analytics',
    'track_view',
]

