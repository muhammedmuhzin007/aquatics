from django.core.management.base import BaseCommand
from store.models import CustomUser, Fish, Order, OrderItem
from decimal import Decimal
import random
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Generate 100 sample orders with random data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting order generation...')

        # Get all customers and fish
        customers = list(CustomUser.objects.filter(role='customer'))
        fishes = list(Fish.objects.all())

        if not customers:
            self.stdout.write(self.style.ERROR('No customers found! Please create customer accounts first.'))
            return

        if not fishes:
            self.stdout.write(self.style.ERROR('No fish found! Please add fish to the database first.'))
            return

        statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        addresses = [
            "123 Main Street, Apartment 4B\nNew York, NY 10001",
            "456 Oak Avenue\nLos Angeles, CA 90012",
            "789 Maple Drive, Suite 200\nChicago, IL 60601",
            "321 Pine Road\nHouston, TX 77001",
            "654 Elm Street\nPhoenix, AZ 85001",
            "987 Cedar Lane, Unit 5\nPhiladelphia, PA 19019",
            "147 Birch Boulevard\nSan Antonio, TX 78201",
            "258 Willow Way\nSan Diego, CA 92101",
            "369 Spruce Street\nDallas, TX 75201",
            "741 Ash Avenue\nSan Jose, CA 95101",
        ]

        phones = [
            '+1-555-0101',
            '+1-555-0102',
            '+1-555-0103',
            '+1-555-0104',
            '+1-555-0105',
            '+1-555-0106',
            '+1-555-0107',
            '+1-555-0108',
            '+1-555-0109',
            '+1-555-0110',
        ]

        orders_created = 0

        for i in range(100):
            try:
                # Random customer
                customer = random.choice(customers)
                
                # Random date within last 6 months
                days_ago = random.randint(0, 180)
                order_date = timezone.now() - timedelta(days=days_ago)
                
                # Random status
                status = random.choice(statuses)
                
                # Create order
                order = Order.objects.create(
                    user=customer,
                    order_number=Order.generate_order_number(),
                    total_amount=Decimal('0.00'),  # Will calculate below
                    status=status,
                    shipping_address=random.choice(addresses),
                    phone_number=random.choice(phones),
                    created_at=order_date,
                    updated_at=order_date + timedelta(hours=random.randint(1, 48))
                )

                # Add 1-5 random items to the order
                num_items = random.randint(1, 5)
                total_amount = Decimal('0.00')

                selected_fishes = random.sample(fishes, min(num_items, len(fishes)))

                for fish in selected_fishes:
                    quantity = random.randint(1, 3)
                    price = fish.price
                    
                    OrderItem.objects.create(
                        order=order,
                        fish=fish,
                        quantity=quantity,
                        price=price
                    )
                    
                    total_amount += price * quantity

                # Update order total
                order.total_amount = total_amount
                order.save()

                orders_created += 1
                
                if (i + 1) % 10 == 0:
                    self.stdout.write(f'Created {i + 1} orders...')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating order {i + 1}: {str(e)}'))
                continue

        self.stdout.write(self.style.SUCCESS(f'Successfully created {orders_created} orders!'))
