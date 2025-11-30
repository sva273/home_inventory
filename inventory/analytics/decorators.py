from functools import wraps
from .services import track_event


def track_view(event_type, get_content_object=None):
    """
    Decorator to track view events.
    
    Args:
        event_type: Type of event to track (e.g., 'item_view', 'location_view')
        get_content_object: Function to extract content object from view args/kwargs
    
    Usage:
        @track_view('item_view', lambda request, item_id: Item.objects.get(id=item_id))
        def item_detail(request, item_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Track the event
            content_object = None
            if get_content_object:
                try:
                    content_object = get_content_object(request, *args, **kwargs)
                except Exception:
                    pass  # Silently fail if object not found
            
            track_event(
                user=request.user,
                event_type=event_type,
                content_object=content_object,
                request=request,
            )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

