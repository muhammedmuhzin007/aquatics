from store.models import ContactInfo


def create_contact_info():
    """Create or update contact information for FISHY FRIEND AQUA."""
    contact, created = ContactInfo.objects.get_or_create(
        id=1,
        defaults={
            'address_line1': 'FISHY FRIEND AQUA, 123 Ocean Avenue',
            'address_line2': 'Suite 5B, Bandra West',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'postal_code': '400050',
            'country': 'India',
            'phone_primary': '+91 98765 43210',
            'phone_secondary': '+91 99876 54321',
            'email_support': 'support@fishyfriendaqua.com',
            'email_sales': 'sales@fishyfriendaqua.com',
            'whatsapp': '+919876543210',
            'facebook_url': 'https://facebook.com/fishyfriendaqua',
            'instagram_url': 'https://instagram.com/fishyfriendaqua',
            'twitter_url': 'https://twitter.com/fishyfriendaqua',
            'youtube_url': 'https://youtube.com/@fishyfriendaqua',
            'map_embed_url': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3771.818099999999!2d72.82635!3d19.05!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3be7c8b6c6c6c6c7%3A0x0!2sBANDRA%20WEST%2C%20Mumbai!5e0!3m2!1sen!2sin!4v1234567890',
            'opening_hours': (
                'Monday - Friday: 9:00 AM - 6:00 PM\n'
                'Saturday: 10:00 AM - 5:00 PM\n'
                'Sunday: Closed\n'
                'Public Holidays: Closed'
            ),
        }
    )
    
    if created:
        print("Created new ContactInfo entry")
    else:
        print("ContactInfo already exists")
    
    return contact


if __name__ == '__main__':
    create_contact_info()
