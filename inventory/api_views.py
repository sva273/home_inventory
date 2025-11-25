from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Location, Item, ItemLog
from .serializers import (
    LocationSerializer, LocationDetailSerializer,
    ItemSerializer, ItemDetailSerializer,
    ItemLogSerializer
)


class LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Location instances.
    
    list:
    Return a list of all locations.
    
    retrieve:
    Return a specific location with items and children.
    
    create:
    Create a new location.
    
    update:
    Update a location.
    
    destroy:
    Delete a location.
    """
    queryset = Location.objects.all().select_related('parent').prefetch_related('items', 'children')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['room_type', 'is_box', 'parent']
    search_fields = ['name']
    ordering_fields = ['name', 'room_type', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LocationDetailSerializer
        return LocationSerializer
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get all items in a location"""
        location = self.get_object()
        items = location.items.all()
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get all child locations"""
        location = self.get_object()
        children = location.children.all()
        serializer = LocationSerializer(children, many=True)
        return Response(serializer.data)


class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Item instances.
    
    list:
    Return a list of all items.
    
    retrieve:
    Return a specific item with logs.
    
    create:
    Create a new item.
    
    update:
    Update an item.
    
    destroy:
    Delete an item.
    """
    queryset = Item.objects.all().select_related('location')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location', 'condition']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at', 'quantity']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ItemDetailSerializer
        return ItemSerializer
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get all logs for an item"""
        item = self.get_object()
        logs = item.logs.all()
        serializer = ItemLogSerializer(logs, many=True)
        return Response(serializer.data)


class ItemLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing ItemLog instances (read-only).
    
    list:
    Return a list of all item logs.
    
    retrieve:
    Return a specific item log.
    """
    queryset = ItemLog.objects.all().select_related('item')
    serializer_class = ItemLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['item', 'action']
    search_fields = ['item__name', 'action', 'details']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']

