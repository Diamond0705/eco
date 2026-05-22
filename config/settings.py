from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, "unsafe-local-dev-key"),
    ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost"]),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
REPORTLAB_FONT_PATH = env("REPORTLAB_FONT_PATH", default="")
ROUTE_PROVIDER = env("ROUTE_PROVIDER", default="mock")
CALCULATION_MODEL = env("CALCULATION_MODEL", default="v2.1")
MAX_ROUTE_DISTANCE_KM = env.int("MAX_ROUTE_DISTANCE_KM", default=2000)
GRAPHHOPPER_API_KEY = env("GRAPHHOPPER_API_KEY", default="")
GRAPHHOPPER_BASE_URL = env("GRAPHHOPPER_BASE_URL", default="https://graphhopper.com/api/1")
GRAPHHOPPER_PROFILE = env("GRAPHHOPPER_PROFILE", default="car")
GRAPHHOPPER_TIMEOUT_SECONDS = env.int("GRAPHHOPPER_TIMEOUT_SECONDS", default=10)
GRAPHHOPPER_FALLBACK_TO_MOCK = env.bool("GRAPHHOPPER_FALLBACK_TO_MOCK", default=True)
GRAPHHOPPER_ALTERNATIVE_MAX_PATHS = env.int(
    "GRAPHHOPPER_ALTERNATIVE_MAX_PATHS",
    default=5,
)
GRAPHHOPPER_ALTERNATIVE_MAX_WEIGHT_FACTOR = env.float(
    "GRAPHHOPPER_ALTERNATIVE_MAX_WEIGHT_FACTOR",
    default=1.6,
)
GRAPHHOPPER_ALTERNATIVE_MAX_SHARE_FACTOR = env.float(
    "GRAPHHOPPER_ALTERNATIVE_MAX_SHARE_FACTOR",
    default=0.7,
)
GRAPHHOPPER_TARGET_CANDIDATES = env.int("GRAPHHOPPER_TARGET_CANDIDATES", default=3)
GRAPHHOPPER_MAX_CANDIDATES = env.int("GRAPHHOPPER_MAX_CANDIDATES", default=5)
GRAPHHOPPER_ENABLE_STRATEGY_REQUESTS = env.bool(
    "GRAPHHOPPER_ENABLE_STRATEGY_REQUESTS",
    default=False,
)
GRAPHHOPPER_MAX_STRATEGY_REQUESTS = env.int(
    "GRAPHHOPPER_MAX_STRATEGY_REQUESTS",
    default=2,
)
GRAPHHOPPER_ENABLE_PATH_DETAILS = env.bool("GRAPHHOPPER_ENABLE_PATH_DETAILS", default=True)
GRAPHHOPPER_PATH_DETAILS = [
    detail.strip()
    for detail in env(
        "GRAPHHOPPER_PATH_DETAILS",
        default="road_class,road_environment,surface,max_speed,toll",
    ).split(",")
    if detail.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",
    "apps.accounts.apps.AccountsConfig",
    "apps.fleet.apps.FleetConfig",
    "apps.locations.apps.LocationsConfig",
    "apps.orders.apps.OrdersConfig",
    "apps.routing.apps.RoutingConfig",
    "apps.trips.apps.TripsConfig",
    "apps.reports.apps.ReportsConfig",
    "apps.dashboard.apps.DashboardConfig",
    "apps.core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://ecologist:ecologist@localhost:5432/ecologist",
    )
}

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

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

USE_S3_STORAGE = env.bool("USE_S3_STORAGE", default=False)
DOCUMENT_ARCHIVE_ENABLED = env.bool("DOCUMENT_ARCHIVE_ENABLED", default=True)
DOCUMENT_ARCHIVE_LOCATION = env("DOCUMENT_ARCHIVE_LOCATION", default="document_archive")
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="ecologist")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="ecologist-password")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="ecologist-documents")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="http://localhost:9000")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_ADDRESSING_STYLE = env("AWS_S3_ADDRESSING_STYLE", default="path")
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"
