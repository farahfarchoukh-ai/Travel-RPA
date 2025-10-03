from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

N8N_WEBHOOK_SECRET = os.environ.get('N8N_WEBHOOK_SECRET', 'test-secret')
