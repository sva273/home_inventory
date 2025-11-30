from rest_framework.exceptions import APIException
from rest_framework import status


class InventoryAPIException(APIException):
    """Base exception for API errors"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'A server error occurred.'
    default_code = 'server_error'

    def __init__(self, detail=None, code=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail, code)


class ValidationError(InventoryAPIException):
    """Validation error exception"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Validation error occurred.'
    default_code = 'validation_error'


class NotFoundError(InventoryAPIException):
    """Resource not found exception"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found.'
    default_code = 'not_found'


class PermissionDeniedError(InventoryAPIException):
    """Permission denied exception"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'permission_denied'


class UnauthorizedError(InventoryAPIException):
    """Unauthorized exception"""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Authentication required.'
    default_code = 'unauthorized'

