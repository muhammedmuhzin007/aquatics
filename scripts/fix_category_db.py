"""
Direct database fix script for Unicode encoding issues in categories.
This script uses raw SQL to fix corrupted UTF-8 bytes in the database.

Run this in Django shell: python manage.py shell
Then: exec(open('scripts/fix_category_db.py').read())
"""

from django.db import connection
from store.models import Category

print("=" * 70)
print("CATEGORY UNICODE ERROR FIX")
print("=" * 70)

def sanitize_string(value):
    """Remove invalid UTF-8 characters from string."""
    if not value:
        return value
    try:
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore')
        return value.encode('utf-8', errors='ignore').decode('utf-8')
    except Exception:
        return str(value).encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')

# Step 1: Identify corrupted categories
print("\n[STEP 1] Scanning categories for encoding issues...")
categories = Category.objects.all()
corrupted_categories = []

for category in categories:
    try:
        # Try to encode to detect issues
        category.name.encode('utf-8')
        category.description.encode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        corrupted_categories.append(category)
        print(f"  Found corrupted category ID: {category.id}")

print(f"\nTotal corrupted categories found: {len(corrupted_categories)}")

if len(corrupted_categories) == 0:
    print("\n✓ No corrupted categories found!")
    print("✓ Database is clean.")
else:
    # Step 2: Fix corrupted categories
    print("\n[STEP 2] Fixing corrupted categories...")
    fixed_count = 0
    
    for category in corrupted_categories:
        try:
            original_name = str(category.name)
            original_desc = str(category.description)
            
            # Sanitize fields
            category.name = sanitize_string(category.name)
            category.description = sanitize_string(category.description)
            
            # Update database directly
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE store_category SET name = %s, description = %s WHERE id = %s",
                    [category.name, category.description, category.id]
                )
            
            fixed_count += 1
            print(f"  ✓ Fixed category ID {category.id}")
        
        except Exception as e:
            print(f"  ✗ Error fixing category ID {category.id}: {str(e)}")

print(f"\n[STEP 3] Summary")
print("=" * 70)
print(f"✓ Total categories fixed: {fixed_count}")
print(f"✓ Database cleanup complete!")
print("=" * 70)
