import os
from datetime import timedelta
from os.path import join
from pathlib import Path

import yaml

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# print(BASE_DIR)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "3x*(qu!b9%w^)$(^o+v@y8svs3fmj(10z6mudssp0mibl4lr&3")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", False)

# allow all hosts during development
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1").split(",")

CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "http://127.0.0.1").split(",")

# Application definition

INSTALLED_APPS = [
    "simpleui",
    "django.contrib.admin",
    "corsheaders",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "drf_spectacular",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "watchman",
    "django_countries",
    "django_prometheus",
    "dj_rest_auth",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "django_filters",
    "dj_rest_auth.registration",
    "django_q",
    "apps.project_management",
    "apps.dashboard",
    "apps.qualification_test",
    "apps.planning",
    "apps.text_annotation",
    "apps.image_annotation",
    "apps.audio_annotation",
    "apps.notifications",
    "apps.profile",
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'middleware.auth.JWTAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

AUTH_SECRET_KEY = "Authservice-secret"

SIMPLE_JWT = {
    "SIGNING_KEY": AUTH_SECRET_KEY,
    "ALGORITHM": "HS256",
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=120),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    # 'USER_ID_FIELD': 'id',  # Assuming your Auth Service issues user IDs as 'id' in the token payload
    'USER_ID_CLAIM': 'user_id',  # This is crucial. If your Auth Service uses 'user_id', set it here.
    # 'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # must be before your middleware
    # "middleware.auth.AuthMiddleware",  # your JWT user setting middleware
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = "base.urls"

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",  # authservice URL
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "apps/website/templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "base.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# REST_AUTH_SERIALIZERS = {
#     'LOGIN_SERIALIZER': 'apps.user_management.serializers.profile.CustomLoginSerializer',
# }
#
# AUTHENTICATION_BACKENDS = [
#     'apps.user_management.backends.EmailOrUsernameBackend',  # Custom backend
#     'django.contrib.auth.backends.ModelBackend',  # Default backend (optional)
# ]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# LOGGER
with open(join(os.getcwd(), "logging.yml"), "r") as f:
    import logging.config

    logging.basicConfig(level=logging.INFO)
    logging.config.dictConfig(yaml.safe_load(f.read()))

# session expiration
SESSION_COOKIE_AGE = 60 * 60  # 1h
# Update the session validity deadline each request
SESSION_SAVE_EVERY_REQUEST = True
# Turn off the browser, then cookie failed
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Media
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Static
STATIC_URL = "/static/"
STATIC_ROOT = "staticfiles/"

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

FRONTEND_BASE_URL = "http://localhost:8000"

ASGI_APPLICATION = 'base.asgi.application'
# django allauth
SITE_ID = 1  # Required for django-allauth
REST_USE_JWT = True  # If you want to use JWT tokens for authentication


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'staff.crowdsourcing@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'fyom gkww tzpl zxcm')  # Must be set in environment

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Fallback to console backend for development if email not configured
if not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print("WARNING: Email credentials not configured. Using console backend for development.")

# AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://authgateway.local:8000/auth")

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-gateway-nginx:80/auth")
# AUTH_SERVICE_URL = "http://127.0.0.1:8000/auth"

JWT_SECRET = "Authservice-secret"  # Must match the one in AuthService

SPECTACULAR_SETTINGS = {
    'TITLE': 'Crowdsourcing API',
    'DESCRIPTION': 'API Documentation',
    'VERSION': '1.0.0',

    # ✅ Enables the Authorize button
    'SECURITY': [
        {'BearerAuth': []},
    ],

    'SECURITY_SCHEMES': {
        'BearerAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }
    },
}
Q_CLUSTER = {
    'name': 'crowdsourcing',
    'workers': 4,
    'recycle': 500,
    'timeout': 60,
    'django_redis': 'default',  # optional if you use redis
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
}
