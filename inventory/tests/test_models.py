from django.test import TestCase
from django.core.exceptions import ValidationError
from inventory.models import Location, Item, ItemLog
from inventory.choices import ROOM_CHOICES, CONDITION_CHOICES


class LocationModelTest(TestCase):
    """Tests for Location model"""
    
    def setUp(self):
        self.location = Location.objects.create(
            name='Test Location',
            room_type='living_room'
        )
    
    def test_location_creation(self):
        """Test location can be created"""
        self.assertEqual(self.location.name, 'Test Location')
        self.assertEqual(self.location.room_type, 'living_room')
        self.assertFalse(self.location.is_box)
    
    def test_location_hierarchy(self):
        """Test location parent-child relationship"""
        child = Location.objects.create(
            name='Child Location',
            parent=self.location
        )
        self.assertEqual(child.parent, self.location)
        self.assertIn(child, self.location.children.all())
    
    def test_circular_reference_prevention(self):
        """Test that circular references are prevented"""
        child = Location.objects.create(
            name='Child',
            parent=self.location
        )
        # Try to set parent as child of its child
        with self.assertRaises(ValueError):
            self.location.parent = child
            self.location.save()


class ItemModelTest(TestCase):
    """Tests for Item model"""
    
    def setUp(self):
        self.location = Location.objects.create(name='Test Location')
        self.item = Item.objects.create(
            name='Test Item',
            quantity=5,
            condition='good',
            location=self.location
        )
    
    def test_item_creation(self):
        """Test item can be created"""
        self.assertEqual(self.item.name, 'Test Item')
        self.assertEqual(self.item.quantity, 5)
        self.assertEqual(self.item.condition, 'good')
        self.assertEqual(self.item.location, self.location)
    
    def test_item_quantity_validation(self):
        """Test quantity validation"""
        # Test zero quantity
        item = Item(name='Test', quantity=0)
        with self.assertRaises(ValidationError):
            item.full_clean()
        
        # Test negative quantity (shouldn't be possible with PositiveIntegerField)
        # But we test our custom validation
        item = Item(name='Test', quantity=10001)
        with self.assertRaises(ValidationError):
            item.full_clean()
    
    def test_item_location_relationship(self):
        """Test item-location relationship"""
        self.assertIn(self.item, self.location.items.all())


class ItemLogModelTest(TestCase):
    """Tests for ItemLog model"""
    
    def setUp(self):
        self.location = Location.objects.create(name='Test Location')
        self.item = Item.objects.create(
            name='Test Item',
            location=self.location
        )
    
    def test_log_creation(self):
        """Test log can be created"""
        log = ItemLog.objects.create(
            item=self.item,
            action='created',
            details='Test log entry'
        )
        self.assertEqual(log.item, self.item)
        self.assertEqual(log.action, 'created')
        self.assertIn(log, self.item.logs.all())


class SignalsTest(TestCase):
    """Tests for signals"""
    
    def setUp(self):
        self.location = Location.objects.create(name='Test Location')
    
    def test_auto_log_on_item_creation(self):
        """Test that log is automatically created when item is created"""
        item = Item.objects.create(
            name='Test Item',
            location=self.location
        )
        # Check that log was created
        logs = ItemLog.objects.filter(item=item, action='created')
        self.assertEqual(logs.count(), 1)
        self.assertIn('created', logs.first().details.lower())
    
    def test_auto_log_on_item_update(self):
        """Test that log is created when item is updated"""
        item = Item.objects.create(
            name='Test Item',
            location=self.location
        )
        # Clear initial log
        ItemLog.objects.filter(item=item).delete()
        
        # Update item
        item.name = 'Updated Item'
        item.save(update_fields=['name'])
        
        # Check that log was created
        logs = ItemLog.objects.filter(item=item, action='updated')
        self.assertEqual(logs.count(), 1)
    
    def test_auto_log_on_item_move(self):
        """Test that log is created when item location changes"""
        new_location = Location.objects.create(name='New Location')
        item = Item.objects.create(
            name='Test Item',
            location=self.location
        )
        # Clear initial log
        ItemLog.objects.filter(item=item).delete()
        
        # Move item
        item.location = new_location
        item.save(update_fields=['location'])
        
        # Check that log was created
        logs = ItemLog.objects.filter(item=item, action='moved')
        self.assertEqual(logs.count(), 1)

