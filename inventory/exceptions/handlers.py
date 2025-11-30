import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from .exceptions import InventoryAPIException

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    
    Args:
        exc: The exception that was raised
        context: Dictionary containing any additional context
    
    Returns:
        Response object with error details
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Get the view and request from context
    view = context.get('view')
    request = context.get('request')
    
    # Log the exception
    logger.error(
        f"Exception in {view.__class__.__name__ if view else 'unknown view'}: {type(exc).__name__}",
        exc_info=True,
        extra={
            'view': view.__class__.__name__ if view else None,
            'request_path': request.path if request else None,
            'user': request.user.username if request and hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
        }
    )
    
    # Handle custom exceptions
    if isinstance(exc, InventoryAPIException):
        custom_response_data = {
            'error': {
                'code': exc.default_code,
                'message': str(exc.detail) if hasattr(exc, 'detail') else exc.default_detail,
                'type': type(exc).__name__,
            }
        }
        
        # Add field errors if available
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            custom_response_data['error']['fields'] = exc.detail
        
        return Response(custom_response_data, status=exc.status_code)
    
    # Handle Django's Http404
    if isinstance(exc, Http404):
        return Response({
            'error': {
                'code': 'not_found',
                'message': 'Resource not found.',
                'type': 'Http404',
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Handle Django's PermissionDenied
    if isinstance(exc, PermissionDenied):
        return Response({
            'error': {
                'code': 'permission_denied',
                'message': 'You do not have permission to perform this action.',
                'type': 'PermissionDenied',
            }
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Handle Django's ValidationError
    if isinstance(exc, DjangoValidationError):
        return Response({
            'error': {
                'code': 'validation_error',
                'message': 'Validation error occurred.',
                'type': 'ValidationError',
                'fields': exc.message_dict if hasattr(exc, 'message_dict') else str(exc),
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # If response is None, it's an unhandled exception
    if response is None:
        # Log unhandled exceptions
        logger.critical(
            f"Unhandled exception: {type(exc).__name__}",
            exc_info=True,
            extra={
                'view': view.__class__.__name__ if view else None,
                'request_path': request.path if request else None,
                'user': request.user.username if request and hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
            }
        )
        
        # Return a generic error response
        return Response({
            'error': {
                'code': 'internal_server_error',
                'message': 'An internal server error occurred. Please try again later.',
                'type': type(exc).__name__,
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Customize the response data for standard DRF exceptions
    custom_response_data = {
        'error': {
            'code': getattr(exc, 'default_code', 'error'),
            'message': response.data.get('detail', 'An error occurred.') if isinstance(response.data, dict) else str(response.data),
            'type': type(exc).__name__,
        }
    }
    
    # Add field errors if available
    if isinstance(response.data, dict):
        if 'detail' not in response.data:
            # If there are field errors, include them
            field_errors = {k: v for k, v in response.data.items() if k != 'detail'}
            if field_errors:
                custom_response_data['error']['fields'] = field_errors
    
    response.data = custom_response_data
    return response

