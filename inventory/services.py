from django.db.models import Q, Count
from .models import Location, Item, ItemLog


class LocationService:
    """Service for location-related operations"""
    
    @staticmethod
    def get_main_locations():
        """Get all main locations (without parent)"""
        return Location.objects.filter(parent=None).order_by('name')
    
    @staticmethod
    def get_locations_with_filters(room_type=None, is_box=None, search=None, sort='name'):
        """Get filtered locations"""
        locations = Location.objects.all().select_related('parent').prefetch_related('items')
        
        if room_type:
            locations = locations.filter(room_type=room_type)
        
        if is_box is not None:
            locations = locations.filter(is_box=is_box == 'true')
        
        if search:
            locations = locations.filter(name__icontains=search)
        
        return locations.order_by(sort)
    
    @staticmethod
    def get_location_statistics():
        """Get location statistics"""
        return {
            'total': Location.objects.count(),
            'boxes': Location.objects.filter(is_box=True).count(),
            'rooms': Location.objects.filter(is_box=False).count(),
        }


class ItemService:
    """Service for item-related operations"""
    
    @staticmethod
    def get_items_with_filters(location_id=None, condition=None, search=None, sort='-created_at'):
        """Get filtered items"""
        items = Item.objects.all().select_related('location')
        
        if location_id:
            items = items.filter(location_id=location_id)
        
        if condition:
            items = items.filter(condition=condition)
        
        if search:
            items = items.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        return items.order_by(sort)
    
    @staticmethod
    def get_item_statistics():
        """Get item statistics"""
        return {
            'total': Item.objects.count(),
            'by_condition': dict(
                Item.objects.values('condition')
                .annotate(count=Count('id'))
                .values_list('condition', 'count')
            ),
        }


class SearchService:
    """Service for search operations"""
    
    @staticmethod
    def search_all(query):
        """Search across locations and items"""
        locations = Location.objects.filter(
            Q(name__icontains=query) | Q(room_type__icontains=query)
        ).select_related('parent')[:10]
        
        items = Item.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).select_related('location')[:10]
        
        return {
            'locations': locations,
            'items': items,
        }

