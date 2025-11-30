from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Location, Item, ItemLog, Category, Tag, LocationShare, ItemShare, Notification, AnalyticsEvent
from .choices import ROOM_CHOICES

# Create your models here.
class LocationShareInline(admin.TabularInline):
    """Inline для отображения shared access к локации"""
    model = LocationShare
    extra = 0
    fields = ('user', 'role', 'created_at')
    readonly_fields = ('created_at',)


class ItemInline(admin.TabularInline):
    """Inline для отображения предметов в локации"""
    model = Item
    extra = 0
    fields = ('name', 'quantity', 'condition', 'created_at')
    readonly_fields = ('created_at',)


class RoomTypeFilter(admin.SimpleListFilter):
    """Кастомный фильтр для room_type с переводами"""
    title = _('Room Type')
    parameter_name = 'room_type'
    
    def lookups(self, request, model_admin):
        """Возвращает список опций фильтра с переведенными названиями"""
        return ROOM_CHOICES
    
    def queryset(self, request, queryset):
        """Фильтрует queryset по выбранному room_type"""
        if self.value():
            return queryset.filter(room_type=self.value())
        return queryset


class LocationChildrenInline(admin.TabularInline):
    """Inline для отображения дочерних локаций"""
    model = Location
    fk_name = 'parent'
    extra = 0
    fields = ('name', 'room_type_display', 'is_box')
    readonly_fields = ('room_type_display',)
    
    def room_type_display(self, obj):
        """Отображение типа комнаты (переведенное)"""
        return obj.get_room_type_display() if obj.room_type else _('No room type')
    room_type_display.short_description = _('Room Type')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_type_display', 'parent_display', 'owner', 'is_box', 'items_count', 'children_count', 'shares_count', 'qr_code_display')
    list_filter = (RoomTypeFilter, 'is_box', 'parent', 'owner')
    search_fields = ('name', 'owner__username')
    readonly_fields = ('id', 'qr_code_display', 'items_count', 'children_count', 'shares_count', 'created_at')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('id', 'name', 'room_type', 'parent', 'owner')
        }),
        (_('Box Settings'), {
            'fields': ('is_box', 'qr_code', 'qr_code_display'),
            'classes': ('collapse',)
        }),
        (_('Statistics'), {
            'fields': ('items_count', 'children_count', 'shares_count'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    inlines = [LocationChildrenInline, ItemInline, LocationShareInline]
    
    def room_type_display(self, obj):
        """Отображение типа комнаты (переведенное)"""
        return obj.get_room_type_display() if obj.room_type else _('No room type')
    room_type_display.short_description = _('Room Type')
    
    def parent_display(self, obj):
        """Отображение родительской локации"""
        return obj.parent.name if obj.parent else _('No parent')
    parent_display.short_description = _('Parent')
    
    def shares_count(self, obj):
        """Количество shared access"""
        return obj.shares.count()
    shares_count.short_description = _('Shared With')
    
    def items_count(self, obj):
        """Количество предметов в локации"""
        return obj.items.count()
    items_count.short_description = _('Items Count')
    
    def children_count(self, obj):
        """Количество дочерних локаций"""
        return obj.children.count()
    children_count.short_description = _('Children Count')
    
    def qr_code_display(self, obj):
        """Отображение QR кода"""
        if obj.qr_code:
            return format_html('<img src="{}" width="100" height="100" />', obj.qr_code.url)
        return _("No QR code")
    qr_code_display.short_description = _('QR Code')


class ItemShareInline(admin.TabularInline):
    """Inline для отображения shared access к предмету"""
    model = ItemShare
    extra = 0
    fields = ('user', 'role', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'category', 'owner', 'quantity', 'condition', 'tags_display', 'shares_count', 'image_display', 'created_at', 'updated_at')
    list_filter = ('condition', 'location', 'category', 'tags', 'owner', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'owner__username')
    filter_horizontal = ('tags',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'image_display', 'tags_display', 'shares_count')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('id', 'name', 'description', 'quantity', 'condition', 'owner')
        }),
        (_('Organization'), {
            'fields': ('location', 'category', 'tags')
        }),
        (_('Media'), {
            'fields': ('image', 'image_display')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'created_at'
    inlines = [ItemShareInline]
    
    def shares_count(self, obj):
        """Количество shared access"""
        return obj.shares.count()
    shares_count.short_description = _('Shared With')
    
    def tags_display(self, obj):
        """Display tags with colors"""
        tags = obj.tags.all()
        if tags:
            return format_html(
                ' '.join([
                    '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-right: 4px;">{}</span>'.format(
                        tag.color, tag.name
                    ) for tag in tags
                ])
            )
        return '-'
    tags_display.short_description = _('Tags')
    
    def image_display(self, obj):
        """Отображение изображения предмета"""
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return _("No image")
    image_display.short_description = _('Image')
    
    actions = ['mark_as_good_condition', 'mark_as_damaged']
    
    def mark_as_good_condition(self, request, queryset):
        """Действие: пометить как в хорошем состоянии"""
        from django.utils.translation import gettext as _
        updated = queryset.update(condition='good')
        self.message_user(request, _('%(count)d items marked as good condition.') % {'count': updated})
    mark_as_good_condition.short_description = _('Mark selected items as good condition')
    
    def mark_as_damaged(self, request, queryset):
        """Действие: пометить как поврежденные"""
        from django.utils.translation import gettext as _
        updated = queryset.update(condition='damaged')
        self.message_user(request, _('%(count)d items marked as damaged.') % {'count': updated})
    mark_as_damaged.short_description = _('Mark selected items as damaged')


@admin.register(ItemLog)
class ItemLogAdmin(admin.ModelAdmin):
    list_display = ('item', 'action', 'user', 'details_preview', 'timestamp')
    list_filter = ('action', 'timestamp', 'user')
    search_fields = ('item__name', 'action', 'details', 'user__username')
    readonly_fields = ('id', 'item', 'action', 'details', 'timestamp', 'user')
    date_hierarchy = 'timestamp'
    
    def details_preview(self, obj):
        """Предпросмотр деталей (первые 50 символов)"""
        if obj.details:
            return obj.details[:50] + '...' if len(obj.details) > 50 else obj.details
        return '-'
    details_preview.short_description = _('Details')
    
    def has_add_permission(self, request):
        """Запретить создание логов вручную"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Запретить редактирование логов"""
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_display', 'icon', 'items_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'items_count', 'color_display')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('id', 'name', 'description')
        }),
        (_('Display'), {
            'fields': ('color', 'color_display', 'icon')
        }),
        (_('Statistics'), {
            'fields': ('items_count',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def items_count(self, obj):
        """Количество предметов в категории"""
        return obj.items.count()
    items_count.short_description = _('Items Count')
    
    def color_display(self, obj):
        """Отображение цвета"""
        return format_html(
            '<div style="width: 30px; height: 30px; background-color: {}; border-radius: 4px; border: 1px solid #ddd;"></div>',
            obj.color
        )
    color_display.short_description = _('Color Preview')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_display', 'items_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'items_count', 'color_display')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('id', 'name')
        }),
        (_('Display'), {
            'fields': ('color', 'color_display')
        }),
        (_('Statistics'), {
            'fields': ('items_count',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def items_count(self, obj):
        """Количество предметов с этим тегом"""
        return obj.items.count()
    items_count.short_description = _('Items Count')
    
    def color_display(self, obj):
        """Отображение цвета"""
        return format_html(
            '<div style="width: 30px; height: 30px; background-color: {}; border-radius: 4px; border: 1px solid #ddd;"></div>',
            obj.color
        )
    color_display.short_description = _('Color Preview')


@admin.register(LocationShare)
class LocationShareAdmin(admin.ModelAdmin):
    list_display = ('location', 'user', 'role', 'created_by', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('location__name', 'user__username', 'created_by__username')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        (_('Share Information'), {
            'fields': ('id', 'location', 'user', 'role', 'created_by')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ItemShare)
class ItemShareAdmin(admin.ModelAdmin):
    list_display = ('item', 'user', 'role', 'created_by', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('item__name', 'user__username', 'created_by__username')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        (_('Share Information'), {
            'fields': ('id', 'item', 'user', 'role', 'created_by')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'message_preview', 'read', 'created_at')
    list_filter = ('notification_type', 'read', 'created_at')
    search_fields = ('user__username', 'message')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('id', 'user', 'notification_type', 'message', 'read')
        }),
        (_('Related Object'), {
            'fields': ('content_type', 'object_id', 'metadata'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']
    actions = ['mark_as_read', 'mark_as_unread']
    
    def message_preview(self, obj):
        """Display first 50 characters of message"""
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = _('Message')
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        from django.utils.translation import gettext as _
        count = queryset.update(read=True)
        self.message_user(request, _('%(count)d notifications marked as read.') % {'count': count})
    mark_as_read.short_description = _('Mark selected notifications as read')
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        from django.utils.translation import gettext as _
        count = queryset.update(read=False)
        self.message_user(request, _('%(count)d notifications marked as unread.') % {'count': count})
    mark_as_unread.short_description = _('Mark selected notifications as unread')


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    """Admin interface for AnalyticsEvent"""
    list_display = ('user', 'event_type', 'content_type', 'object_id', 'created_at', 'ip_address')
    list_filter = ('event_type', 'content_type', 'created_at', 'user')
    search_fields = ('user__username', 'event_type', 'object_id', 'ip_address')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        (_('Event Information'), {
            'fields': ('id', 'user', 'event_type', 'content_type', 'object_id')
        }),
        (_('Metadata'), {
            'fields': ('metadata', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']