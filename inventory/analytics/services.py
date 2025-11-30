from django.db.models import Count, Q, F
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
from ..models import AnalyticsEvent, Item, Location
from ..utils import optimize_item_queryset, optimize_location_queryset


def track_event(user, event_type, content_object=None, metadata=None, request=None):
    """
    Track an analytics event.
    
    Args:
        user: User who performed the action (can be None for anonymous)
        event_type: Type of event (from EVENT_TYPE_CHOICES)
        content_object: Related object (Item, Location, etc.)
        metadata: Additional data (dict)
        request: Django request object (for IP and user agent)
    
    Returns:
        Created AnalyticsEvent instance
    """
    content_type = None
    object_id = None
    
    if content_object:
        content_type = ContentType.objects.get_for_model(content_object)
        object_id = content_object.id
    
    ip_address = None
    user_agent = ''
    if request:
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    return AnalyticsEvent.objects.create(
        user=user if user and user.is_authenticated else None,
        event_type=event_type,
        content_type=content_type,
        object_id=object_id,
        metadata=metadata or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )


def get_popular_items(user=None, days=30, limit=10):
    """
    Get most viewed items.
    
    Args:
        user: Filter by user (optional)
        days: Number of days to look back
        limit: Maximum number of items to return
    
    Returns:
        QuerySet of items ordered by view count
    """
    since = timezone.now() - timedelta(days=days)
    item_content_type = ContentType.objects.get_for_model(Item)
    
    # Get item view events
    view_events = AnalyticsEvent.objects.filter(
        event_type='item_view',
        content_type=item_content_type,
        created_at__gte=since,
    )
    
    if user:
        view_events = view_events.filter(user=user)
    
    # Count views per item
    item_view_counts = view_events.values('object_id').annotate(
        view_count=Count('id')
    ).order_by('-view_count')[:limit]
    
    # Get item IDs
    item_ids = [item['object_id'] for item in item_view_counts]
    
    if not item_ids:
        return []
    
    # Get items with view counts
    items = optimize_item_queryset(Item.objects.filter(id__in=item_ids))
    
    # Create a dict to map item IDs to view counts
    view_count_map = {item['object_id']: item['view_count'] for item in item_view_counts}
    
    # Sort items by view count
    items_list = list(items)
    items_list.sort(key=lambda x: view_count_map.get(x.id, 0), reverse=True)
    
    # Add view_count to each item
    for item in items_list:
        item.view_count = view_count_map.get(item.id, 0)
    
    return items_list


def get_popular_locations(user=None, days=30, limit=10):
    """
    Get most viewed locations.
    
    Args:
        user: Filter by user (optional)
        days: Number of days to look back
        limit: Maximum number of locations to return
    
    Returns:
        QuerySet of locations ordered by view count
    """
    since = timezone.now() - timedelta(days=days)
    location_content_type = ContentType.objects.get_for_model(Location)
    
    # Get location view events
    view_events = AnalyticsEvent.objects.filter(
        event_type='location_view',
        content_type=location_content_type,
        created_at__gte=since,
    )
    
    if user:
        view_events = view_events.filter(user=user)
    
    # Count views per location
    location_view_counts = view_events.values('object_id').annotate(
        view_count=Count('id')
    ).order_by('-view_count')[:limit]
    
    # Get location IDs
    location_ids = [loc['object_id'] for loc in location_view_counts]
    
    if not location_ids:
        return []
    
    # Get locations with view counts
    locations = optimize_location_queryset(Location.objects.filter(id__in=location_ids))
    
    # Create a dict to map location IDs to view counts
    view_count_map = {loc['object_id']: loc['view_count'] for loc in location_view_counts}
    
    # Sort locations by view count
    locations_list = list(locations)
    locations_list.sort(key=lambda x: view_count_map.get(x.id, 0), reverse=True)
    
    # Add view_count to each location
    for loc in locations_list:
        loc.view_count = view_count_map.get(loc.id, 0)
    
    return locations_list


