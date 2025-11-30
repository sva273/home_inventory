import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from services.qr_service import generate_qr_for_box
from .choices import ROOM_CHOICES, CONDITION_CHOICES, ACTION_CHOICES, ROLE_CHOICES, NOTIFICATION_TYPE_CHOICES, EVENT_TYPE_CHOICES
from .images import validate_image_size, validate_image_format, validate_image_dimensions, resize_image

User = get_user_model()

# Create your models here.

class Category(models.Model):
    """Category for organizing items (e.g., Electronics, Furniture, Clothing)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#667eea', help_text='Hex color code for UI display')
    icon = models.CharField(max_length=50, blank=True, help_text='Emoji or icon identifier')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]


class Tag(models.Model):
    """Tag for flexible item categorization"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6c757d', help_text='Hex color code for UI display')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]


class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    room_type = models.CharField(max_length=50, choices=ROOM_CHOICES, null=True, blank=True, verbose_name=_('Room Type'))
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE, verbose_name=_('Parent'))
    is_box = models.BooleanField(default=False)
    qr_code = models.ImageField(upload_to='qr/', null=True, blank=True)
    owner = models.ForeignKey(User, related_name='owned_locations', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Генерируем QR только для коробок
        if self.is_box and not self.qr_code:
            qr_path = generate_qr_for_box(self)
            self.qr_code = qr_path
            super().save(update_fields=['qr_code'])

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Location')
        verbose_name_plural = _('Locations')
        ordering = ['name']
        indexes = [
            models.Index(fields=['room_type']),
            models.Index(fields=['is_box']),
            models.Index(fields=['parent']),
            models.Index(fields=['owner']),
            models.Index(fields=['created_at']),
            models.Index(fields=['room_type', 'is_box']),  # Composite index for common queries
            models.Index(fields=['parent', 'owner']),  # Composite index for filtering
        ]

class LocationShare(models.Model):
    """Model for sharing locations with other users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.ForeignKey('Location', related_name='shares', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='shared_locations', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='created_location_shares', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = _('Location Share')
        verbose_name_plural = _('Location Shares')
        unique_together = ['location', 'user']
        indexes = [
            models.Index(fields=['location', 'user']),
            models.Index(fields=['role']),
            models.Index(fields=['user', 'role']),  # Composite index for user's shares
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.location.name} - {self.user.username} ({self.role})"


class Item(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES, default='good')
    location = models.ForeignKey(Location, related_name='items', on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, related_name='items', on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='items', blank=True)
    owner = models.ForeignKey(User, related_name='owned_items', on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(
        upload_to='items/',
        null=True,
        blank=True,
        validators=[validate_image_size, validate_image_format, validate_image_dimensions],
        help_text=_('Upload an image (JPEG, PNG, GIF, WEBP). Maximum size: 5MB.')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        """Validate item data"""
        if self.quantity <= 0:
            raise ValidationError({'quantity': _('Quantity must be greater than 0')})
        if self.quantity > 10000:
            raise ValidationError({'quantity': _('Quantity is too large (max 10000)')})
        
        # Validate image if provided
        if self.image:
            validate_image_size(self.image)
            validate_image_format(self.image)
            validate_image_dimensions(self.image)
    
    def save(self, *args, **kwargs):
        """Override save to call clean validation and resize image"""
        # Validate before saving
        self.full_clean()
        
        # Resize image if needed
        if self.image:
            # Check if image was changed (new upload or update)
            if not self.pk or (hasattr(self, '_image_changed') and self._image_changed):
                resized_image = resize_image(self.image)
                if resized_image:
                    self.image = resized_image
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Item')
        verbose_name_plural = _('Items')
        ordering = ['-created_at', 'name']
        indexes = [
            models.Index(fields=['location']),
            models.Index(fields=['condition']),
            models.Index(fields=['category']),
            models.Index(fields=['owner']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['location', 'condition']),  # Composite index for filtering
            models.Index(fields=['category', 'condition']),  # Composite index for filtering
            models.Index(fields=['owner', 'created_at']),  # Composite index for user's items
        ]

class ItemShare(models.Model):
    """Model for sharing items with other users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey('Item', related_name='shares', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='shared_items', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='created_item_shares', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = _('Item Share')
        verbose_name_plural = _('Item Shares')
        unique_together = ['item', 'user']
        indexes = [
            models.Index(fields=['item', 'user']),
            models.Index(fields=['role']),
            models.Index(fields=['user', 'role']),  # Composite index for user's shares
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.item.name} - {self.user.username} ({self.role})"


class ItemLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(Item, related_name='logs', on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, related_name='item_logs', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.item.name} - {self.action} at {self.timestamp}"

    class Meta:
        verbose_name = _('Item Log')
        verbose_name_plural = _('Item Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['item']),
            models.Index(fields=['action']),
            models.Index(fields=['user']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['item', 'timestamp']),  # Composite index for item logs
            models.Index(fields=['action', 'timestamp']),  # Composite index for filtering
        ]


class Notification(models.Model):
    """Model for user notifications"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Generic foreign key fields for related objects
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_('Type of related object (Item, Location, etc.)')
    )
    object_id = models.UUIDField(null=True, blank=True, help_text=_('ID of related object'))
    
    # Additional context data (JSON field would be better, but using TextField for compatibility)
    metadata = models.TextField(blank=True, help_text=_('Additional context data (JSON)'))

    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()} - {self.created_at}"

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at', '-read']
        indexes = [
            models.Index(fields=['user', 'read']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['read', 'created_at']),
            models.Index(fields=['user', 'read', 'created_at']),  # Composite index for user's unread notifications
        ]


class AnalyticsEvent(models.Model):
    """Model to track analytics events (views, searches, actions)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_events', null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True, help_text=_('Additional event data (search query, filters, etc.)'))
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Analytics Event')
        verbose_name_plural = _('Analytics Events')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user', 'event_type', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str} - {self.get_event_type_display()} - {self.created_at}"
