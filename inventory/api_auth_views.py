from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from .authentication import create_token, delete_user_token, refresh_token, get_user_token

User = get_user_model()


class TokenObtainSerializer(serializers.Serializer):
    """Serializer for token obtain request."""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


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
    })

