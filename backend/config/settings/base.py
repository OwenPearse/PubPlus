import importlib
import os
import sys
from pathlib import Path

from config.env import get_bool, get_env, get_list, load_dotenv, parse_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

load_dotenv(BASE_DIR / ".env")

# Django / runtime
DJANGO_ENV = get_env("DJANGO_ENV", default="local")
SECRET_KEY = get_env("DJANGO_SECRET_KEY", required=True)
DEBUG = get_bool("DJANGO_DEBUG", default=False)


def _build_allowed_hosts() -> list[str]:
    hosts = get_list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
    # Railway platform health probes use this Host header (not the public service domain).
    for required in ("healthcheck.railway.app",):
        if required not in hosts:
            hosts.append(required)
    for key in ("RAILWAY_PUBLIC_DOMAIN", "RAILWAY_PRIVATE_DOMAIN"):
        value = os.getenv(key, "").strip()
        if value and value not in hosts:
            hosts.append(value)
    return hosts


ALLOWED_HOSTS = _build_allowed_hosts()
CORS_ALLOWED_ORIGINS = get_list("DJANGO_CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = get_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.discovery.apps.DiscoveryConfig",
    "apps.venues.apps.VenuesConfig",
    "apps.saved.apps.SavedConfig",
    "apps.profile.apps.ProfileConfig",
    "apps.submissions.apps.SubmissionsConfig",
    "apps.internal_tools.apps.InternalToolsConfig",
    "apps.founder_venues.apps.FounderVenuesConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database — DATABASE_URL (if parseable) else discrete DB_* vars.
DATABASE_URL = get_env("DATABASE_URL", default="")


def _databases_from_db_vars() -> dict:
    db_host = get_env("DB_HOST", required=True)
    db_port = int(get_env("DB_PORT", default="5432"))
    db_name = get_env("DB_NAME", required=True)
    db_user = get_env("DB_USER", required=True)
    db_password = get_env("DB_PASSWORD", required=True)
    db_sslmode = get_env("DB_SSLMODE", default="")

    default_db: dict = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": db_name,
        "USER": db_user,
        "PASSWORD": db_password,
        "HOST": db_host,
        "PORT": db_port,
    }
    if db_sslmode:
        default_db["OPTIONS"] = {"sslmode": db_sslmode}
    return {"default": default_db}


if DATABASE_URL:
    try:
        DATABASES = {"default": parse_database_url(DATABASE_URL)}
    except (RuntimeError, ValueError):
        if get_env("DB_HOST"):
            DATABASES = _databases_from_db_vars()
        else:
            raise
else:
    DATABASES = _databases_from_db_vars()

# Supabase
SUPABASE_URL = get_env("SUPABASE_URL", required=True)
SUPABASE_ANON_KEY = get_env("SUPABASE_ANON_KEY", required=True)
SUPABASE_SERVICE_ROLE_KEY = get_env("SUPABASE_SERVICE_ROLE_KEY", default="")

# JWT / auth verification
SUPABASE_JWT_ISSUER = get_env("SUPABASE_JWT_ISSUER", required=True)
SUPABASE_JWT_AUDIENCE = get_env("SUPABASE_JWT_AUDIENCE", default="authenticated")
SUPABASE_JWT_JWKS_URL = get_env("SUPABASE_JWT_JWKS_URL", required=True)
SUPABASE_JWT_ALGORITHM = get_env("SUPABASE_JWT_ALGORITHM", default="RS256")

# Storage / media placeholders
SUPABASE_STORAGE_BUCKET_VENUES = get_env(
    "SUPABASE_STORAGE_BUCKET_VENUES", default="venues"
)
MEDIA_URL = get_env("MEDIA_URL", default="/media/")

# Internal / admin protection placeholders
INTERNAL_ADMIN_ENABLED = get_bool("INTERNAL_ADMIN_ENABLED", default=False)
INTERNAL_ADMIN_TOKEN = get_env("INTERNAL_ADMIN_TOKEN", default="")
INTERNAL_ADMIN_ALLOWED_IPS = get_list("INTERNAL_ADMIN_ALLOWED_IPS")
# Supabase JWT `sub` values allowed for /api/v1/internal/* (comma-separated UUIDs)
PUBPLUS_INTERNAL_ADMIN_SUBJECTS = get_list("PUBPLUS_INTERNAL_ADMIN_SUBJECTS")

LANGUAGE_CODE = "en-us"
TIME_ZONE = get_env("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Optional local overrides hook
LOCAL_SETTINGS_MODULE = get_env("LOCAL_SETTINGS_MODULE", default="")
if LOCAL_SETTINGS_MODULE:
    importlib.import_module(LOCAL_SETTINGS_MODULE)
