from django.core.management.base import BaseCommand
from django.utils import timezone
from inventory.models import Location, Item, ItemLog
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
            Location.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Data cleared.'))

        self.stdout.write('Generating test data...')

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

        # Sample items data
        items_data = [
            # Living Room items
            ('TV', '55 inch Smart TV', 1, 'good', 'living_room'),
            ('Sofa', 'Comfortable 3-seater sofa', 1, 'good', 'living_room'),
            ('Coffee Table', 'Wooden coffee table', 1, 'good', 'living_room'),
            ('Lamp', 'Floor lamp with LED bulb', 2, 'good', 'living_room'),
            ('Remote Control', 'TV remote control', 1, 'good', 'living_room'),
            
            # Kitchen items
            ('Coffee Maker', 'Automatic coffee maker', 1, 'good', 'kitchen'),
            ('Toaster', '4-slice toaster', 1, 'good', 'kitchen'),
            ('Cutting Board', 'Wooden cutting board', 2, 'good', 'kitchen'),
            ('Knife Set', 'Set of 6 kitchen knives', 1, 'good', 'kitchen'),
            ('Dish Set', 'Dinner plates set', 12, 'good', 'kitchen'),
            
            # Children's Room A items
            ('Teddy Bear', 'Large teddy bear', 1, 'good', 'children_room_a'),
            ('LEGO Set', 'Classic LEGO building set', 1, 'good', 'children_room_a'),
            ('Puzzle', '1000 piece jigsaw puzzle', 3, 'good', 'children_room_a'),
            ('Books', 'Children story books', 15, 'good', 'children_room_a'),
            ('Toy Car', 'Remote control car', 2, 'damaged', 'children_room_a'),
            
            # Children's Room N items
            ('Doll', 'Barbie doll', 3, 'good', 'children_room_n'),
            ('Art Supplies', 'Crayons, markers, paints', 1, 'good', 'children_room_n'),
            ('Board Game', 'Monopoly game', 1, 'good', 'children_room_n'),
            ('Stuffed Animal', 'Various stuffed animals', 8, 'good', 'children_room_n'),
            
            # Office items
            ('Laptop', 'MacBook Pro 15 inch', 1, 'good', 'office'),
            ('Monitor', '27 inch 4K monitor', 1, 'good', 'office'),
            ('Keyboard', 'Mechanical keyboard', 1, 'good', 'office'),
            ('Mouse', 'Wireless mouse', 1, 'good', 'office'),
            ('Printer', 'Inkjet printer', 1, 'good', 'office'),
            ('Desk Lamp', 'LED desk lamp', 1, 'good', 'office'),
            ('Notebooks', 'Office notebooks', 5, 'good', 'office'),
            ('Pens', 'Set of ballpoint pens', 20, 'good', 'office'),
            
            # Attic items
            ('Old Books', 'Collection of old books', 30, 'good', 'attic'),
            ('Photo Albums', 'Family photo albums', 5, 'good', 'attic'),
            ('Vintage Camera', 'Old film camera', 1, 'damaged', 'attic'),
            ('Suitcase', 'Vintage leather suitcase', 2, 'good', 'attic'),
            ('Christmas Decorations', 'Holiday decorations box', 1, 'good', 'attic'),
        ]

        # Generate items
        items = []
        conditions = ['good', 'fair', 'damaged', 'excellent']
        
        for name, description, quantity, condition, room_type in items_data:
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
                location=location
            )
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
            f'  - {Item.objects.count()} items\n'
            f'  - {ItemLog.objects.count()} logs'
        ))

