from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import random

from store.models import CustomUser, Order, OrderItem, Fish, Category, Breed


class Command(BaseCommand):
    help = 'Seed 30 orders with random dates in November (current year).'

    def handle(self, *args, **options):
        now = timezone.now()
        year = now.year
        month = 11  # November

        created = 0
        with transaction.atomic():
            # Ensure there is at least one customer user
            user = CustomUser.objects.filter(role='customer').order_by('?').first()
            if not user:
                user, _ = CustomUser.objects.get_or_create(
                    username='seed_customer',
                    defaults={'email': 'seed@example.com', 'role': 'customer'}
                )

            # Ensure at least one fish exists; create minimal sample if needed
            fish = Fish.objects.order_by('?').first()
            if not fish:
                cat, _ = Category.objects.get_or_create(name='Seed Category')
                breed, _ = Breed.objects.get_or_create(name='Seed Breed', category=cat)
                fish = Fish.objects.create(
                    name='Seed Fish',
                    category=cat,
                    breed=breed,
                    description='Placeholder fish for seeding orders',
                    price=100.00,
                    stock_quantity=100,
                )

            created_orders = []
            for i in range(30):
                # Random day in November: 1-30 (November has 30 days)
                day = random.randint(1, 30)
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                dt = datetime(year, month, day, hour, minute, second)
                aware_dt = timezone.make_aware(dt, timezone.get_current_timezone())

                qty = random.randint(max(1, (fish.minimum_order_quantity or 1)), (fish.minimum_order_quantity or 1) + 3)
                total = float(fish.price) * qty

                order = Order.objects.create(
                    user=user,
                    order_number=Order.generate_order_number(),
                    total_amount=total,
                    discount_amount=0,
                    final_amount=total,
                    status=random.choice([c[0] for c in Order.STATUS_CHOICES]),
                    payment_method=random.choice([c[0] for c in Order.PAYMENT_METHOD_CHOICES]),
                    payment_status=random.choice([c[0] for c in Order.PAYMENT_STATUS_CHOICES]),
                    shipping_address='Seed address, Seeder Street',
                    phone_number='0000000000',
                )

                # Add a single OrderItem
                OrderItem.objects.create(
                    order=order,
                    fish=fish,
                    quantity=qty,
                    price=fish.price,
                )

                # Set created_at/updated_at to the chosen aware datetime using update()
                Order.objects.filter(pk=order.pk).update(created_at=aware_dt, updated_at=aware_dt)

                created += 1
                created_orders.append((order.order_number, aware_dt))

        self.stdout.write(self.style.SUCCESS(f'Seeded {created} orders for November {year}.'))
        if created_orders:
            created_orders.sort(key=lambda x: x[1])
            first = created_orders[0]
            last = created_orders[-1]
            self.stdout.write(self.style.NOTICE(f'First order: {first[0]} at {first[1]}'))
            self.stdout.write(self.style.NOTICE(f'Last order: {last[0]} at {last[1]}'))
