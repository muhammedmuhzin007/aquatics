from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand

from store.models import Accessory, ComboOffer, Fish, Plant


class Command(BaseCommand):
    help = "Populate missing weight values for fishes, combos, accessories, and plants."

    def handle(self, *args, **options):
        fish_updates = self._update_fish_weights()
        accessory_updates = self._update_accessory_weights()
        plant_updates = self._update_plant_weights()
        combo_updates = self._update_combo_weights()

        self.stdout.write(self.style.SUCCESS(
            "Weights populated. Fish: {} | Accessories: {} | Plants: {} | Combos: {}".format(
                fish_updates, accessory_updates, plant_updates, combo_updates
            )
        ))

    def _update_fish_weights(self):
        updated = 0
        for fish in Fish.objects.all():
            current_weight = fish.weight or Decimal("0")
            if current_weight > 0:
                continue

            size = fish.size or Decimal("3.0")
            if size <= 0:
                size = Decimal("3.0")

            weight = Decimal(size) * Decimal("0.04")
            weight = max(weight, Decimal("0.05"))
            weight = min(weight, Decimal("1.5"))
            weight = Decimal(weight).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

            fish.weight = weight
            fish.save(update_fields=["weight"])
            updated += 1
        return updated

    def _update_accessory_weights(self):
        updated = 0
        for accessory in Accessory.objects.all():
            current_weight = accessory.weight or Decimal("0")
            if current_weight > 0:
                continue

            price = accessory.price or Decimal("0")
            weight = Decimal("0.18")
            if price and price > 0:
                weight = Decimal("0.12") + (Decimal(price) / Decimal("6000"))

            weight = max(weight, Decimal("0.12"))
            weight = min(weight, Decimal("2.5"))
            weight = weight.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

            accessory.weight = weight
            accessory.save(update_fields=["weight"])
            updated += 1
        return updated

    def _update_plant_weights(self):
        updated = 0
        for plant in Plant.objects.all():
            current_weight = plant.weight or Decimal("0")
            if current_weight > 0:
                continue

            price = plant.price or Decimal("0")
            weight = Decimal("0.08")
            if price and price > 0:
                weight += Decimal(price) / Decimal("10000")

            weight = max(weight, Decimal("0.05"))
            weight = min(weight, Decimal("0.8"))
            weight = weight.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

            plant.weight = weight
            plant.save(update_fields=["weight"])
            updated += 1
        return updated

    def _update_combo_weights(self):
        updated = 0
        combos = ComboOffer.objects.all().prefetch_related("items__fish")
        for combo in combos:
            current_weight = combo.weight or Decimal("0")
            if current_weight > 0:
                continue

            bundle_weight = Decimal("0")
            for item in combo.items.all():
                fish_weight = item.fish.weight or Decimal("0")
                if fish_weight <= 0:
                    continue
                bundle_weight += Decimal(fish_weight) * Decimal(item.quantity or 0)

            if bundle_weight <= 0:
                bundle_weight = Decimal("0.75")

            weight = bundle_weight.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
            combo.weight = weight
            combo.save(update_fields=["weight"])
            updated += 1
        return updated
