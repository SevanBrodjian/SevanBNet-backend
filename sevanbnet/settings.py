import os
import sys
from datetime import timedelta
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static
from django.urls import reverse_lazy

BASE_DIR = Path(__file__).resolve().parent.parent

# Railway injects RAILWAY_ENVIRONMENT_NAME ("production" / "development") into every
# deploy. Its presence is how we tell a real deployment from a laptop: deployments
# must be configured explicitly, while local runs get safe throwaway defaults.
RAILWAY_ENV = os.environ.get("RAILWAY_ENVIRONMENT_NAME")
ON_RAILWAY = RAILWAY_ENV is not None
TESTING = sys.argv[1:2] == ["test"]


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

# ── Hosts ────────────────────────────────────────────────────────────────────
# The control panel (/admin/, /accounts/) is served only on ADMIN_HOSTS; every other
# host gets the public API (/api/) and QR short links (/r/) and nothing else.
ADMIN_HOSTS = ["admin.sevanb.net", "dev-admin.sevanb.net"]
if not ON_RAILWAY:
    ADMIN_HOSTS += ["localhost", "127.0.0.1"]
PUBLIC_HOSTS = [
    "api.sevanb.net",
    "go.sevanb.net",
    "sevanbnet-backend-development.up.railway.app",
    "sevanbnet-backend-production.up.railway.app",
]
ALLOWED_HOSTS = [
    "admin.sevanb.net",
    "dev-admin.sevanb.net",
    *PUBLIC_HOSTS,
    "localhost",
    "127.0.0.1",
    "healthcheck.railway.app",
]
CSRF_TRUSTED_ORIGINS = ["https://admin.sevanb.net", "https://dev-admin.sevanb.net"]

CORS_ALLOWED_ORIGINS = [
    "https://www.sevanb.net",
    "https://sevanb.net",
    "https://dev.sevanb.net",
    "https://sevanbnet-frontend-development.up.railway.app",
    "https://sevanbnet-frontend-production.up.railway.app",
    "http://localhost:5173",
]
CORS_URLS_REGEX = r"^/api/.*$"

INSTALLED_APPS = [
    # First, so its templates override Unfold's and allauth's.
    "sevanbnet.apps.SevanBNetConfig",
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",  # allauth's passkey list uses it
    "allauth",
    "allauth.account",
    "allauth.mfa",
    "axes",
    "rest_framework",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "sevanbnet.middleware.noindex",
    "sevanbnet.middleware.admin_hosts",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "sevanbnet.middleware.require_passkey",
    # Last, as django-axes requires.
    "axes.middleware.AxesMiddleware",
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
                "sevanbnet.admin_site.sign_in_pages",
            ],
        },
    },
]

WSGI_APPLICATION = "sevanbnet.wsgi.application"

