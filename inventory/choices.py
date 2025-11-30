# Choices for inventory models
from django.utils.translation import gettext_lazy as _

ROOM_CHOICES = [
    ('living_room', _('Living Room')),
    ('kitchen', _('Kitchen')),
    ('children_room_a', _("Children's Room A")),
    ('children_room_n', _("Children's Room N")),
    ('office', _('Office')),
    ('attic', _('Attic')),
]

CONDITION_CHOICES = [
    ('excellent', _('Excellent')),
    ('good', _('Good')),
    ('fair', _('Fair')),
    ('damaged', _('Damaged')),
    ('poor', _('Poor')),
]

ACTION_CHOICES = [
    ('created', _('Created')),
    ('updated', _('Updated')),
    ('moved', _('Moved')),
    ('deleted', _('Deleted')),
]

ROLE_CHOICES = [
    ('owner', _('Owner')),
    ('editor', _('Editor')),
    ('viewer', _('Viewer')),
]

NOTIFICATION_TYPE_CHOICES = [
    ('item_created', _('Item Created')),
    ('item_updated', _('Item Updated')),
    ('item_moved', _('Item Moved')),
    ('item_deleted', _('Item Deleted')),
    ('location_shared', _('Location Shared')),
    ('item_shared', _('Item Shared')),
    ('location_created', _('Location Created')),
    ('location_updated', _('Location Updated')),
    ('share_revoked', _('Share Revoked')),
]

EVENT_TYPE_CHOICES = [
    ('item_view', _('Item Viewed')),
    ('location_view', _('Location Viewed')),
    ('item_search', _('Item Searched')),
    ('location_search', _('Location Searched')),
    ('item_created', _('Item Created')),
    ('item_updated', _('Item Updated')),
    ('item_deleted', _('Item Deleted')),
    ('location_created', _('Location Created')),
    ('location_updated', _('Location Updated')),
    ('location_deleted', _('Location Deleted')),
]

