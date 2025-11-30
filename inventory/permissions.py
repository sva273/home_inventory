from rest_framework import permissions
from django.contrib.auth import get_user_model
from .models import Location, Item, LocationShare, ItemShare

User = get_user_model()


class IsOwnerOrShared(permissions.BasePermission):
    """
    Permission class that allows access if user is owner or has shared access.
    """
    
    def has_object_permission(self, request, view, obj):
        # Superusers can do anything
        if request.user.is_superuser:
            return True
        
        # Check if user is owner
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True
        
        # For Location: check shares
        if isinstance(obj, Location):
            share = LocationShare.objects.filter(
                location=obj,
                user=request.user
            ).first()
            if share:
                # Check role permissions
                if request.method in permissions.SAFE_METHODS:
                    return True  # Viewer can read
                elif share.role in ['owner', 'editor']:
                    return True  # Editor and owner can write
            return False
        
        # For Item: check item shares and location shares
        if isinstance(obj, Item):
            # Check direct item share
            item_share = ItemShare.objects.filter(
                item=obj,
                user=request.user
            ).first()
            if item_share:
                if request.method in permissions.SAFE_METHODS:
                    return True
                elif item_share.role in ['owner', 'editor']:
                    return True
            
            # Check location share (if item has location)
            if obj.location:
                location_share = LocationShare.objects.filter(
                    location=obj.location,
                    user=request.user
                ).first()
                if location_share:
                    if request.method in permissions.SAFE_METHODS:
                        return True
                    elif location_share.role in ['owner', 'editor']:
                        return True
            
            return False
        
        return False


def can_view_location(user, location):
    """Check if user can view location"""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if location.owner == user:
        return True
    return LocationShare.objects.filter(location=location, user=user).exists()


def can_edit_location(user, location):
    """Check if user can edit location"""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if location.owner == user:
        return True
    share = LocationShare.objects.filter(location=location, user=user).first()
    return share and share.role in ['owner', 'editor']


def can_view_item(user, item):
    """Check if user can view item"""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if item.owner == user:
        return True
    if ItemShare.objects.filter(item=item, user=user).exists():
        return True
    if item.location and can_view_location(user, item.location):
        return True
    return False


def can_edit_item(user, item):
    """Check if user can edit item"""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if item.owner == user:
        return True
    share = ItemShare.objects.filter(item=item, user=user).first()
    if share and share.role in ['owner', 'editor']:
        return True
    if item.location and can_edit_location(user, item.location):
        return True
    return False


# Bulk permission functions for optimization
def get_accessible_location_ids(user):
    """
    Get all location IDs accessible to user (optimized bulk function).
    This function loads all shares in one query instead of checking each location separately.
    
    Args:
        user: User object
    
    Returns:
        set: Set of accessible location IDs
    """
    if not user.is_authenticated:
        return set()
    if user.is_superuser:
        from .models import Location
        return set(Location.objects.values_list('id', flat=True))
    
    # Get all owned locations
    owned_ids = set(Location.objects.filter(owner=user).values_list('id', flat=True))
    
    # Get all shared locations
    shared_ids = set(LocationShare.objects.filter(user=user).values_list('location_id', flat=True))
    
    return owned_ids | shared_ids


def get_accessible_item_ids(user):
    """
    Get all item IDs accessible to user (optimized bulk function).
    This function loads all shares in one query instead of checking each item separately.
    
    Args:
        user: User object
    
    Returns:
        set: Set of accessible item IDs
    """
    if not user.is_authenticated:
        return set()
    if user.is_superuser:
        from .models import Item
        return set(Item.objects.values_list('id', flat=True))
    
    # Get all owned items
    owned_ids = set(Item.objects.filter(owner=user).values_list('id', flat=True))
    
    # Get all directly shared items
    shared_item_ids = set(ItemShare.objects.filter(user=user).values_list('item_id', flat=True))
    
    # Get items in shared locations
    accessible_location_ids = get_accessible_location_ids(user)
    shared_via_location_ids = set(
        Item.objects.filter(location_id__in=accessible_location_ids).values_list('id', flat=True)
    )
    
    return owned_ids | shared_item_ids | shared_via_location_ids


def filter_accessible_locations(queryset, user):
    """
    Filter queryset to only include accessible locations.
    
    Args:
        queryset: Location queryset
        user: User object
    
    Returns:
        Filtered queryset
    """
    accessible_ids = get_accessible_location_ids(user)
    return queryset.filter(id__in=accessible_ids)


def filter_accessible_items(queryset, user):
    """
    Filter queryset to only include accessible items.
    
    Args:
        queryset: Item queryset
        user: User object
    
    Returns:
        Filtered queryset
    """
    accessible_ids = get_accessible_item_ids(user)
    return queryset.filter(id__in=accessible_ids)

