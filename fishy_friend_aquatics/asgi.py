"""
ASGI config for Fishy Friend Aquatics project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fishy_friend_aquatics.settings')

application = get_asgi_application()
