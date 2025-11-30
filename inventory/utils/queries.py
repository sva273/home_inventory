"""
Query optimization utilities for Home Inventory application.
"""
from django.db import models


def optimize_location_queryset(queryset=None):
    """
    Optimize Location queryset with select_related and prefetch_related.
    
    Args:
        queryset: Optional base queryset (defaults to Location.objects.all())
    
    Returns:
        Optimized queryset
    """
    from ..models import Location
    
    if queryset is None:
        queryset = Location.objects.all()
    
    return queryset.select_related(
        'parent',
        'owner',
    ).prefetch_related(
        'items__category',
        'items__owner',
        'items__tags',
        'items__shares__user',
        'items__shares__created_by',
        'children__owner',
        'children__shares__user',
        'shares__user',
        'shares__created_by',
    )


def optimize_item_queryset(queryset=None):
    """
    Optimize Item queryset with select_related and prefetch_related.
    
    Args:
        queryset: Optional base queryset (defaults to Item.objects.all())
    
    Returns:
        Optimized queryset
    """
    from ..models import Item
    
    if queryset is None:
        queryset = Item.objects.all()
    
    return queryset.select_related(
        'location__parent',
        'location__owner',
        'category',
        'owner',
    ).prefetch_related(
        'tags',
        'shares__user',
        'shares__created_by',
        'logs__user',
    )


def optimize_itemlog_queryset(queryset=None):
    """
    Optimize ItemLog queryset with select_related.
    
    Args:
        queryset: Optional base queryset (defaults to ItemLog.objects.all())
    
    Returns:
        Optimized queryset
    """
    from ..models import ItemLog
    
    if queryset is None:
        queryset = ItemLog.objects.all()
    
    return queryset.select_related(
        'item__location',
        'item__category',
        'item__owner',
        'user',
    )


def optimize_category_queryset(queryset=None):
    """
    Optimize Category queryset with prefetch_related.
    
    Args:
        queryset: Optional base queryset (defaults to Category.objects.all())
    
    Returns:
        Optimized queryset
    """
    from ..models import Category
    
    if queryset is None:
        queryset = Category.objects.all()
    
    return queryset.prefetch_related(
        'items__location',
        'items__owner',
        'items__tags',
    )


def optimize_tag_queryset(queryset=None):
    """
    Optimize Tag queryset with prefetch_related.
    
    Args:
        queryset: Optional base queryset (defaults to Tag.objects.all())
    
    Returns:
        Optimized queryset
    """
    from ..models import Tag
    
    if queryset is None:
        queryset = Tag.objects.all()
    
    return queryset.prefetch_related(
        'items__location',
        'items__category',
        'items__owner',
    )


def get_optimized_statistics():
    """
    Get optimized statistics using single queries with annotations.
    
    Returns:
        dict with statistics
    """
    from ..models import Location, Item
    from django.db.models import Count, Q
    
    return {
        'total_locations': Location.objects.count(),
        'total_items': Item.objects.count(),
        'boxes_count': Location.objects.filter(is_box=True).count(),
        'rooms_count': Location.objects.filter(is_box=False, room_type__isnull=False).count(),
        'items_by_condition': dict(
            Item.objects.values('condition')
            .annotate(count=Count('id'))
            .values_list('condition', 'count')
        ),
        'items_by_category': dict(
            Item.objects.filter(category__isnull=False)
            .values('category__name')
            .annotate(count=Count('id'))
            .values_list('category__name', 'count')
        ),
    }

