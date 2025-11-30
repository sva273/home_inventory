from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Item, ItemLog, Location, LocationShare, ItemShare
from .utils import invalidate_location_cache, invalidate_item_cache, invalidate_user_cache
from .notifications import (
    notify_item_created, notify_item_updated, notify_item_moved,
    notify_location_shared, notify_item_shared, notify_share_revoked
)
from .analytics.services import track_event

User = get_user_model()

# Store old location before save for move notifications
_item_old_locations = {}


@receiver(pre_save, sender=Item)
def store_old_location(sender, instance, **kwargs):
    """Store old location before save for move notifications"""
    if instance.pk:
        try:
            old_item = Item.objects.get(pk=instance.pk)
            _item_old_locations[instance.pk] = old_item.location
        except Item.DoesNotExist:
            pass


@receiver(post_save, sender=Item)
def create_item_log(sender, instance, created, **kwargs):
    """Automatically create log entry when item is created or updated"""
    # Try to get user from instance if it was set during save
    user = getattr(instance, '_current_user', None)
    
    if created:
        # Item was created
        ItemLog.objects.create(
            item=instance,
            action='created',
            details=f'Item "{instance.name}" was created in {instance.location.name if instance.location else "no location"}',
            user=user
        )
        # Create notifications
        notify_item_created(instance, user)
        # Track analytics event
        if user:
            track_event(user=user, event_type='item_created', content_object=instance)
        # Invalidate cache
        invalidate_item_cache()
        if instance.location:
            invalidate_location_cache(instance.location.id)
        if instance.owner:
            invalidate_user_cache(instance.owner.id)
    else:
        # Item was updated - check what changed
        old_location = _item_old_locations.pop(instance.pk, None) if instance.pk else None
        
        if 'update_fields' in kwargs and kwargs['update_fields']:
            # Only log if significant fields changed
            if 'location' in kwargs['update_fields']:
                ItemLog.objects.create(
                    item=instance,
                    action='moved',
                    details=f'Item moved to {instance.location.name if instance.location else "no location"}',
                    user=user
                )
                # Create notifications for move
                notify_item_moved(instance, old_location, instance.location, user)
                # Invalidate cache for old and new locations
                invalidate_location_cache()
            elif any(field in kwargs['update_fields'] for field in ['name', 'description', 'quantity', 'condition']):
                ItemLog.objects.create(
                    item=instance,
                    action='updated',
                    details='Item details were updated',
                    user=user
                )
                # Create notifications for update
                changes = [field for field in kwargs['update_fields'] if field in ['name', 'description', 'quantity', 'condition']]
                notify_item_updated(instance, user, changes=changes)
                # Track analytics event
                if user:
                    track_event(user=user, event_type='item_updated', content_object=instance)
            # Invalidate item cache
            invalidate_item_cache(instance.id)
            if instance.owner:
                invalidate_user_cache(instance.owner.id)


@receiver(post_delete, sender=Item)
def log_item_deletion(sender, instance, **kwargs):
    """Log when item is deleted"""
    # Note: We can't create ItemLog here because item is already deleted
    # This is a limitation - consider using soft delete instead
    # Track analytics event (before deletion, we still have the object)
    # Note: We can't track with content_object since it's being deleted
    # Invalidate cache
    invalidate_item_cache()
    if instance.location:
        invalidate_location_cache(instance.location.id)
    if instance.owner:
        invalidate_user_cache(instance.owner.id)


@receiver(pre_save, sender=Location)
def validate_location_hierarchy(sender, instance, **kwargs):
    """Validate that location doesn't create circular references"""
    if instance.parent:
        # Check for circular reference
        current = instance.parent
        depth = 0
        max_depth = 10  # Prevent infinite loops
        
        while current and depth < max_depth:
            if current.id == instance.id:
                raise ValueError("Circular reference detected: location cannot be its own parent")
            current = current.parent
            depth += 1


@receiver(post_save, sender=Location)
def invalidate_location_cache_on_save(sender, instance, **kwargs):
    """Invalidate cache when location is saved"""
    created = kwargs.get('created', False)
    user = getattr(instance, '_current_user', None)
    
    # Track analytics event
    if created and user:
        track_event(user=user, event_type='location_created', content_object=instance)
    elif not created and user:
        track_event(user=user, event_type='location_updated', content_object=instance)
    
    invalidate_location_cache(instance.id)
    if instance.parent:
        invalidate_location_cache(instance.parent.id)
    if instance.owner:
        invalidate_user_cache(instance.owner.id)


@receiver(post_delete, sender=Location)
def invalidate_location_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when location is deleted"""
    invalidate_location_cache()
    if instance.owner:
        invalidate_user_cache(instance.owner.id)


@receiver(post_save, sender=LocationShare)
def notify_location_share_created(sender, instance, created, **kwargs):
    """Create notification when location is shared"""
    if created:
        created_by = instance.created_by or instance.location.owner
        notify_location_shared(instance, created_by)


@receiver(post_save, sender=ItemShare)
def notify_item_share_created(sender, instance, created, **kwargs):
    """Create notification when item is shared"""
    if created:
        created_by = instance.created_by or instance.item.owner
        notify_item_shared(instance, created_by)


@receiver(post_delete, sender=LocationShare)
def notify_location_share_revoked(sender, instance, **kwargs):
    """Create notification when location share is revoked"""
    notify_share_revoked(
        user=instance.user,
        object_type='location',
        object_name=instance.location.name,
        revoked_by=instance.location.owner
    )


@receiver(post_delete, sender=ItemShare)
def notify_item_share_revoked(sender, instance, **kwargs):
    """Create notification when item share is revoked"""
    notify_share_revoked(
        user=instance.user,
        object_type='item',
        object_name=instance.item.name,
        revoked_by=instance.item.owner
    )

