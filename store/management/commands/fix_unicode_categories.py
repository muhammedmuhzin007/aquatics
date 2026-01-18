from django.core.management.base import BaseCommand
from store.models import Category


class Command(BaseCommand):
    help = 'Fix Unicode encoding issues in Category fields'

    def handle(self, *args, **options):
        categories = Category.objects.all()
        fixed_count = 0
        errors = []

        for category in categories:
            try:
                # Try to encode and decode the fields to detect issues
                original_name = category.name
                original_description = category.description

                # Clean the name field
                if category.name:
                    try:
                        # Try to encode as UTF-8
                        category.name.encode('utf-8').decode('utf-8')
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        # If it fails, try to encode with latin-1 and decode as UTF-8
                        try:
                            category.name = category.name.encode('latin-1').decode('utf-8', errors='ignore')
                        except Exception as e:
                            category.name = category.name.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')

                # Clean the description field
                if category.description:
                    try:
                        category.description.encode('utf-8').decode('utf-8')
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        try:
                            category.description = category.description.encode('latin-1').decode('utf-8', errors='ignore')
                        except Exception as e:
                            category.description = category.description.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')

                # Check if any field changed
                if category.name != original_name or category.description != original_description:
                    category.save()
                    fixed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Fixed category: {original_name} (ID: {category.id})'
                        )
                    )

            except Exception as e:
                error_msg = f'Error processing category {category.id} ({category.name}): {str(e)}'
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(error_msg))

        self.stdout.write(
            self.style.SUCCESS(
                f'\nTotal categories fixed: {fixed_count}'
            )
        )

        if errors:
            self.stdout.write(
                self.style.WARNING(
                    f'\nTotal errors: {len(errors)}'
                )
            )
