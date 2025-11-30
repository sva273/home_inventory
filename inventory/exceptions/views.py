from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponseServerError, HttpResponseForbidden, HttpResponseBadRequest
import logging

logger = logging.getLogger(__name__)


def handler404(request, exception):
    """Custom 404 error handler"""
    logger.warning(
        f"404 error: {request.path}",
        extra={
            'request_path': request.path,
            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
        }
    )
    return render(request, 'errors/404.html', {
        'error_message': 'The page you are looking for could not be found.',
        'request_path': request.path,
    }, status=404)


def handler500(request):
    """Custom 500 error handler"""
    logger.error(
        f"500 error: {request.path}",
        exc_info=True,
        extra={
            'request_path': request.path,
            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
        }
    )
    return render(request, 'errors/500.html', {
        'error_message': 'An internal server error occurred. Please try again later.',
    }, status=500)


def handler403(request, exception):
    """Custom 403 error handler"""
    logger.warning(
        f"403 error: {request.path}",
        extra={
            'request_path': request.path,
            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
        }
    )
    return render(request, 'errors/403.html', {
        'error_message': 'You do not have permission to access this resource.',
    }, status=403)


def handler400(request, exception):
    """Custom 400 error handler"""
    logger.warning(
        f"400 error: {request.path}",
        extra={
            'request_path': request.path,
            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
        }
    )
    return render(request, 'errors/400.html', {
        'error_message': 'Bad request. Please check your input and try again.',
    }, status=400)

