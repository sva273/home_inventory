from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    LocationViewSet, ItemViewSet, ItemLogViewSet,
    CategoryViewSet, TagViewSet,
    LocationShareViewSet, ItemShareViewSet, NotificationViewSet, AnalyticsViewSet
)
from .api_auth_views import obtain_token, revoke_token, refresh_token_view, token_info

router = DefaultRouter()
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'items', ItemViewSet, basename='item')
router.register(r'logs', ItemLogViewSet, basename='log')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'location-shares', LocationShareViewSet, basename='location-share')
router.register(r'item-shares', ItemShareViewSet, basename='item-share')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')

urlpatterns = [
    # Authentication endpoints
    path('auth/token/', obtain_token, name='api_token_obtain'),
    path('auth/revoke/', revoke_token, name='api_token_revoke'),
    path('auth/refresh/', refresh_token_view, name='api_token_refresh'),
    path('auth/info/', token_info, name='api_token_info'),
    # API endpoints
    path('', include(router.urls)),
]

