from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext as _
from ..models import Notification, LocationShare, ItemShare
import json

User = get_user_model()


def create_notification(user, notification_type, message, related_object=None, metadata=None):
    """
    Create a notification for a user.
    
    Args:
        user: User to notify
        notification_type: Type of notification (from NOTIFICATION_TYPE_CHOICES)
        message: Notification message
        related_object: Optional related object (Item, Location, etc.)
        metadata: Optional additional context data (dict)
    
    Returns:
        Created Notification instance
    """
    content_type = None
    object_id = None
    
    if related_object:
        content_type = ContentType.objects.get_for_model(related_object)
        object_id = related_object.id
    
    metadata_json = json.dumps(metadata) if metadata else ''
    
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        message=message,
        content_type=content_type,
        object_id=object_id,
        metadata=metadata_json
    )


def notify_item_created(item, created_by):
    """Create notifications when an item is created"""
    # Notify owner if different from creator
    if item.owner and item.owner != created_by:
        create_notification(
            user=item.owner,
            notification_type='item_created',
            message=_('New item "%(item_name)s" was added to your inventory') % {'item_name': item.name},
            related_object=item,
            metadata={'created_by': created_by.username if created_by else None}
        )
    
    # Notify users with shared access to the location
    if item.location:
        shares = LocationShare.objects.filter(location=item.location)
        for share in shares:
            if share.user != created_by:
                create_notification(
                    user=share.user,
                    notification_type='item_created',
                    message=_('New item "%(item_name)s" was added to shared location "%(location_name)s"') % {
                        'item_name': item.name,
                        'location_name': item.location.name
                    },
                    related_object=item,
                    metadata={'location': item.location.name, 'created_by': created_by.username if created_by else None}
                )


def notify_item_updated(item, updated_by, changes=None):
    """Create notifications when an item is updated"""
    # Notify owner if different from updater
    if item.owner and item.owner != updated_by:
        create_notification(
            user=item.owner,
            notification_type='item_updated',
            message=_('Item "%(item_name)s" was updated') % {'item_name': item.name},
            related_object=item,
            metadata={'updated_by': updated_by.username if updated_by else None, 'changes': changes}
        )
    
    # Notify users with shared access
    shares = ItemShare.objects.filter(item=item)
    for share in shares:
        if share.user != updated_by:
            create_notification(
                user=share.user,
                notification_type='item_updated',
                message=_('Shared item "%(item_name)s" was updated') % {'item_name': item.name},
                related_object=item,
                metadata={'updated_by': updated_by.username if updated_by else None, 'changes': changes}
            )


def notify_item_moved(item, old_location, new_location, moved_by):
    """Create notifications when an item is moved"""
    # Notify owner
    if item.owner and item.owner != moved_by:
        old_loc_name = old_location.name if old_location else _('no location')
        new_loc_name = new_location.name if new_location else _('no location')
        create_notification(
            user=item.owner,
            notification_type='item_moved',
            message=_('Item "%(item_name)s" was moved from "%(old_location)s" to "%(new_location)s"') % {
                'item_name': item.name,
                'old_location': old_loc_name,
                'new_location': new_loc_name
            },
            related_object=item,
            metadata={
                'old_location': old_location.name if old_location else None,
                'new_location': new_location.name if new_location else None,
                'moved_by': moved_by.username if moved_by else None
            }
        )
    
    # Notify users with access to old location
    if old_location:
        shares = LocationShare.objects.filter(location=old_location)
        for share in shares:
            if share.user != moved_by:
                create_notification(
                    user=share.user,
                    notification_type='item_moved',
                    message=_('Item "%(item_name)s" was moved from shared location "%(location_name)s"') % {
                        'item_name': item.name,
                        'location_name': old_location.name
                    },
                    related_object=item,
                    metadata={'old_location': old_location.name, 'moved_by': moved_by.username if moved_by else None}
                )
    
    # Notify users with access to new location
    if new_location:
        shares = LocationShare.objects.filter(location=new_location)
        for share in shares:
            if share.user != moved_by:
                create_notification(
                    user=share.user,
                    notification_type='item_moved',
                    message=_('Item "%(item_name)s" was moved to shared location "%(location_name)s"') % {
                        'item_name': item.name,
                        'location_name': new_location.name
                    },
                    related_object=item,
                    metadata={'new_location': new_location.name, 'moved_by': moved_by.username if moved_by else None}
                )


def notify_location_shared(location_share, shared_by):
    """Create notification when a location is shared"""
    create_notification(
        user=location_share.user,
        notification_type='location_shared',
        message=_('Location "%(location_name)s" was shared with you (%(role)s)') % {
            'location_name': location_share.location.name,
            'role': location_share.get_role_display()
        },
        related_object=location_share.location,
        metadata={
            'role': location_share.role,
            'shared_by': shared_by.username if shared_by else None
        }
    )


def notify_item_shared(item_share, shared_by):
    """Create notification when an item is shared"""
    create_notification(
        user=item_share.user,
        notification_type='item_shared',
        message=_('Item "%(item_name)s" was shared with you (%(role)s)') % {
            'item_name': item_share.item.name,
            'role': item_share.get_role_display()
        },
        related_object=item_share.item,
        metadata={
            'role': item_share.role,
            'shared_by': shared_by.username if shared_by else None
        }
    )


def notify_share_revoked(user, object_type, object_name, revoked_by):
    """Create notification when share access is revoked"""
    create_notification(
        user=user,
        notification_type='share_revoked',
        message=_('Your access to %(object_type)s "%(object_name)s" was revoked') % {
            'object_type': object_type,
            'object_name': object_name
        },
        metadata={
            'object_type': object_type,
            'object_name': object_name,
            'revoked_by': revoked_by.username if revoked_by else None
        }
    )

