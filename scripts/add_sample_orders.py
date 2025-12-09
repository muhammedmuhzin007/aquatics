import random
from decimal import Decimal
from django.utils import timezone
from store.models import CustomUser, Order, OrderItem, Fish


def create_sample_orders(count=5):
    """Create sample orders with random fishes and statuses."""
    # Ensure sample customer exists
    customer, _ = CustomUser.objects.get_or_create(
        username="order_customer",
        defaults={"email": "customer@example.com", "role": "customer"},
    )

    fishes = list(Fish.objects.all())
    if not fishes:
        print("No fishes found; seed fishes first.")
        return

    statuses = [choice[0] for choice in Order.STATUS_CHOICES]
    payment_methods = [choice[0] for choice in Order.PAYMENT_METHOD_CHOICES]
    payment_statuses = [choice[0] for choice in Order.PAYMENT_STATUS_CHOICES]

    created = 0
    for i in range(count):
        # Generate order number
        order_number = Order.generate_order_number()

        # Pick 1-3 random fishes for the order
        num_items = random.randint(1, 3)
        selected_fishes = random.sample(fishes, min(num_items, len(fishes)))

        # Calculate total
        total_amount = Decimal("0")
        order_items_data = []
        for fish in selected_fishes:
            qty = random.randint(1, 5)
            price = fish.price
            order_items_data.append((fish, qty, price))
            total_amount += price * qty

        # Apply optional discount
        discount_amount = Decimal("0")
        if random.random() < 0.3:  # 30% chance of discount
            discount_amount = total_amount * Decimal("0.1")  # 10% off

        final_amount = total_amount - discount_amount

        # Create order
        order = Order.objects.create(
            user=customer,
            order_number=order_number,
            total_amount=total_amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            status=random.choice(statuses),
            payment_method=random.choice(payment_methods),
            payment_status=random.choice(payment_statuses),
            shipping_address="123 Main Street, Mumbai, MH 400001, India",
            phone_number="+91 98765 43210",
        )

        # Create order items
        for fish, qty, price in order_items_data:
            OrderItem.objects.create(order=order, fish=fish, quantity=qty, price=price)

        created += 1
        print(f"Created Order #{order.order_number}: {created} items, total ₹{order.final_amount}")

    print(f"Finished: created {created} orders.")


if __name__ == "__main__":
    create_sample_orders(5)
