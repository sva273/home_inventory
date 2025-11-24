import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from services.qr_service import generate_qr_for_box
from .choices import ROOM_CHOICES, CONDITION_CHOICES, ACTION_CHOICES

# Create your models here.

class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    room_type = models.CharField(max_length=50, choices=ROOM_CHOICES, null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    is_box = models.BooleanField(default=False)
    qr_code = models.ImageField(upload_to='qr/', null=True, blank=True)

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
        ]

class Item(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES, default='good')
    location = models.ForeignKey(Location, related_name='items', on_delete=models.SET_NULL, null=True, blank=True)
    
    def clean(self):
        """Validate item data"""
        if self.quantity <= 0:
            raise ValidationError({'quantity': _('Quantity must be greater than 0')})
        if self.quantity > 10000:
            raise ValidationError({'quantity': _('Quantity is too large (max 10000)')})
    
    def save(self, *args, **kwargs):
        """Override save to call clean validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    image = models.ImageField(upload_to='items/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Item')
        verbose_name_plural = _('Items')
        ordering = ['-created_at', 'name']
        indexes = [
            models.Index(fields=['location']),
            models.Index(fields=['condition']),
            models.Index(fields=['created_at']),
        ]

class ItemLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(Item, related_name='logs', on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.name} - {self.action} at {self.timestamp}"

    class Meta:
        verbose_name = _('Item Log')
        verbose_name_plural = _('Item Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['item']),
            models.Index(fields=['action']),
            models.Index(fields=['timestamp']),
        ]
