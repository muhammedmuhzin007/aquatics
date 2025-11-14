"""
Fishy Friend Aquatics Django project package.
"""

# Ensure Celery app is loaded when Django starts (so `celery -A fishy_friend_aquatics worker` works)
try:
	from .celery import app as celery_app  # noqa: F401
except Exception:
	celery_app = None
