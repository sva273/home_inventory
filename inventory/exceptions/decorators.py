import logging
from functools import wraps
from django.http import JsonResponse, HttpResponseServerError
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404

logger = logging.getLogger(__name__)


def handle_exceptions(view_func):
    """
    Decorator to handle exceptions in views and return appropriate responses.
    
    Usage:
        @handle_exceptions
        def my_view(request):
            # view code
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Http404 as e:
            logger.warning(f"404 error in {view_func.__name__}: {str(e)}")
            from inventory.exceptions.views import handler404
            return handler404(request, e)
        except PermissionDenied as e:
            logger.warning(f"403 error in {view_func.__name__}: {str(e)}")
            from inventory.exceptions.views import handler403
            return handler403(request, e)
        except ValidationError as e:
            logger.warning(f"400 error in {view_func.__name__}: {str(e)}")
            from inventory.exceptions.views import handler400
            return handler400(request, e)
        except Exception as e:
            logger.error(
                f"Unhandled exception in {view_func.__name__}: {type(e).__name__}: {str(e)}",
                exc_info=True,
                extra={
                    'view': view_func.__name__,
                    'request_path': request.path,
                    'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
                }
            )
            from inventory.exceptions.views import handler500
            return handler500(request)
    
    return wrapper

