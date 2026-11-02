from base.settings.common import *

STATIC_ROOT = "/opt/application/webapp/staticfiles"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "DEFAULT-CHARACTER-SET": "utf8",
        # "ENGINE": "dj_db_conn_pool.backends.mysql",
        "NAME": os.environ.get("MYSQL_DATABASE"),
        "USER": os.environ.get("MYSQL_USER"),
        "PASSWORD": os.environ.get("MYSQL_PASSWORD"),
        "HOST": os.environ.get("MYSQL_HOST"),
        "PORT": os.environ.get("MYSQL_PORT", 3306),
        "OPTIONS": {
            "sql_mode": "traditional",
        },
    }
}

# CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", False)
SECURE_SSL_HOST = os.environ.get("DJANGO_SECURE_SSL_HOST", None)
SECURE_REDIRECT_EXEMPT = os.environ.get("DJANGO_SECURE_REDIRECT_EXEMPT", "health,metrics").split(",")

# watchman
WATCHMAN_STORAGE_PATH = "/opt/application/webapp/tmp/"
