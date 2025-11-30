from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .models import Location, Item, ItemLog, Category, Tag, Notification
from .choices import ROOM_CHOICES
from .permissions import (
    can_view_location, can_edit_location, can_view_item, can_edit_item,
    get_accessible_location_ids, get_accessible_item_ids,
    filter_accessible_locations, filter_accessible_items
)
from .utils import (
    get_cached_or_set, get_cache_key, CACHE_TIMEOUT_STATS,
    invalidate_location_cache, invalidate_item_cache,
    optimize_location_queryset, optimize_item_queryset,
    optimize_itemlog_queryset, get_optimized_statistics
)
from .exceptions.decorators import handle_exceptions
from .analytics.services import (
    track_event, get_popular_items, get_popular_locations,
    get_usage_statistics, get_user_activity
)

# Create your views here.

def _get_home_statistics(user):
    """Helper function to get home page statistics (cached)"""
    def compute_stats():
        if user.is_superuser:
            locations = optimize_location_queryset(
                Location.objects.filter(parent=None)
            ).order_by('name')
            items_count = Item.objects.count()
            locations_count = Location.objects.count()
            boxes_count = Location.objects.filter(is_box=True).count()
            recent_items = list(
                optimize_item_queryset(Item.objects.all())
                .order_by('-created_at')[:5]
            )
        else:
            # Use bulk functions to get accessible IDs (optimized - no N+1 queries)
            accessible_location_ids = get_accessible_location_ids(user)
            accessible_item_ids = get_accessible_item_ids(user)
            
            # Get main locations (without parent) that are accessible
            locations = optimize_location_queryset(
                Location.objects.filter(
                    id__in=accessible_location_ids,
                    parent=None
                )
            ).order_by('name')
            
            items_count = len(accessible_item_ids)
            
            # Count accessible locations
            locations_count = len(accessible_location_ids)
            
            # Count accessible boxes
            boxes_count = Location.objects.filter(
                id__in=accessible_location_ids,
                is_box=True
            ).count()
            
            # Get recent items
            recent_items = list(
                optimize_item_queryset(Item.objects.filter(id__in=accessible_item_ids))
                .order_by('-created_at')[:5]
            ) if accessible_item_ids else []
        
        # Statistics by room type (optimized - using bulk function)
        room_stats = []
        if user.is_authenticated:
            accessible_location_ids = get_accessible_location_ids(user)
            for room_type, room_name in ROOM_CHOICES:
                count = Location.objects.filter(
                    id__in=accessible_location_ids,
                    room_type=room_type
                ).count()
                if count > 0:
                    room_stats.append({'room_type': room_type, 'count': count})
        
        return {
            'locations': locations,
            'items_count': items_count,
            'locations_count': locations_count,
            'boxes_count': boxes_count,
            'recent_items': recent_items,
            'room_stats': room_stats,
        }
    
    # Cache key includes user ID to ensure user-specific caching
    cache_key = get_cache_key('stats:home', user)
    return get_cached_or_set(cache_key, compute_stats, CACHE_TIMEOUT_STATS)


def home(request):
    """Home page with inventory overview (cached)"""
    stats = _get_home_statistics(request.user)
    context = {
        **stats,
    }
    return render(request, 'inventory/home.html', context)


@login_required
def location_list(request):
    """List all locations with filtering"""
    # Filter accessible locations (optimized - using bulk function)
    if request.user.is_superuser:
        locations = optimize_location_queryset(Location.objects.all())
    else:
        # Use bulk function to get accessible location IDs (no N+1 queries)
        accessible_location_ids = get_accessible_location_ids(request.user)
        locations = optimize_location_queryset(
            Location.objects.filter(id__in=accessible_location_ids)
        )
    
    # Filters
    room_type = request.GET.get('room_type')
    is_box = request.GET.get('is_box')
    search = request.GET.get('search')
    
    if room_type:
        locations = locations.filter(room_type=room_type)
    
    if is_box is not None:
        locations = locations.filter(is_box=is_box == 'true')
    
    if search:
        locations = locations.filter(name__icontains=search)
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    locations = locations.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(locations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'room_choices': ROOM_CHOICES,
        'current_room_type': room_type,
        'current_is_box': is_box,
        'current_search': search,
        'current_sort': sort_by,
    }
    return render(request, 'inventory/location_list.html', context)


