import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Railway injects RAILWAY_ENVIRONMENT_NAME ("production" / "development") into every
# deploy. Its presence is how we tell a real deployment from a laptop: deployments
# must be configured explicitly, while local runs get safe throwaway defaults.
RAILWAY_ENV = os.environ.get("RAILWAY_ENVIRONMENT_NAME")
ON_RAILWAY = RAILWAY_ENV is not None


def env_required(name, local_default):
    value = os.environ.get(name)
    if value:
        return value
    if ON_RAILWAY:
        raise ImproperlyConfigured(f"{name} must be set on Railway")
    return local_default


SECRET_KEY = env_required("DJANGO_SECRET_KEY", "django-insecure-local-only")
DEBUG = os.environ.get("DJANGO_DEBUG", str(not ON_RAILWAY)) == "True"

# The public site. Root and "view on site" links on the backend point here.
SITE_URL = os.environ.get("SITE_URL", "https://www.sevanb.net")

# Base URL embedded in generated QR codes; production sets https://go.sevanb.net.
QR_BASE_URL = os.environ.get("QR_BASE_URL", "http://127.0.0.1:8000")

PUBLIC_HOSTS = [
    "api.sevanb.net",
    "go.sevanb.net",
    "sevanbnet-backend-development.up.railway.app",
    "sevanbnet-backend-production.up.railway.app",
]
ALLOWED_HOSTS = [*PUBLIC_HOSTS, "localhost", "127.0.0.1", "healthcheck.railway.app"]
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in PUBLIC_HOSTS]

CORS_ALLOWED_ORIGINS = [
    "https://www.sevanb.net",
    "https://sevanb.net",
    "https://dev.sevanb.net",
    "https://sevanbnet-frontend-development.up.railway.app",
    "https://sevanbnet-frontend-production.up.railway.app",
    "http://localhost:5173",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "sevanbnet.apps.SevanBNetConfig",
    "rest_framework",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "sevanbnet.middleware.noindex",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sevanbnet.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "sevanbnet.wsgi.application"

# On Railway the database must come from DATABASE_URL. Silently falling back to a
# SQLite file there would mean an empty, ephemeral database that vanishes on redeploy.
DATABASES = {
    "default": dj_database_url.parse(
        env_required("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Chicago"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # The hashed manifest only exists after collectstatic, which runs at deploy.
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if ON_RAILWAY
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

if ON_RAILWAY:
    # Railway terminates TLS at its edge and forwards plain HTTP with this header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SECURE_REDIRECT_EXEMPT = [r"^healthz/$"]
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
    },
}
