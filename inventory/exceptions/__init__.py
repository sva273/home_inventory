"""
Exception handling module for Home Inventory application.

This module contains:
- Custom exception classes (exceptions.py)
- API exception handlers (handlers.py)
- Web error views (views.py)
- Error handling decorators (decorators.py)
"""
from .exceptions import (
    InventoryAPIException,
    ValidationError,
    NotFoundError,
    PermissionDeniedError,
    UnauthorizedError,
)
from .handlers import custom_exception_handler
from .views import handler404, handler500, handler403, handler400
from .decorators import handle_exceptions

__all__ = [
    'InventoryAPIException',
    'ValidationError',
    'NotFoundError',
    'PermissionDeniedError',
    'UnauthorizedError',
    'custom_exception_handler',
    'handler404',
    'handler500',
    'handler403',
    'handler400',
    'handle_exceptions',
]
