from rest_framework import serializers
from .models import Location, Item, ItemLog
from .choices import ROOM_CHOICES


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location model"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    children_count = serializers.IntegerField(source='children.count', read_only=True)
    room_type_display = serializers.CharField(source='get_room_type_display', read_only=True)
    
    class Meta:
        model = Location
        fields = [
            'id', 'name', 'room_type', 'room_type_display', 'parent', 
            'parent_name', 'is_box', 'qr_code', 'items_count', 'children_count'
        ]
        read_only_fields = ['id', 'qr_code']


class ItemSerializer(serializers.ModelSerializer):
    """Serializer for Item model"""
    location_name = serializers.CharField(source='location.name', read_only=True)
    condition_display = serializers.SerializerMethodField()
    
    def get_condition_display(self, obj):
        return obj.condition.title() if obj.condition else ''
    
    class Meta:
        model = Item
        fields = [
            'id', 'name', 'description', 'quantity', 'condition', 
            'condition_display', 'location', 'location_name', 'image', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ItemLogSerializer(serializers.ModelSerializer):
    """Serializer for ItemLog model"""
    item_name = serializers.CharField(source='item.name', read_only=True)
    
    class Meta:
        model = ItemLog
        fields = ['id', 'item', 'item_name', 'action', 'details', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class LocationDetailSerializer(LocationSerializer):
    """Extended serializer for Location with nested items and children"""
    items = ItemSerializer(many=True, read_only=True)
    children = LocationSerializer(many=True, read_only=True)
    
    class Meta(LocationSerializer.Meta):
        fields = LocationSerializer.Meta.fields + ['items', 'children']


class ItemDetailSerializer(ItemSerializer):
    """Extended serializer for Item with nested logs"""
    logs = ItemLogSerializer(many=True, read_only=True)
    
    class Meta(ItemSerializer.Meta):
        fields = ItemSerializer.Meta.fields + ['logs']

