from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    "api.reportmitra.in",
    ".reportmitra.in",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = [
    "https://api.reportmitra.in",
    "https://reportmitra.in",
    "https://www.reportmitra.in",
    "https://admin.reportmitra.in",
]

CORS_ALLOWED_ORIGINS = [
    "https://reportmitra.in",
    "https://www.reportmitra.in",
    "https://admin.reportmitra.in",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRFToken']

SECURE_CROSS_ORIGIN_OPENER_POLICY = None

SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SAMESITE = "None"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# RDS MySQL Database Configuration for Production
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.mysql"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
            "ssl": {"ca": os.getenv("DB_SSL_CA")}
            if os.getenv("DB_SSL_CA")
            else None,
        },
        "CONN_MAX_AGE": 600,  # Connection pooling for production
    }
}