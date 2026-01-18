"""
Database fix script to repair Unicode encoding issues in categories.
Run this in Django shell: python manage.py shell < fix_category_encoding.py
"""

from store.models import Category

def sanitize_string(value):
    """Remove invalid UTF-8 characters from string."""
    if not value:
        return value
    try:
        # Try to encode and decode to ensure valid UTF-8
        return value.encode('utf-8', errors='ignore').decode('utf-8')
    except Exception:
        return str(value).encode('utf-8', errors='ignore').decode('utf-8')

# Fix all categories
fixed_count = 0
errors = []

for category in Category.objects.all():
    try:
        original_name = category.name
        original_description = category.description
        
        # Sanitize the fields
        category.name = sanitize_string(category.name)
        category.description = sanitize_string(category.description)
        
        # Save if changes were made
        if category.name != original_name or category.description != original_description:
            # Use update to bypass model save method to avoid double sanitization
            Category.objects.filter(pk=category.pk).update(
                name=category.name,
                description=category.description
            )
            fixed_count += 1
            print(f"✓ Fixed category: {original_name} (ID: {category.id})")
    
    except Exception as e:
        error_msg = f"✗ Error processing category {category.id} ({category.name}): {str(e)}"
        errors.append(error_msg)
        print(error_msg)

print(f"\n✓ Total categories fixed: {fixed_count}")
if errors:
    print(f"✗ Total errors: {len(errors)}")
else:
    print("✓ All categories processed successfully!")
