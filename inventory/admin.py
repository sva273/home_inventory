from django.contrib import admin
from django.utils.html import format_html
from .models import Location, Item, ItemLog


class ItemInline(admin.TabularInline):
    """Inline для отображения предметов в локации"""
    model = Item
    extra = 0
    fields = ('name', 'quantity', 'condition', 'created_at')
    readonly_fields = ('created_at',)


class LocationChildrenInline(admin.TabularInline):
    """Inline для отображения дочерних локаций"""
    model = Location
    fk_name = 'parent'
    extra = 0
    fields = ('name', 'room_type', 'is_box')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_type', 'parent', 'is_box', 'items_count', 'children_count', 'qr_code_display')
    list_filter = ('room_type', 'is_box', 'parent')
    search_fields = ('name',)
    readonly_fields = ('id', 'qr_code_display', 'items_count', 'children_count')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'room_type', 'parent')
        }),
        ('Box Settings', {
            'fields': ('is_box', 'qr_code', 'qr_code_display'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('items_count', 'children_count'),
            'classes': ('collapse',)
        }),
    )
    inlines = [LocationChildrenInline, ItemInline]
    
    def items_count(self, obj):
        """Количество предметов в локации"""
        return obj.items.count()
    items_count.short_description = 'Items Count'
    
    def children_count(self, obj):
        """Количество дочерних локаций"""
        return obj.children.count()
    children_count.short_description = 'Children Count'
    
    def qr_code_display(self, obj):
        """Отображение QR кода"""
        if obj.qr_code:
            return format_html('<img src="{}" width="100" height="100" />', obj.qr_code.url)
        return "No QR code"
    qr_code_display.short_description = 'QR Code'


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'quantity', 'condition', 'image_display', 'created_at', 'updated_at')
    list_filter = ('condition', 'location', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at', 'image_display')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'quantity', 'condition')
        }),
        ('Location', {
            'fields': ('location',)
        }),
        ('Media', {
            'fields': ('image', 'image_display')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'created_at'
    
    def image_display(self, obj):
        """Отображение изображения предмета"""
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return "No image"
    image_display.short_description = 'Image'
    
    actions = ['mark_as_good_condition', 'mark_as_damaged']
    
    def mark_as_good_condition(self, request, queryset):
        """Действие: пометить как в хорошем состоянии"""
        updated = queryset.update(condition='good')
        self.message_user(request, f'{updated} items marked as good condition.')
    mark_as_good_condition.short_description = 'Mark selected items as good condition'
    
    def mark_as_damaged(self, request, queryset):
        """Действие: пометить как поврежденные"""
        updated = queryset.update(condition='damaged')
        self.message_user(request, f'{updated} items marked as damaged.')
    mark_as_damaged.short_description = 'Mark selected items as damaged'


@admin.register(ItemLog)
class ItemLogAdmin(admin.ModelAdmin):
    list_display = ('item', 'action', 'details_preview', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('item__name', 'action', 'details')
    readonly_fields = ('id', 'item', 'action', 'details', 'timestamp')
    date_hierarchy = 'timestamp'
    
    def details_preview(self, obj):
        """Предпросмотр деталей (первые 50 символов)"""
        if obj.details:
            return obj.details[:50] + '...' if len(obj.details) > 50 else obj.details
        return '-'
    details_preview.short_description = 'Details'
    
    def has_add_permission(self, request):
        """Запретить создание логов вручную"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Запретить редактирование логов"""
        return False