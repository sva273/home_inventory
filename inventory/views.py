from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Location, Item, ItemLog
from .choices import ROOM_CHOICES

# Create your views here.

def home(request):
    """Home page with inventory overview"""
    locations = Location.objects.filter(parent=None).order_by('name')
    items_count = Item.objects.count()
    locations_count = Location.objects.count()
    boxes_count = Location.objects.filter(is_box=True).count()
    
    # Recently added items
    recent_items = Item.objects.select_related('location').order_by('-created_at')[:5]
    
    # Statistics by room type
    room_stats = Location.objects.filter(
        room_type__isnull=False
    ).values('room_type').annotate(
        count=Count('id')
    ).order_by('room_type')
    
    context = {
        'locations': locations,
        'items_count': items_count,
        'locations_count': locations_count,
        'boxes_count': boxes_count,
        'recent_items': recent_items,
        'room_stats': room_stats,
    }
    return render(request, 'inventory/home.html', context)


def location_list(request):
    """List all locations with filtering"""
    locations = Location.objects.all().select_related('parent').prefetch_related('items')
    
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


def location_detail(request, location_id):
    """Location detail information"""
    location = get_object_or_404(
        Location.objects.select_related('parent').prefetch_related('children', 'items'),
        id=location_id
    )
    
    # Get all items in this location and children
    items = location.items.all()
    children = location.children.all()
    
    # Statistics
    items_count = items.count()
    children_count = children.count()
    
    # Get path to root (breadcrumbs)
    breadcrumbs = []
    current = location
    while current:
        breadcrumbs.insert(0, current)
        current = current.parent
    
    context = {
        'location': location,
        'items': items,
        'children': children,
        'items_count': items_count,
        'children_count': children_count,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'inventory/location_detail.html', context)


def item_list(request):
    """List all items with filtering"""
    items = Item.objects.select_related('location').all()
    
    # Filters
    location_id = request.GET.get('location')
    condition = request.GET.get('condition')
    search = request.GET.get('search')
    
    if location_id:
        items = items.filter(location_id=location_id)
    
    if condition:
        items = items.filter(condition=condition)
    
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
    
    # Get all locations for filter
    locations = Location.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'locations': locations,
        'current_location': location_id,
        'current_condition': condition,
        'current_search': search,
        'current_sort': sort_by,
    }
    return render(request, 'inventory/item_list.html', context)


def item_detail(request, item_id):
    """Item detail information"""
    item = get_object_or_404(
        Item.objects.select_related('location'),
        id=item_id
    )
    
    # Get activity logs
    logs = ItemLog.objects.filter(item=item).order_by('-timestamp')[:10]
    
    # Similar items (in the same location)
    similar_items = Item.objects.filter(
        location=item.location
    ).exclude(id=item.id)[:5]
    
    context = {
        'item': item,
        'logs': logs,
        'similar_items': similar_items,
    }
    return render(request, 'inventory/item_detail.html', context)


def room_view(request, room_type):
    """View items by room type"""
    # Validate room type
    valid_room_types = [choice[0] for choice in ROOM_CHOICES]
    if room_type not in valid_room_types:
        from django.http import Http404
        raise Http404("Room type not found")
    
    # Get locations of this type
    locations = Location.objects.filter(room_type=room_type).select_related('parent')
    
    # Get all items in these locations
    items = Item.objects.filter(location__room_type=room_type).select_related('location')
    
    # Statistics
    items_count = items.count()
    locations_count = locations.count()
    
    # Get room name for display
    room_name = dict(ROOM_CHOICES).get(room_type, room_type)
    
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
    
    # Search locations
    locations = Location.objects.filter(
        Q(name__icontains=query) | 
        Q(room_type__icontains=query)
    ).select_related('parent')[:10]
    
    # Search items
    items = Item.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query)
    ).select_related('location')[:10]
    
    context = {
        'query': query,
        'locations': locations,
        'items': items,
        'locations_count': locations.count(),
        'items_count': items.count(),
    }
    return render(request, 'inventory/search.html', context)
