from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .authentication import create_token, delete_user_token, refresh_token, get_user_token


# Create your models here.
User = get_user_model()


class TokenObtainSerializer(serializers.Serializer):
    """Serializer for token obtain request."""
    username = serializers.CharField(required=True, help_text="Username for authentication")
    password = serializers.CharField(required=True, write_only=True, help_text="Password for authentication")


@swagger_auto_schema(
    method='post',
    request_body=TokenObtainSerializer,
    responses={
        200: openapi.Response(
            description="Token obtained successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'token': openapi.Schema(type=openapi.TYPE_STRING, description='Authentication token'),
                    'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                    'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                    'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email', nullable=True),
                }
            )
        ),
        400: openapi.Response(description="Invalid request"),
        401: openapi.Response(description="Invalid credentials"),
    },
    operation_summary="Obtain authentication token",
    operation_description="Get an authentication token by providing username and password. Use this token in the Authorization header as 'Token <your_token>' for authenticated requests."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def obtain_token(request):
    """
    Obtain authentication token.
    
    POST /api/auth/token/
    {
        "username": "user",
        "password": "password"
    }
    
    Returns:
    {
        "token": "abc123...",
        "user_id": 1,
        "username": "user"
    }
    """
    serializer = TokenObtainSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request. Username and password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    user = authenticate(username=username, password=password)
    
    if not user:
        return Response(
            {'error': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'error': 'User account is disabled.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Create or get existing token
    token = get_user_token(user)
    if not token:
        token = create_token(user)
    
    return Response({
        'token': token,
        'user_id': user.id,
        'username': user.username,
        'email': user.email if hasattr(user, 'email') else None,
    })


@swagger_auto_schema(
    method='post',
    responses={
        200: openapi.Response(
            description="Token revoked successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                }
            )
        ),
        401: openapi.Response(description="Unauthorized"),
    },
    operation_summary="Revoke authentication token",
    operation_description="Revoke the current authentication token. Requires authentication.",
    security=[{'Token': []}]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_token(request):
    """
    Revoke current authentication token.
    
    POST /api/auth/revoke/
    Requires authentication.
    
    Returns:
    {
        "message": "Token revoked successfully"
    }
    """
    from .authentication import delete_user_token
    delete_user_token(request.user)
    
    return Response({
        'message': 'Token revoked successfully'
    })


@swagger_auto_schema(
    method='post',
    responses={
        200: openapi.Response(
            description="Token refreshed successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                }
            )
        ),
        400: openapi.Response(description="Token not found"),
        401: openapi.Response(description="Invalid or expired token"),
    },
    operation_summary="Refresh authentication token",
    operation_description="Refresh the current authentication token (extend expiration). Requires authentication.",
    security=[{'Token': []}]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_token_view(request):
    """
    Refresh current authentication token (extend expiration).
    
    POST /api/auth/refresh/
    Requires authentication.
    
    Returns:
    {
        "message": "Token refreshed successfully"
    }
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token = auth_header.split(' ')[1] if len(auth_header.split(' ')) > 1 else None
    
    if not token:
        return Response(
            {'error': 'Token not found in request.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if refresh_token(token):
        return Response({
            'message': 'Token refreshed successfully'
        })
    else:
        return Response(
            {'error': 'Invalid or expired token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            description="Token information",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                    'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                    'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email', nullable=True),
                    'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is staff user'),
                    'is_superuser': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is superuser'),
                    'authenticated': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is authenticated'),
                }
            )
        ),
        401: openapi.Response(description="Unauthorized"),
    },
    operation_summary="Get token information",
    operation_description="Get information about the current authentication token and user. Requires authentication.",
    security=[{'Token': []}]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def token_info(request):
    """
    Get information about current token.
    
    GET /api/auth/info/
    Requires authentication.
    
    Returns:
    {
        "user_id": 1,
        "username": "user",
        "email": "user@example.com"
    }
    """
    return Response({
        'user_id': request.user.id,
        'username': request.user.username,
        'email': request.user.email if hasattr(request.user, 'email') else None,
        'is_staff': request.user.is_staff,
        'is_superuser': request.user.is_superuser,
        'authenticated': request.user.is_authenticated,
    })

