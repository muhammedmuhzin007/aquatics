"""Django settings for Fishy Friend Aquatics project (renamed from aquafish_store)."""
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-your-secret-key-here-change-in-production')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes', 'on')

ALLOWED_HOSTS = ['fishyfriendaqua.in', 'www.fishyfriendaqua.in','15.235.185.50']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'store',
]

SITE_NAME = 'FISHY FRIEND AQUA'

# Public site base URL used by background tasks to build absolute links when
# no HttpRequest object is available. Override in .env for production.

SITE_URL = os.getenv('SITE_URL', 'https://fishyfriendaqua.in')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'fishy_friend_aquatics.middleware.AjaxLoginRedirectMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fishy_friend_aquatics.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'fishy_friend_aquatics.context_processors.site_settings',
                'fishy_friend_aquatics.context_processors.global_flags',
            ],
            'libraries': {
                'currency': 'store.templatetags.currency',
            },
        },
    },
]

# Template caching in production
if not DEBUG:
    TEMPLATES[0]['OPTIONS']['loaders'] = [
        ('django.template.loaders.cached.Loader', [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ]),
    ]
    # Remove APP_DIRS when using custom loaders
    TEMPLATES[0]['APP_DIRS'] = False

WSGI_APPLICATION = 'fishy_friend_aquatics.wsgi.application'

# Production Security Settings
if not DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
    
    # Trust the reverse proxy (cPanel/Nginx)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True
    

DB_ENGINE = os.getenv('DB_ENGINE', 'mysql').lower()

if DB_ENGINE == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'fishyfr2_aquatics_data'),
            'USER': os.getenv('DB_USER', 'fishyfr2_jojimohan'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'CONN_MAX_AGE': 600,  # Database connection pooling (10 minutes)
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
    

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_ROOT = '/home/fishyfr2/public_html/static/'
MEDIA_ROOT = '/home/fishyfr2/public_html/media/'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'store.CustomUser'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

EMAIL_HOST_ENV = os.getenv('EMAIL_HOST')
EMAIL_HOST_USER_ENV = os.getenv('EMAIL_HOST_USER')

RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')
PAYMENT_PROVIDER = os.getenv('PAYMENT_PROVIDER', 'razorpay')


def _parse_bool_env(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.lower() in ("true", "1", "yes", "on")


ORDER_EMAILS_ASYNC = _parse_bool_env('ORDER_EMAILS_ASYNC', False)


# If SMTP settings are provided via environment variables, configure SMTP backend.
# Otherwise fall back to console backend for development.
if EMAIL_HOST_ENV and EMAIL_HOST_USER_ENV:
    EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    # Allow explicit toggles for TLS and SSL. SSL takes precedence if enabled.
    EMAIL_USE_TLS = _parse_bool_env("EMAIL_USE_TLS", True)
    EMAIL_USE_SSL = _parse_bool_env("EMAIL_USE_SSL", False)
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
    DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
    if DEBUG:
        proto = "smtps" if EMAIL_USE_SSL else ("smtp+tls" if EMAIL_USE_TLS else "smtp")
        print(f"[EMAIL CONFIG] Using SMTP backend: {EMAIL_BACKEND} host={EMAIL_HOST}:{EMAIL_PORT} proto={proto} user={EMAIL_HOST_USER}")
else:
    EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
    DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@fishyfriendaquatics.local")
    if DEBUG:
        print("[EMAIL CONFIG] Using console email backend. Configure SMTP via environment variables (.env) to enable SMTP.")

EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "30"))

# Whether to attach invoice PDFs to outgoing emails. When False, PDFs are still
# generated and saved under MEDIA_ROOT/invoices/ and a download link is included
# in the email body. Set to True only when your SMTP provider reliably supports
# large messages and attachments.
INVOICE_ATTACHMENTS = _parse_bool_env('INVOICE_ATTACHMENTS', False)

# Celery / Redis
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


# Basic logging configuration so email backend events and errors appear in console
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django.core.mail": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
        'TIMEOUT': 300,  # 5 minutes default
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    },
    'staticfiles': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'staticfiles-cache',
        'TIMEOUT': 86400,  # 24 hours
    }
}

# Session configuration for better performance
if not DEBUG:
    SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
    SESSION_CACHE_ALIAS = 'default'

# Static files optimization
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Data upload settings for better performance
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
