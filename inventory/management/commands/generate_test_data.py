from django.core.management.base import BaseCommand
from django.utils import timezone
from inventory.models import Location, Item, ItemLog, Category, Tag
from inventory.choices import ROOM_CHOICES
import random


class Command(BaseCommand):
    help = 'Generate test data for inventory app'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            ItemLog.objects.all().delete()
            Item.objects.all().delete()
            Tag.objects.all().delete()
            Category.objects.all().delete()
            Location.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Data cleared.'))

        self.stdout.write('Generating test data...')

        # Create categories
        categories_data = [
            ('Electronics', 'Electronic devices and gadgets', '#667eea', '📱'),
            ('Furniture', 'Furniture and home decor', '#764ba2', '🪑'),
            ('Kitchenware', 'Kitchen items and utensils', '#f093fb', '🍳'),
            ('Toys', 'Children toys and games', '#4facfe', '🧸'),
            ('Clothing', 'Clothes and accessories', '#43e97b', '👕'),
            ('Books', 'Books and reading materials', '#fa709a', '📚'),
            ('Office Supplies', 'Office equipment and supplies', '#fee140', '📎'),
            ('Tools', 'Tools and hardware', '#30cfd0', '🔧'),
        ]
        
        categories = {}
        for name, description, color, icon in categories_data:
            category = Category.objects.create(
                name=name,
                description=description,
                color=color,
                icon=icon
            )
            categories[name] = category
            self.stdout.write(f'Created category: {category.name}')

        # Create tags
        tags_data = [
            ('Valuable', '#dc3545'),
            ('Fragile', '#ffc107'),
            ('Seasonal', '#17a2b8'),
            ('Gift', '#28a745'),
            ('Vintage', '#6c757d'),
            ('New', '#20c997'),
            ('Needs Repair', '#fd7e14'),
            ('Donate', '#e83e8c'),
        ]
        
        tags = {}
        for name, color in tags_data:
            tag = Tag.objects.create(name=name, color=color)
            tags[name] = tag
            self.stdout.write(f'Created tag: {tag.name}')

        # Room types
        room_types = [choice[0] for choice in ROOM_CHOICES]

        # Generate main locations (rooms)
        rooms = {}
        room_names = {
            'living_room': 'Living Room',
            'kitchen': 'Kitchen',
            'children_room_a': "Children's Room A",
            'children_room_n': "Children's Room N",
            'office': 'Office',
            'attic': 'Attic',
        }

        for room_type in room_types:
            room = Location.objects.create(
                name=room_names[room_type],
                room_type=room_type,
                is_box=False
            )
            rooms[room_type] = room
            self.stdout.write(f'Created room: {room.name}')

        # Generate boxes in different rooms
        boxes = []
        box_data = [
            ('Box 1 - Electronics', 'living_room'),
            ('Box 2 - Books', 'living_room'),
            ('Box 3 - Kitchen Utensils', 'kitchen'),
            ('Box 4 - Toys', 'children_room_a'),
            ('Box 5 - Clothes', 'children_room_n'),
            ('Box 6 - Documents', 'office'),
            ('Box 7 - Old Items', 'attic'),
            ('Box 8 - Tools', 'attic'),
        ]

        for box_name, room_type in box_data:
            box = Location.objects.create(
                name=box_name,
                parent=rooms[room_type],
                is_box=True
            )
            boxes.append(box)
            self.stdout.write(f'Created box: {box.name}')

        # Generate sub-locations (shelves, cabinets, etc.)
        sub_locations = []
        sub_location_data = [
            ('Top Shelf', 'living_room'),
            ('Bottom Shelf', 'living_room'),
            ('Kitchen Cabinet', 'kitchen'),
            ('Refrigerator', 'kitchen'),
            ('Desk Drawer', 'office'),
            ('Wardrobe', 'children_room_a'),
        ]

        for sub_name, room_type in sub_location_data:
            sub = Location.objects.create(
                name=sub_name,
                parent=rooms[room_type],
                is_box=False
            )
            sub_locations.append(sub)
            self.stdout.write(f'Created sub-location: {sub.name}')

        # Sample items data with categories and tags
        items_data = [
            # Living Room items
            ('TV', '55 inch Smart TV', 1, 'good', 'living_room', 'Electronics', ['Valuable', 'Fragile']),
            ('Sofa', 'Comfortable 3-seater sofa', 1, 'good', 'living_room', 'Furniture', ['Valuable']),
            ('Coffee Table', 'Wooden coffee table', 1, 'good', 'living_room', 'Furniture', []),
            ('Lamp', 'Floor lamp with LED bulb', 2, 'good', 'living_room', 'Furniture', []),
            ('Remote Control', 'TV remote control', 1, 'good', 'living_room', 'Electronics', []),
            
            # Kitchen items
            ('Coffee Maker', 'Automatic coffee maker', 1, 'good', 'kitchen', 'Kitchenware', []),
            ('Toaster', '4-slice toaster', 1, 'good', 'kitchen', 'Kitchenware', []),
            ('Cutting Board', 'Wooden cutting board', 2, 'good', 'kitchen', 'Kitchenware', []),
            ('Knife Set', 'Set of 6 kitchen knives', 1, 'good', 'kitchen', 'Kitchenware', ['Fragile']),
            ('Dish Set', 'Dinner plates set', 12, 'good', 'kitchen', 'Kitchenware', ['Fragile']),
            
            # Children's Room A items
            ('Teddy Bear', 'Large teddy bear', 1, 'good', 'children_room_a', 'Toys', ['Gift']),
            ('LEGO Set', 'Classic LEGO building set', 1, 'good', 'children_room_a', 'Toys', []),
            ('Puzzle', '1000 piece jigsaw puzzle', 3, 'good', 'children_room_a', 'Toys', []),
            ('Books', 'Children story books', 15, 'good', 'children_room_a', 'Books', []),
            ('Toy Car', 'Remote control car', 2, 'damaged', 'children_room_a', 'Toys', ['Needs Repair']),
            
            # Children's Room N items
            ('Doll', 'Barbie doll', 3, 'good', 'children_room_n', 'Toys', ['Gift']),
            ('Art Supplies', 'Crayons, markers, paints', 1, 'good', 'children_room_n', 'Office Supplies', []),
            ('Board Game', 'Monopoly game', 1, 'good', 'children_room_n', 'Toys', []),
            ('Stuffed Animal', 'Various stuffed animals', 8, 'good', 'children_room_n', 'Toys', []),
            
            # Office items
            ('Laptop', 'MacBook Pro 15 inch', 1, 'good', 'office', 'Electronics', ['Valuable', 'Fragile']),
            ('Monitor', '27 inch 4K monitor', 1, 'good', 'office', 'Electronics', ['Valuable', 'Fragile']),
            ('Keyboard', 'Mechanical keyboard', 1, 'good', 'office', 'Electronics', []),
            ('Mouse', 'Wireless mouse', 1, 'good', 'office', 'Electronics', []),
            ('Printer', 'Inkjet printer', 1, 'good', 'office', 'Electronics', []),
            ('Desk Lamp', 'LED desk lamp', 1, 'good', 'office', 'Furniture', []),
            ('Notebooks', 'Office notebooks', 5, 'good', 'office', 'Office Supplies', []),
            ('Pens', 'Set of ballpoint pens', 20, 'good', 'office', 'Office Supplies', []),
            
            # Attic items
            ('Old Books', 'Collection of old books', 30, 'good', 'attic', 'Books', ['Vintage']),
            ('Photo Albums', 'Family photo albums', 5, 'good', 'attic', 'Books', ['Vintage']),
            ('Vintage Camera', 'Old film camera', 1, 'damaged', 'attic', 'Electronics', ['Vintage', 'Needs Repair']),
            ('Suitcase', 'Vintage leather suitcase', 2, 'good', 'attic', 'Furniture', ['Vintage']),
            ('Christmas Decorations', 'Holiday decorations box', 1, 'good', 'attic', 'Furniture', ['Seasonal']),
        ]

        # Generate items
        items = []
        conditions = ['good', 'fair', 'damaged', 'excellent']
        
        for item_data in items_data:
            if len(item_data) == 5:
                # Old format without category/tags
                name, description, quantity, condition, room_type = item_data
                category = None
                item_tags = []
            else:
                # New format with category/tags
                name, description, quantity, condition, room_type, category_name, tag_names = item_data
                category = categories.get(category_name)
                item_tags = [tags[tag_name] for tag_name in tag_names if tag_name in tags]
            
            # Randomly assign to room, box, or sub-location
            location_choice = random.choice(['room', 'box', 'sub'])
            
            if location_choice == 'box' and boxes:
                location = random.choice(boxes)
            elif location_choice == 'sub' and sub_locations:
                location = random.choice(sub_locations)
            else:
                location = rooms[room_type]
            
            item = Item.objects.create(
                name=name,
                description=description,
                quantity=quantity,
                condition=condition,
                location=location,
                category=category
            )
            
            # Add tags
            if item_tags:
                item.tags.set(item_tags)
            
            items.append(item)
            
            # Create logs for some items
            if random.random() > 0.5:  # 50% chance
                actions = ['created', 'moved', 'updated']
                action = random.choice(actions)
                details = f'Item {action}'
                
                ItemLog.objects.create(
                    item=item,
                    action=action,
                    details=details
                )

        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully generated test data:\n'
            f'  - {Location.objects.count()} locations\n'
            f'  - {Category.objects.count()} categories\n'
            f'  - {Tag.objects.count()} tags\n'
            f'  - {Item.objects.count()} items\n'
            f'  - {ItemLog.objects.count()} logs'
        ))