# ── Database ─────────────────────────────────────────────────────────────────
# On Railway the database must come from DATABASE_URL. Silently falling back to a
# SQLite file there would mean an empty, ephemeral database that vanishes on redeploy.
# Locally: DATABASE_URL if set (the sandbox, see docs/sandbox.md), else db.sqlite3.
# Tests always use a throwaway SQLite database.
LOCAL_SQLITE = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
DATABASES = {
    "default": dj_database_url.parse(
        LOCAL_SQLITE if TESTING and not ON_RAILWAY else env_required("DATABASE_URL", LOCAL_SQLITE),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
USING_SANDBOX = not ON_RAILWAY and DATABASES["default"]["ENGINE"].endswith("postgresql")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
# Sevan is in Pasadena; the admin shows times (and warns about offsets) in this zone.
TIME_ZONE = "America/Los_Angeles"
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
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
}

# ── Sign-in ──────────────────────────────────────────────────────────────────
# On Railway the admin signs in through allauth: password, then a passkey (or a passkey
# alone), with one-time backup codes for recovery. Locally the admin keeps Django's own
# password form. See docs/control-panel.md.
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/admin/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/accounts/login/"
ACCOUNT_ADAPTER = "sevanbnet.auth.AccountAdapter"
ACCOUNT_LOGIN_METHODS = {"username"}
ACCOUNT_SIGNUP_FIELDS = ["username*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
MFA_ADAPTER = "sevanbnet.auth.MFAAdapter"
MFA_FORMS = {"add_webauthn": "sevanbnet.auth.AddPasskeyForm"}
MFA_SUPPORTED_TYPES = ["webauthn", "recovery_codes"]
MFA_PASSKEY_LOGIN_ENABLED = True
MFA_TRUST_ENABLED = True
MFA_TRUST_COOKIE_AGE = timedelta(days=30)
MFA_RECOVERY_CODES_SHOW_ONCE = True
# Staff must register a passkey before using the panel (Railway only).
REQUIRE_PASSKEY = ON_RAILWAY
# Railway's edge proxy sets X-Real-IP to the visitor's address.
ALLAUTH_TRUSTED_CLIENT_IP_HEADER = "X-Real-IP" if ON_RAILWAY else None

# After 5 failed sign-ins from one address, or for one username from anywhere, password
# sign-in pauses for an hour (recorded in the database, so shared across workers).
# Signing in with a passkey alone still works during a pause.
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(hours=1)
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]
AXES_RESET_ON_SUCCESS = True
AXES_ENABLE_ADMIN = False
AXES_CLIENT_IP_CALLABLE = "sevanbnet.security.client_ip"
AXES_LOCKOUT_TEMPLATE = "lockout.html"

SESSION_COOKIE_AGE = 60 * 60 * 24 * 3

# ── Control panel ────────────────────────────────────────────────────────────
# Media uploads: committed to this public GitHub repo, served by jsDelivr.
MEDIA_REPO = os.environ.get("MEDIA_REPO", "")
MEDIA_BRANCH = os.environ.get("MEDIA_BRANCH", "main")
GITHUB_MEDIA_TOKEN = os.environ.get("GITHUB_MEDIA_TOKEN", "")
# "Rebuild site": redeploys this environment's frontend through Railway's API.
RAILWAY_DEPLOY_TOKEN = os.environ.get("RAILWAY_DEPLOY_TOKEN", "")
FRONTEND_SERVICE_ID = os.environ.get("FRONTEND_SERVICE_ID", "")
RAILWAY_ENVIRONMENT_ID = os.environ.get("RAILWAY_ENVIRONMENT_ID", "")

UNFOLD = {
    "SITE_TITLE": "sevanb.net",
    "SITE_HEADER": "sevanb.net",
    "SITE_SUBHEADER": "Control panel",
    "SITE_URL": SITE_URL,
    "SITE_SYMBOL": "tune",
    "STYLES": [lambda request: static("sevanbnet/panel.css")],
    "SITE_FAVICONS": [
        {"rel": "icon", "type": "image/png", "href": f"{SITE_URL}/favicon-32x32.png"}
    ],
    "ENVIRONMENT": "sevanbnet.admin_site.environment",
    "DASHBOARD_CALLBACK": "sevanbnet.admin_site.dashboard",
    "SHOW_VIEW_ON_SITE": True,
    "COLORS": {
        # A quiet slate blue.
        "primary": {
            "50": "oklch(97% .01 250)",
            "100": "oklch(93% .025 250)",
            "200": "oklch(87% .045 250)",
            "300": "oklch(78% .07 250)",
            "400": "oklch(68% .1 250)",
            "500": "oklch(59% .12 250)",
            "600": "oklch(52% .12 250)",
            "700": "oklch(45% .11 250)",
            "800": "oklch(38% .09 250)",
            "900": "oklch(32% .07 250)",
            "950": "oklch(24% .05 250)",
        },
    },
    "SITE_DROPDOWN": [
        {"icon": "open_in_new", "title": "Open the site", "link": SITE_URL},
        {"icon": "refresh", "title": "Rebuild site", "link": reverse_lazy("rebuild")},
        {
            "icon": "passkey",
            "title": "Passkeys and backup codes",
            "link": reverse_lazy("mfa_index"),
        },
    ],
    "ACCOUNT": {
        "navigation": [
            {"title": "Passkeys and backup codes", "link": reverse_lazy("mfa_index")},
        ],
    },
    "SIDEBAR": {
        "show_search": False,
        "show_all_applications": False,
        "navigation": [
            {
                "items": [
                    {
                        "title": "Site settings",
                        "icon": "tune",
                        "link": reverse_lazy("admin:sevanbnet_sitesettings_changelist"),
                    },
                    {
                        "title": "Projects",
                        "icon": "deployed_code",
                        "link": reverse_lazy("admin:sevanbnet_project_changelist"),
                    },
                    {
                        "title": "Papers",
                        "icon": "article",
                        "link": reverse_lazy("admin:sevanbnet_publication_changelist"),
                    },
                    {
                        "title": "Writing",
                        "icon": "edit_note",
                        "link": reverse_lazy("admin:sevanbnet_blogpost_changelist"),
                    },
                    {
                        "title": "Media",
                        "icon": "perm_media",
                        "link": reverse_lazy("admin:sevanbnet_media_changelist"),
                    },
                    {
                        "title": "QR codes",
                        "icon": "qr_code_2",
                        "link": reverse_lazy("qr_dashboard"),
                    },
                    {
                        "title": "Users",
                        "icon": "person",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                ],
            },
        ],
    },
}

# ── HTTPS and headers ────────────────────────────────────────────────────────
# Unfold opens related-object forms (the + beside a dropdown) in a same-origin frame.
X_FRAME_OPTIONS = "SAMEORIGIN"

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
