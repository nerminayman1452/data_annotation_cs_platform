from base.settings.common import *

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": join(BASE_DIR, "db.sqlite3"),
    }
}

######################### APPLICATION CONFIGURATION #########################

INSTALLED_APPS = INSTALLED_APPS

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
