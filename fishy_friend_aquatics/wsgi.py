"""
WSGI config for Fishy Friend Aquatics project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fishy_friend_aquatics.settings')

application = get_wsgi_application()
