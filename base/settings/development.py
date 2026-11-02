from base.settings.common import *

DEBUG = True

# allow all hosts during development
ALLOWED_HOSTS = ["*"]

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        # "ENGINE": "dj_db_conn_pool.backends.mysql",
        "NAME": os.getenv("DB_DATABASE", "crowdsourcing"),
        "USER": os.getenv("DB_USER", "root"),
        "PASSWORD": os.getenv("DB_PASSWORD", "12345"),
        "DEFAULT-CHARACTER-SET": "utf8",
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {
            "sql_mode": "traditional",
        },
    }
}