@login_required
def location_detail(request, location_id):
    """Location detail information"""
    location = get_object_or_404(
        optimize_location_queryset(Location.objects.all()),
        id=location_id
    )
    
    # Check permissions
    if not can_view_location(request.user, location):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You do not have permission to view this location.")
    
    # Track view event
    track_event(
        user=request.user,
        event_type='location_view',
        content_object=location,
        request=request,
    )
    
    # Get all items in this location (filter accessible, optimized - using bulk function)
    accessible_item_ids = get_accessible_item_ids(request.user)
    items = list(optimize_item_queryset(
        location.items.filter(id__in=accessible_item_ids)
    ))
    
    # Get accessible children (optimized - using bulk function)
    accessible_location_ids = get_accessible_location_ids(request.user)
    children = list(optimize_location_queryset(
        location.children.filter(id__in=accessible_location_ids)
    ))
    
    # Statistics
    items_count = len(items)
    children_count = len(children)
    
    # Get path to root (breadcrumbs)
    breadcrumbs = []
    current = location
    while current:
        breadcrumbs.insert(0, current)
        current = current.parent
    
    # Check if user can edit
    can_edit = can_edit_location(request.user, location)
    
    # Get shares
    shares = location.shares.select_related('user', 'created_by').all() if can_edit else []
    
    context = {
        'location': location,
        'items': items,
        'children': children,
        'items_count': items_count,
        'children_count': children_count,
        'breadcrumbs': breadcrumbs,
        'can_edit': can_edit,
        'shares': shares,
    }
    return render(request, 'inventory/location_detail.html', context)


