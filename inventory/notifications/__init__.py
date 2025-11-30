"""
Notification module for Home Inventory application.

This module contains:
- Services for creating notifications (services.py)
- Context processors for notifications (context_processors.py)
"""
from .services import (
    create_notification,
    notify_item_created,
    notify_item_updated,
    notify_item_moved,
    notify_location_shared,
    notify_item_shared,
    notify_share_revoked,
)
from .context_processors import notifications

__all__ = [
    # Services
    'create_notification',
    'notify_item_created',
    'notify_item_updated',
    'notify_item_moved',
    'notify_location_shared',
    'notify_item_shared',
    'notify_share_revoked',
    # Context processors
    'notifications',
]

