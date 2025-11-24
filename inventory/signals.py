from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Item, ItemLog, Location


@receiver(post_save, sender=Item)
def create_item_log(sender, instance, created, **kwargs):
    """Automatically create log entry when item is created or updated"""
    if created:
        # Item was created
        ItemLog.objects.create(
            item=instance,
            action='created',
            details=f'Item "{instance.name}" was created in {instance.location.name if instance.location else "no location"}'
        )
    else:
        # Item was updated - check what changed
        if 'update_fields' in kwargs and kwargs['update_fields']:
            # Only log if significant fields changed
            if 'location' in kwargs['update_fields']:
                ItemLog.objects.create(
                    item=instance,
                    action='moved',
                    details=f'Item moved to {instance.location.name if instance.location else "no location"}'
                )
            elif any(field in kwargs['update_fields'] for field in ['name', 'description', 'quantity', 'condition']):
                ItemLog.objects.create(
                    item=instance,
                    action='updated',
                    details='Item details were updated'
                )


@receiver(post_delete, sender=Item)
def log_item_deletion(sender, instance, **kwargs):
    """Log when item is deleted"""
    # Note: We can't create ItemLog here because item is already deleted
    # This is a limitation - consider using soft delete instead
    pass


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