@login_required
def item_list(request):
    """List all items with filtering"""
    # Filter accessible items (optimized - using bulk function)
    if request.user.is_superuser:
        items = optimize_item_queryset(Item.objects.all())
    else:
        # Use bulk function to get accessible item IDs (no N+1 queries)
        accessible_item_ids = get_accessible_item_ids(request.user)
        items = optimize_item_queryset(Item.objects.filter(id__in=accessible_item_ids))
    
    # Filters
    location_id = request.GET.get('location')
    condition = request.GET.get('condition')
    category_id = request.GET.get('category')
    tag_id = request.GET.get('tag')
    search = request.GET.get('search')
    
    if location_id:
        items = items.filter(location_id=location_id)
    
    if condition:
        items = items.filter(condition=condition)
    
    if category_id:
        items = items.filter(category_id=category_id)
    
    if tag_id:
        items = items.filter(tags__id=tag_id)
    
    if search:
        items = items.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    items = items.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(items, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all locations, categories, and tags for filters (filter accessible, optimized)
    if request.user.is_superuser:
        locations = optimize_location_queryset(Location.objects.all()).order_by('name')
    else:
        # Use bulk function to get accessible location IDs (no N+1 queries)
        accessible_location_ids = get_accessible_location_ids(request.user)
        locations = optimize_location_queryset(
            Location.objects.filter(id__in=accessible_location_ids)
        ).order_by('name')
    categories = Category.objects.all().prefetch_related('items').order_by('name')
    tags = Tag.objects.all().prefetch_related('items').order_by('name')
    
    context = {
        'page_obj': page_obj,
        'locations': locations,
        'categories': categories,
        'tags': tags,
        'current_location': location_id,
        'current_condition': condition,
        'current_category': category_id,
        'current_tag': tag_id,
        'current_search': search,
        'current_sort': sort_by,
    }
    return render(request, 'inventory/item_list.html', context)


@login_required
def item_detail(request, item_id):
    """Item detail information"""
    item = get_object_or_404(
        optimize_item_queryset(Item.objects.all()),
        id=item_id
    )
    
    # Check permissions
    if not can_view_item(request.user, item):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You do not have permission to view this item.")
    
    # Track view event
    track_event(
        user=request.user,
        event_type='item_view',
        content_object=item,
        request=request,
    )
    
    # Get activity logs (optimized)
    logs = optimize_itemlog_queryset(
        ItemLog.objects.filter(item=item)
    ).order_by('-timestamp')[:10]
    
    # Similar items (in the same location, filter accessible, optimized - using bulk function)
    if item.location:
        accessible_item_ids = get_accessible_item_ids(request.user)
        similar_items = list(optimize_item_queryset(
            Item.objects.filter(
                location=item.location,
                id__in=accessible_item_ids
            ).exclude(id=item.id)
        )[:5])
    else:
        similar_items = []
    
    # Check if user can edit
    can_edit = can_edit_item(request.user, item)
    
    # Get shares
    shares = item.shares.select_related('user', 'created_by').all() if can_edit else []
    
    context = {
        'item': item,
        'logs': logs,
        'similar_items': similar_items,
        'can_edit': can_edit,
        'shares': shares,
    }
    return render(request, 'inventory/item_detail.html', context)


def room_view(request, room_type):
    """View items by room type (optimized)"""
    # Validate room type
    valid_room_types = [choice[0] for choice in ROOM_CHOICES]
    if room_type not in valid_room_types:
        from django.http import Http404
        raise Http404("Room type not found")
    
    # Filter accessible locations and items if user is authenticated
    if request.user.is_authenticated and not request.user.is_superuser:
        accessible_location_ids = get_accessible_location_ids(request.user)
        accessible_item_ids = get_accessible_item_ids(request.user)
        
        # Get locations of this type (filter accessible, optimized)
        locations = optimize_location_queryset(
            Location.objects.filter(
                room_type=room_type,
                id__in=accessible_location_ids
            )
        )
        
        # Get all items in these locations (filter accessible, optimized)
        items = optimize_item_queryset(
            Item.objects.filter(
                location__room_type=room_type,
                id__in=accessible_item_ids
            )
        )
    else:
        # Superuser or anonymous - get all
        locations = optimize_location_queryset(
            Location.objects.filter(room_type=room_type)
        )
        items = optimize_item_queryset(
            Item.objects.filter(location__room_type=room_type)
        )
    
    # Statistics
    items_count = items.count()
    locations_count = locations.count()
    
    # Get room name for display (translated)
    # Create a temporary Location object to use get_room_type_display() for translation
    temp_location = Location(room_type=room_type)
    room_name = temp_location.get_room_type_display() if room_type else room_type
    
    context = {
        'room_type': room_type,
        'room_name': room_name,
        'locations': locations,
        'items': items,
        'items_count': items_count,
        'locations_count': locations_count,
    }
    return render(request, 'inventory/room_view.html', context)


def search(request):
    """Universal search across locations and items"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return render(request, 'inventory/search.html', {'query': ''})
    
    # Track search events
    track_event(
        user=request.user,
        event_type='item_search',
        metadata={'query': query},
        request=request,
    )
    track_event(
        user=request.user,
        event_type='location_search',
        metadata={'query': query},
        request=request,
    )
    
    # Search locations (optimized)
    location_query = Location.objects.filter(
        Q(name__icontains=query) | 
        Q(room_type__icontains=query)
    )
    
    # Filter accessible locations if user is authenticated
    if request.user.is_authenticated and not request.user.is_superuser:
        accessible_location_ids = get_accessible_location_ids(request.user)
        location_query = location_query.filter(id__in=accessible_location_ids)
    
    locations = optimize_location_queryset(location_query)[:10]
    
    # Search items (optimized)
    item_query = Item.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query)
    )
    
    # Filter accessible items if user is authenticated
    if request.user.is_authenticated and not request.user.is_superuser:
        accessible_item_ids = get_accessible_item_ids(request.user)
        item_query = item_query.filter(id__in=accessible_item_ids)
    
    items = optimize_item_queryset(item_query)[:10]
    
    context = {
        'query': query,
        'locations': locations,
        'items': items,
        'locations_count': locations.count(),
        'items_count': items.count(),
    }
    return render(request, 'inventory/search.html', context)


@login_required
@handle_exceptions
def notification_list(request):
    """List all notifications for the current user"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by read status
    read_filter = request.GET.get('read', None)
    if read_filter == 'true':
        notifications = notifications.filter(read=True)
    elif read_filter == 'false':
        notifications = notifications.filter(read=False)
    
    # Filter by type
    notification_type = request.GET.get('type', None)
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unread count
    unread_count = Notification.objects.filter(user=request.user, read=False).count()
    
    context = {
        'notifications': page_obj,
        'unread_count': unread_count,
        'read_filter': read_filter,
        'notification_type': notification_type,
    }
    
    return render(request, 'inventory/notification_list.html', context)


@login_required
@handle_exceptions
def notification_mark_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.read = True
    notification.save()
    
    # Redirect back to notification list or referrer
    next_url = request.GET.get('next', 'notification_list')
    return redirect(next_url)


@login_required
@handle_exceptions
def notification_mark_all_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, read=False).update(read=True)
    
    # Redirect back to notification list
    return redirect('notification_list')


@login_required
@handle_exceptions
def analytics_dashboard(request):
    """Analytics dashboard with usage statistics and popular items/locations"""
    # Get period from query params (default 30 days)
    days = int(request.GET.get('days', 30))
    
    # Get statistics
    stats = get_usage_statistics(user=request.user, days=days)
    user_activity = get_user_activity(user=request.user, days=days)
    
    # Get popular items and locations
    popular_items = get_popular_items(user=request.user, days=days, limit=10)
    popular_locations = get_popular_locations(user=request.user, days=days, limit=10)
    
    context = {
        'stats': stats,
        'user_activity': user_activity,
        'popular_items': popular_items,
        'popular_locations': popular_locations,
        'days': days,
    }
    
    return render(request, 'inventory/analytics_dashboard.html', context)
