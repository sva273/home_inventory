from rest_framework import serializers
from django.db.models import Prefetch, Count
from django.utils.translation import gettext_lazy as _
from .models import Location, Item, ItemLog, Category, Tag, LocationShare, ItemShare, Notification
from .choices import ROOM_CHOICES


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    items_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'color', 'icon', 'items_count', 'created_at']
        read_only_fields = ['id', 'created_at']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""
    items_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'items_count', 'created_at']
        read_only_fields = ['id', 'created_at']


class LocationShareSerializer(serializers.ModelSerializer):
    """Serializer for LocationShare model"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = LocationShare
        fields = [
            'id', 'location', 'user', 'user_username', 'user_email',
            'role', 'role_display', 'created_at', 'created_by', 'created_by_username'
        ]
        read_only_fields = ['id', 'created_at']


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location model"""
    parent_name = serializers.CharField(source='parent.name', read_only=True, label=_('Parent'))
    items_count = serializers.IntegerField(read_only=True)
    children_count = serializers.IntegerField(read_only=True)
    room_type_display = serializers.CharField(source='get_room_type_display', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    is_owner = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    
    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.owner == request.user
        return False
    
    def get_user_role(self, obj):
        """
        Get user role for location (optimized - uses prefetched shares).
        This method uses prefetched shares from the queryset to avoid N+1 queries.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # Check if user is owner (no DB query needed)
        if obj.owner == request.user:
            return 'owner'
        
        # Use prefetched shares if available (from ViewSet queryset)
        # Check if user_shares attribute exists (from Prefetch with to_attr)
        if hasattr(obj, 'user_shares'):
            # Use prefetched shares from Prefetch with to_attr
            for share in obj.user_shares:
                if share.user_id == request.user.id:
                    return share.role
        # Check if shares are in _prefetched_objects_cache (standard prefetch)
        elif hasattr(obj, '_prefetched_objects_cache') and 'shares' in obj._prefetched_objects_cache:
            prefetched_shares = obj._prefetched_objects_cache['shares']
            for share in prefetched_shares:
                if share.user_id == request.user.id:
                    return share.role
        # Fallback: check if user_shares dict is in context (from ViewSet)
        user_shares = self.context.get('user_location_shares', {})
        if obj.id in user_shares:
            return user_shares[obj.id]
        
        # Last resort: single query (should be rare if ViewSet is optimized)
        share = LocationShare.objects.filter(location=obj, user=request.user).first()
        if share:
            return share.role
        
        return None
    
    class Meta:
        model = Location
        fields = [
            'id', 'name', 'room_type', 'room_type_display', 'parent', 
            'parent_name', 'is_box', 'qr_code', 'items_count', 'children_count',
            'owner', 'owner_username', 'is_owner', 'user_role', 'created_at'
        ]
        read_only_fields = ['id', 'qr_code', 'created_at']


class ItemShareSerializer(serializers.ModelSerializer):
    """Serializer for ItemShare model"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ItemShare
        fields = [
            'id', 'item', 'user', 'user_username', 'user_email',
            'role', 'role_display', 'created_at', 'created_by', 'created_by_username'
        ]
        read_only_fields = ['id', 'created_at']


class ItemSerializer(serializers.ModelSerializer):
    """Serializer for Item model"""
    location_name = serializers.CharField(source='location.name', read_only=True)
    condition_display = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Tag.objects.all(), 
        source='tags', 
        write_only=True,
        required=False
    )
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    is_owner = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    
    def get_condition_display(self, obj):
        return obj.condition.title() if obj.condition else ''
    
    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.owner == request.user
        return False
    
    def get_user_role(self, obj):
        """
        Get user role for item (optimized - uses prefetched shares).
        This method uses prefetched shares from the queryset to avoid N+1 queries.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # Check if user is owner (no DB query needed)
        if obj.owner == request.user:
            return 'owner'
        
        # Use prefetched shares if available (from ViewSet queryset)
        # Check if user_shares attribute exists (from Prefetch with to_attr)
        if hasattr(obj, 'user_shares'):
            # Use prefetched item shares from Prefetch with to_attr
            for share in obj.user_shares:
                if share.user_id == request.user.id:
                    return share.role
        # Check standard prefetch cache
        elif hasattr(obj, '_prefetched_objects_cache') and 'shares' in obj._prefetched_objects_cache:
            prefetched_shares = obj._prefetched_objects_cache['shares']
            for share in prefetched_shares:
                if share.user_id == request.user.id:
                    return share.role
        
        # Check context for cached shares (from ViewSet)
        user_item_shares = self.context.get('user_item_shares', {})
        if obj.id in user_item_shares:
            return user_item_shares[obj.id]
        
        # Check location share if item has location
        if obj.location:
            # Use prefetched location shares if available (from Prefetch with to_attr)
            if hasattr(obj.location, 'user_location_shares'):
                for share in obj.location.user_location_shares:
                    if share.user_id == request.user.id:
                        return share.role
            # Check standard prefetch cache
            elif hasattr(obj.location, '_prefetched_objects_cache') and 'shares' in obj.location._prefetched_objects_cache:
                prefetched_location_shares = obj.location._prefetched_objects_cache['shares']
                for share in prefetched_location_shares:
                    if share.user_id == request.user.id:
                        return share.role
            
            # Check context for cached location shares
            user_location_shares = self.context.get('user_location_shares', {})
            if obj.location.id in user_location_shares:
                return user_location_shares[obj.location.id]
            
            # Last resort: single query (should be rare if ViewSet is optimized)
            location_share = LocationShare.objects.filter(
                location=obj.location, user=request.user
            ).first()
            if location_share:
                return location_share.role
        
        # Last resort: check item share directly
        share = ItemShare.objects.filter(item=obj, user=request.user).first()
        if share:
            return share.role
        
        return None
    
    class Meta:
        model = Item
        fields = [
            'id', 'name', 'description', 'quantity', 'condition', 
            'condition_display', 'location', 'location_name', 
            'category', 'category_name', 'category_color',
            'tags', 'tag_ids', 'image', 
            'owner', 'owner_username', 'is_owner', 'user_role',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ItemLogSerializer(serializers.ModelSerializer):
    """Serializer for ItemLog model"""
    item_name = serializers.CharField(source='item.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ItemLog
        fields = ['id', 'item', 'item_name', 'action', 'details', 'timestamp', 'user', 'user_username']
        read_only_fields = ['id', 'timestamp']


class LocationDetailSerializer(LocationSerializer):
    """Extended serializer for Location with nested items and children"""
    items = ItemSerializer(many=True, read_only=True)
    children = LocationSerializer(many=True, read_only=True)
    shares = LocationShareSerializer(many=True, read_only=True)
    
    class Meta(LocationSerializer.Meta):
        fields = LocationSerializer.Meta.fields + ['items', 'children', 'shares']


class ItemDetailSerializer(ItemSerializer):
    """Extended serializer for Item with nested logs"""
    logs = ItemLogSerializer(many=True, read_only=True)
    category_detail = CategorySerializer(source='category', read_only=True)
    shares = ItemShareSerializer(many=True, read_only=True)
    
    class Meta(ItemSerializer.Meta):
        fields = ItemSerializer.Meta.fields + ['logs', 'category_detail', 'shares']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    related_object_type = serializers.CharField(source='content_type.model', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'notification_type', 'notification_type_display',
            'message', 'read', 'created_at', 'content_type', 'object_id',
            'related_object_type', 'metadata'
        ]
        read_only_fields = ['id', 'created_at']

