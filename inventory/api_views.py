from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Prefetch, Count
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from .models import Location, Item, ItemLog, Category, Tag, LocationShare, ItemShare, Notification, AnalyticsEvent
from .utils import get_cached_or_set, get_cache_key, CACHE_TIMEOUT_MEDIUM
from .serializers import (
    LocationSerializer, LocationDetailSerializer,
    ItemSerializer, ItemDetailSerializer,
    ItemLogSerializer, CategorySerializer, TagSerializer,
    LocationShareSerializer, ItemShareSerializer, NotificationSerializer
)
from .permissions import IsOwnerOrShared, can_view_location, can_edit_location, can_view_item, can_edit_item

User = get_user_model()


class LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Location instances.
    
    list:
    Return a list of all locations accessible to the user.
    
    retrieve:
    Return a specific location with items and children.
    
    create:
    Create a new location (user becomes owner).
    
    update:
    Update a location (requires owner or editor role).
    
    destroy:
    Delete a location (requires owner role).
    """
    queryset = Location.objects.all().select_related('parent', 'owner')
    permission_classes = [IsAuthenticated, IsOwnerOrShared]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['room_type', 'is_box', 'parent', 'owner']
    search_fields = ['name']
    ordering_fields = ['name', 'room_type', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter locations to only show those accessible to the user (optimized)"""
        from .utils import optimize_location_queryset
        
        user = self.request.user
        
        # Prefetch user's shares for this user to avoid N+1 queries in serializer
        user_shares_prefetch = Prefetch(
            'shares',
            queryset=LocationShare.objects.filter(user=user).select_related('user', 'created_by'),
            to_attr='user_shares'
        )
        
        if user.is_superuser:
            queryset = Location.objects.all().select_related('parent', 'owner').prefetch_related(
                user_shares_prefetch,
                'items',
                'children'
            ).annotate(
                items_count=Count('items', distinct=True),
                children_count=Count('children', distinct=True)
            )
            return optimize_location_queryset(queryset)
        
        # Get locations where user is owner or has shared access
        owned = Location.objects.filter(owner=user)
        shared = Location.objects.filter(shares__user=user)
        queryset = (owned | shared).distinct().select_related('parent', 'owner').prefetch_related(
            user_shares_prefetch,
            'items',
            'children'
        ).annotate(
            items_count=Count('items', distinct=True),
            children_count=Count('children', distinct=True)
        )
        return optimize_location_queryset(queryset)
    
    def get_serializer_context(self):
        """Add request and cached shares to serializer context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        
        # Pre-cache user's location shares to avoid N+1 queries
        user = self.request.user
        if user.is_authenticated:
            # Get all location shares for this user in one query
            location_shares = LocationShare.objects.filter(user=user).select_related('user', 'created_by')
            # Create a dict: location_id -> role
            user_location_shares = {share.location_id: share.role for share in location_shares}
            context['user_location_shares'] = user_location_shares
        
        return context
    
    def perform_create(self, serializer):
        """Set owner when creating location"""
        serializer.save(owner=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LocationDetailSerializer
        return LocationSerializer
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get all items in a location (cached)"""
        location = self.get_object()
        if not can_view_location(request.user, location):
            return Response({'detail': 'You do not have permission to view this location.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Cache key includes location ID and user ID
        cache_key = get_cache_key('location:items', location.id, request.user.id)
        
        def get_items_data():
            # Use optimized queryset with prefetch
            items = location.items.select_related(
                'category', 'owner', 'location__parent', 'location__owner'
            ).prefetch_related(
                Prefetch('shares', queryset=ItemShare.objects.filter(user=request.user)),
                Prefetch('location__shares', queryset=LocationShare.objects.filter(user=request.user)),
                'tags'
            ).all()
            # Use same context as main ViewSet
            context = self.get_serializer_context()
            serializer = ItemSerializer(items, many=True, context=context)
            return serializer.data
        
        items_data = get_cached_or_set(cache_key, get_items_data, CACHE_TIMEOUT_MEDIUM)
        return Response(items_data)
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get all child locations (cached)"""
        location = self.get_object()
        if not can_view_location(request.user, location):
            return Response({'detail': 'You do not have permission to view this location.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Cache key includes location ID and user ID
        cache_key = get_cache_key('location:children', location.id, request.user.id)
        
        def get_children_data():
            # Use optimized queryset with prefetch and annotate
            children = location.children.select_related(
                'parent', 'owner'
            ).prefetch_related(
                Prefetch('shares', queryset=LocationShare.objects.filter(user=request.user)),
                'items',
                'children'
            ).annotate(
                items_count=Count('items', distinct=True),
                children_count=Count('children', distinct=True)
            ).all()
            # Use same context as main ViewSet
            context = self.get_serializer_context()
            serializer = LocationSerializer(children, many=True, context=context)
            return serializer.data
        
        children_data = get_cached_or_set(cache_key, get_children_data, CACHE_TIMEOUT_MEDIUM)
        return Response(children_data)
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share location with another user"""
        location = self.get_object()
        if not can_edit_location(request.user, location):
            return Response({'detail': 'You do not have permission to share this location.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        user_id = request.data.get('user')
        role = request.data.get('role', 'viewer')
        
        if not user_id:
            return Response({'detail': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        if user == request.user:
            return Response({'detail': 'Cannot share with yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        
        share, created = LocationShare.objects.get_or_create(
            location=location,
            user=user,
            defaults={'role': role, 'created_by': request.user}
        )
        
        if not created:
            share.role = role
            share.save()
        
        serializer = LocationShareSerializer(share)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'])
    def unshare(self, request, pk=None):
        """Remove share from location"""
        location = self.get_object()
        if not can_edit_location(request.user, location):
            return Response({'detail': 'You do not have permission to unshare this location.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        user_id = request.data.get('user')
        if not user_id:
            return Response({'detail': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            share = LocationShare.objects.get(location=location, user_id=user_id)
            share.delete()
            return Response({'detail': 'Share removed successfully.'}, status=status.HTTP_204_NO_CONTENT)
        except LocationShare.DoesNotExist:
            return Response({'detail': 'Share not found.'}, status=status.HTTP_404_NOT_FOUND)


class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Item instances.
    
    list:
    Return a list of all items accessible to the user.
    
    retrieve:
    Return a specific item with logs.
    
    create:
    Create a new item (user becomes owner).
    
    update:
    Update an item (requires owner or editor role).
    
    destroy:
    Delete an item (requires owner role).
    """
    queryset = Item.objects.all().select_related('location', 'category', 'owner')
    permission_classes = [IsAuthenticated, IsOwnerOrShared]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location', 'condition', 'category', 'tags', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at', 'quantity']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter items to only show those accessible to the user (optimized)"""
        from .utils import optimize_item_queryset
        
        user = self.request.user
        
        # Prefetch user's shares for items and locations to avoid N+1 queries
        user_item_shares_prefetch = Prefetch(
            'shares',
            queryset=ItemShare.objects.filter(user=user).select_related('user', 'created_by'),
            to_attr='user_shares'
        )
        
        # Prefetch location with user's location shares
        user_location_shares_prefetch = Prefetch(
            'location__shares',
            queryset=LocationShare.objects.filter(user=user).select_related('user', 'created_by'),
            to_attr='user_location_shares'
        )
        
        if user.is_superuser:
            queryset = Item.objects.all().select_related(
                'location__parent',
                'location__owner',
                'category',
                'owner'
            ).prefetch_related(
                user_item_shares_prefetch,
                user_location_shares_prefetch,
                'tags',
                'logs__user'
            )
            return optimize_item_queryset(queryset)
        
        # Get items where user is owner or has shared access
        owned = Item.objects.filter(owner=user)
        shared_items = Item.objects.filter(shares__user=user)
        # Items in shared locations
        shared_locations = Location.objects.filter(shares__user=user)
        shared_via_location = Item.objects.filter(location__in=shared_locations)
        
        queryset = (owned | shared_items | shared_via_location).distinct().select_related(
            'location__parent',
            'location__owner',
            'category',
            'owner'
        ).prefetch_related(
            user_item_shares_prefetch,
            user_location_shares_prefetch,
            'tags',
            'logs__user'
        )
        return optimize_item_queryset(queryset)
    
    def get_serializer_context(self):
        """Add request and cached shares to serializer context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        
        # Pre-cache user's item and location shares to avoid N+1 queries
        user = self.request.user
        if user.is_authenticated:
            # Get all item shares for this user in one query
            item_shares = ItemShare.objects.filter(user=user).select_related('user', 'created_by')
            user_item_shares = {share.item_id: share.role for share in item_shares}
            context['user_item_shares'] = user_item_shares
            
            # Get all location shares for this user in one query
            location_shares = LocationShare.objects.filter(user=user).select_related('user', 'created_by')
            user_location_shares = {share.location_id: share.role for share in location_shares}
            context['user_location_shares'] = user_location_shares
        
        return context
    
    def perform_create(self, serializer):
        """Set owner when creating item"""
        item = serializer.save(owner=self.request.user)
        # Store user for signal
        item._current_user = self.request.user
    
    def perform_update(self, serializer):
        """Store user for signal"""
        item = serializer.save()
        item._current_user = self.request.user
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ItemDetailSerializer
        return ItemSerializer
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get all logs for an item (cached)"""
        item = self.get_object()
        if not can_view_item(request.user, item):
            return Response({'detail': 'You do not have permission to view this item.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Cache key includes item ID
        cache_key = get_cache_key('item:logs', item.id)
        
        def get_logs_data():
            logs = item.logs.select_related('user').all().order_by('-timestamp')[:50]
            serializer = ItemLogSerializer(logs, many=True)
            return serializer.data
        
        logs_data = get_cached_or_set(cache_key, get_logs_data, CACHE_TIMEOUT_MEDIUM)
        return Response(logs_data)
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share item with another user"""
        item = self.get_object()
        if not can_edit_item(request.user, item):
            return Response({'detail': 'You do not have permission to share this item.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        user_id = request.data.get('user')
        role = request.data.get('role', 'viewer')
        
        if not user_id:
            return Response({'detail': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        if user == request.user:
            return Response({'detail': 'Cannot share with yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        
        share, created = ItemShare.objects.get_or_create(
            item=item,
            user=user,
            defaults={'role': role, 'created_by': request.user}
        )
        
        if not created:
            share.role = role
            share.save()
        
        serializer = ItemShareSerializer(share)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'])
    def unshare(self, request, pk=None):
        """Remove share from item"""
        item = self.get_object()
        if not can_edit_item(request.user, item):
            return Response({'detail': 'You do not have permission to unshare this item.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        user_id = request.data.get('user')
        if not user_id:
            return Response({'detail': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            share = ItemShare.objects.get(item=item, user_id=user_id)
            share.delete()
            return Response({'detail': 'Share removed successfully.'}, status=status.HTTP_204_NO_CONTENT)
        except ItemShare.DoesNotExist:
            return Response({'detail': 'Share not found.'}, status=status.HTTP_404_NOT_FOUND)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Category instances.
    
    list:
    Return a list of all categories.
    
    retrieve:
    Return a specific category with items count.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = []
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Optimize queryset with annotate for items_count"""
        return Category.objects.annotate(
            items_count=Count('items', distinct=True)
        ).prefetch_related('items__location', 'items__owner', 'items__tags')
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get all items in a category"""
        category = self.get_object()
        items = category.items.all()
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Tag instances.
    
    list:
    Return a list of all tags.
    
    retrieve:
    Return a specific tag with items count.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = []
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Optimize queryset with annotate for items_count"""
        return Tag.objects.annotate(
            items_count=Count('items', distinct=True)
        ).prefetch_related('items__location', 'items__category', 'items__owner')
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get all items with this tag"""
        tag = self.get_object()
        items = tag.items.all()
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)


class LocationShareViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing LocationShare instances.
    """
    queryset = LocationShare.objects.all().select_related('location', 'user', 'created_by')
    serializer_class = LocationShareSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['location', 'user', 'role']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter shares to only show those the user can manage"""
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        
        # Show shares where user is owner of location or created the share
        owned_locations = Location.objects.filter(owner=user)
        return LocationShare.objects.filter(
            models.Q(location__in=owned_locations) | 
            models.Q(created_by=user) |
            models.Q(user=user)
        ).distinct()


class ItemShareViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing ItemShare instances.
    """
    queryset = ItemShare.objects.all().select_related('item', 'user', 'created_by')
    serializer_class = ItemShareSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['item', 'user', 'role']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter shares to only show those the user can manage"""
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        
        # Show shares where user is owner of item or created the share
        owned_items = Item.objects.filter(owner=user)
        return ItemShare.objects.filter(
            models.Q(item__in=owned_items) | 
            models.Q(created_by=user) |
            models.Q(user=user)
        ).distinct()


class ItemLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing ItemLog instances (read-only).
    
    list:
    Return a list of all item logs for accessible items.
    
    retrieve:
    Return a specific item log.
    """
    queryset = ItemLog.objects.all().select_related('item', 'user')
    serializer_class = ItemLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['item', 'action', 'user']
    search_fields = ['item__name', 'action', 'details']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter logs to only show those for accessible items (optimized - using bulk function)"""
        from .utils import optimize_itemlog_queryset
        from .permissions import get_accessible_item_ids
        
        user = self.request.user
        if user.is_superuser:
            return optimize_itemlog_queryset(self.queryset)
        
        # Use bulk function to get accessible item IDs (no N+1 queries)
        accessible_item_ids = get_accessible_item_ids(user)
        
        queryset = ItemLog.objects.filter(item_id__in=accessible_item_ids)
        return optimize_itemlog_queryset(queryset)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and managing user notifications.
    
    list:
    Return a list of all notifications for the current user.
    
    retrieve:
    Return a specific notification.
    
    mark_read:
    Mark a notification as read.
    
    mark_all_read:
    Mark all notifications as read.
    
    unread_count:
    Get count of unread notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'read']
    ordering_fields = ['created_at', 'read']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter notifications to only show those for the current user"""
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response({'message': 'Notification marked as read'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        count = Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({'message': f'{count} notifications marked as read'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(user=request.user, read=False).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)


class AnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for analytics data.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get overall usage statistics"""
        from .analytics.services import get_usage_statistics
        days = int(request.query_params.get('days', 30))
        stats = get_usage_statistics(user=request.user, days=days)
        return Response(stats, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def popular_items(self, request):
        """Get most viewed items"""
        from .analytics.services import get_popular_items
        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 10))
        items = get_popular_items(user=request.user, days=days, limit=limit)
        from .serializers import ItemSerializer
        serializer = ItemSerializer(items, many=True, context={'request': request})
        # Add view_count to response
        data = serializer.data
        for i, item in enumerate(items):
            data[i]['view_count'] = getattr(item, 'view_count', 0)
        return Response(data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def popular_locations(self, request):
        """Get most viewed locations"""
        from .analytics.services import get_popular_locations
        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 10))
        locations = get_popular_locations(user=request.user, days=days, limit=limit)
        from .serializers import LocationSerializer
        serializer = LocationSerializer(locations, many=True, context={'request': request})
        # Add view_count to response
        data = serializer.data
        for i, loc in enumerate(locations):
            data[i]['view_count'] = getattr(loc, 'view_count', 0)
        return Response(data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def user_activity(self, request):
        """Get current user's activity statistics"""
        from .analytics.services import get_user_activity
        days = int(request.query_params.get('days', 30))
        activity = get_user_activity(user=request.user, days=days)
        return Response(activity, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='item/(?P<item_id>[^/.]+)')
    def item_analytics(self, request, item_id=None):
        """Get analytics for a specific item"""
        from .analytics.services import get_item_analytics
        item = get_object_or_404(Item.objects.all(), id=item_id)
        if not can_view_item(request.user, item):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        days = int(request.query_params.get('days', 30))
        analytics = get_item_analytics(item, days=days)
        return Response(analytics, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='location/(?P<location_id>[^/.]+)')
    def location_analytics(self, request, location_id=None):
        """Get analytics for a specific location"""
        from .analytics.services import get_location_analytics
        location = get_object_or_404(Location.objects.all(), id=location_id)
        if not can_view_location(request.user, location):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        days = int(request.query_params.get('days', 30))
        analytics = get_location_analytics(location, days=days)
        return Response(analytics, status=status.HTTP_200_OK)