def get_usage_statistics(user=None, days=30):
    """
    Get overall usage statistics.
    
    Args:
        user: Filter by user (optional)
        days: Number of days to look back
    
    Returns:
        Dict with statistics
    """
    since = timezone.now() - timedelta(days=days)
    
    events = AnalyticsEvent.objects.filter(created_at__gte=since)
    if user:
        events = events.filter(user=user)
    
    # Count events by type
    event_counts = events.values('event_type').annotate(
        count=Count('id')
    )
    
    event_type_map = {item['event_type']: item['count'] for item in event_counts}
    
    # Get unique users
    unique_users = events.filter(user__isnull=False).values('user').distinct().count()
    
    # Get unique items viewed
    item_content_type = ContentType.objects.get_for_model(Item)
    unique_items = events.filter(
        event_type='item_view',
        content_type=item_content_type
    ).values('object_id').distinct().count()
    
    # Get unique locations viewed
    location_content_type = ContentType.objects.get_for_model(Location)
    unique_locations = events.filter(
        event_type='location_view',
        content_type=location_content_type
    ).values('object_id').distinct().count()
    
    return {
        'total_events': events.count(),
        'unique_users': unique_users,
        'unique_items_viewed': unique_items,
        'unique_locations_viewed': unique_locations,
        'item_views': event_type_map.get('item_view', 0),
        'location_views': event_type_map.get('location_view', 0),
        'item_searches': event_type_map.get('item_search', 0),
        'location_searches': event_type_map.get('location_search', 0),
        'items_created': event_type_map.get('item_created', 0),
        'items_updated': event_type_map.get('item_updated', 0),
        'items_deleted': event_type_map.get('item_deleted', 0),
        'locations_created': event_type_map.get('location_created', 0),
        'locations_updated': event_type_map.get('location_updated', 0),
        'locations_deleted': event_type_map.get('location_deleted', 0),
        'period_days': days,
    }


def get_user_activity(user, days=30):
    """
    Get activity statistics for a specific user.
    
    Args:
        user: User to get activity for
        days: Number of days to look back
    
    Returns:
        Dict with user activity statistics
    """
    since = timezone.now() - timedelta(days=days)
    
    events = AnalyticsEvent.objects.filter(user=user, created_at__gte=since)
    
    # Count events by type
    event_counts = events.values('event_type').annotate(
        count=Count('id')
    )
    
    event_type_map = {item['event_type']: item['count'] for item in event_counts}
    
    return {
        'total_events': events.count(),
        'item_views': event_type_map.get('item_view', 0),
        'location_views': event_type_map.get('location_view', 0),
        'item_searches': event_type_map.get('item_search', 0),
        'location_searches': event_type_map.get('location_search', 0),
        'items_created': event_type_map.get('item_created', 0),
        'items_updated': event_type_map.get('item_updated', 0),
        'items_deleted': event_type_map.get('item_deleted', 0),
        'locations_created': event_type_map.get('location_created', 0),
        'locations_updated': event_type_map.get('location_updated', 0),
        'locations_deleted': event_type_map.get('location_deleted', 0),
        'period_days': days,
    }


def get_item_analytics(item, days=30):
    """
    Get analytics for a specific item.
    
    Args:
        item: Item instance
        days: Number of days to look back
    
    Returns:
        Dict with item analytics
    """
    since = timezone.now() - timedelta(days=days)
    item_content_type = ContentType.objects.get_for_model(Item)
    
    events = AnalyticsEvent.objects.filter(
        content_type=item_content_type,
        object_id=item.id,
        created_at__gte=since,
    )
    
    view_count = events.filter(event_type='item_view').count()
    unique_viewers = events.filter(
        event_type='item_view',
        user__isnull=False
    ).values('user').distinct().count()
    
    return {
        'item_id': str(item.id),
        'item_name': item.name,
        'total_views': view_count,
        'unique_viewers': unique_viewers,
        'period_days': days,
    }


def get_location_analytics(location, days=30):
    """
    Get analytics for a specific location.
    
    Args:
        location: Location instance
        days: Number of days to look back
    
    Returns:
        Dict with location analytics
    """
    since = timezone.now() - timedelta(days=days)
    location_content_type = ContentType.objects.get_for_model(Location)
    
    events = AnalyticsEvent.objects.filter(
        content_type=location_content_type,
        object_id=location.id,
        created_at__gte=since,
    )
    
    view_count = events.filter(event_type='location_view').count()
    unique_viewers = events.filter(
        event_type='location_view',
        user__isnull=False
    ).values('user').distinct().count()
    
    return {
        'location_id': str(location.id),
        'location_name': location.name,
        'total_views': view_count,
        'unique_viewers': unique_viewers,
        'period_days': days,
    }

