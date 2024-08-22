import datetime
import os
import sys

import environ

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)
# reading .env file
environ.Env.read_env(env.str('../', '.env'))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = env('SECRET_KEY', default='NO_SECRET_KEY')

LOCALE_PATHS = (
    os.path.realpath('locale'),
)

# Set log level
ALLOWED_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
LOG_LEVEL = env('LOG_LEVEL', default='INFO')
if LOG_LEVEL not in ALLOWED_LOG_LEVELS:
    raise ValueError(f"Invalid LOG_LEVEL value. Allowed values are {ALLOWED_LOG_LEVELS}")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=False)
TESTING = sys.argv[1:2] == ['test']

EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = env('SENDGRID_KEY', default='xxx')

DOMAIN = env('DOMAIN', default='localhost:8000')
API_DOMAIN = env('API_DOMAIN', default='localhost:8000')

SITE_NAME = DOMAIN

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default='localhost,127.0.0.1')
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=["http://localhost", "http://127.0.0.1"])
SECURE_REFERRER_POLICY = "origin"

ADMINS = []

BUILT_IN_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.humanize'
]

LOCAL_APPS = [
    'mathefragen.apps.core',
    'mathefragen.apps.user',
    'mathefragen.apps.question',
    'mathefragen.apps.search',
    'mathefragen.apps.notifier',
    'mathefragen.apps.hashtag',
    'mathefragen.apps.vote',
    'mathefragen.apps.news',
    'mathefragen.apps.promotion',
    'mathefragen.apps.messaging',
    'mathefragen.apps.follow',
    'mathefragen.apps.guardian',
    'mathefragen.apps.feedback',
    'mathefragen.apps.stats',
    'mathefragen.apps.playlist',
    'mathefragen.apps.tips',
    'mathefragen.apps.tutoring',
    'mathefragen.apps.review',
    'mathefragen.apps.video',
    'mathefragen.apps.settings',
    'mathefragen.apps.aiedn',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'django_user_agents',
    'django_extensions',
    'storages',
    'compressor',
    'markdownify',
    'cloudinary',
    'adminsortable2',
    'drf_spectacular',
    'drf_spectacular_sidecar'
]

MARKDOWNIFY_BLEACH = False

FIREBASE_SERVER_KEY = env('FIREBASE_SERVER_KEY', default='xxx')

INSTALLED_APPS = BUILT_IN_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'mathefragen.apps.core.middlewares.CORSMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'mathefragen.apps.core.middlewares.AccountCheckMiddleware',
]

ROOT_URLCONF = 'mathefragen.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'mathefragen.apps.core.context_processors.project_settings'
            ],
        },
    },
]

WSGI_APPLICATION = 'mathefragen.wsgi.application'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": env("DB_NAME", default="mathefragen"),
        "USER": env("DB_USER", default="mathefragen"),
        "PASSWORD": env("DB_PWD", default="mathefragen"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432")
    }
}

INTERNAL_IPS = [
    # '127.0.0.1',
    '0.0.0.1'
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.AllowAllUsersModelBackend'
]

LOGIN_URL = '/user/login/'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'hashers_passlib.phpass',
]

DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000000
LOGOUT_REDIRECT_URL = "/"

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 50
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'AIEDN API',
    'DESCRIPTION': 'This is the place where AIEDN APIs live.',
    'VERSION': '1.0.0',

    'SWAGGER_UI_DIST': 'SIDECAR',  # shorthand to use the sidecar instead
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
}

LANGUAGE_CODE = 'de'

TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_L10N = True
USE_TZ = False

# 10 years
SESSION_COOKIE_AGE = 315569520
SESSION_COOKIE_NAME = env('COOKIE_NAME', default='session_dv')

# push server
ENABLE_WEBSOCKETS = env('ENABLE_WEBSOCKETS', default=False)
WEBSOCKET_GLOBAL_PUSH_DOMAIN = env('GLOBAL_WSS_URL', default='')
WEBSOCKET_USER_PUSH_DOMAIN_BASE = env('WEBSOCKET_USER_PUSH_DOMAIN_BASE', default='')
WEBSOCKET_USER_PUSH_DOMAIN = WEBSOCKET_USER_PUSH_DOMAIN_BASE + '%s'

WEBSOCKET_QUESTION_PUSH_DOMAIN_BASE = env('WEBSOCKET_QUESTION_PUSH_DOMAIN_BASE', default='')
WEBSOCKET_QUESTION_PUSH_DOMAIN = WEBSOCKET_QUESTION_PUSH_DOMAIN_BASE + '%s'

# AWS S3 Settings
AWS_HEADERS = {  # see http://developer.yahoo.com/performance/rules.html#expires
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'Cache-Control': 'max-age=94608000',
}
AWS_PRELOAD_METADATA = True
AWS_S3_HOST = 's3.eu-central-1.amazonaws.com'
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default='')
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='')
AWS_S3_CUSTOM_DOMAIN = AWS_STORAGE_BUCKET_NAME
AWS_DEFAULT_ACL = None

STATICFILES_LOCATION = 'static'

if DEBUG:
    STATIC_URL = '/site-static/'
else:
    # Production Setting. If set, css will be loaded from external CDN Storage
    STATICFILES_STORAGE = 'custom_storages.StaticStorage'
    STATIC_URL = "https://%s/%s/" % (AWS_STORAGE_BUCKET_NAME, STATICFILES_LOCATION)

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "site-static")
]
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

# AIEDN settings
AIEDN_API_TOKEN = env('AIEDN_API_TOKEN', default='')
AIEDN_API_URL = env('AIEDN_API_URL', default='')

# django compressor
COMPRESS_STORAGE = 'custom_storages.StaticStorage'
COMPRESS_OFFLINE_MANIFEST = 'manifest-1.json'
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_OUTPUT_DIR = env('COMPRESS_OUTPUT_DIR', default='cache')
COMPRESS_URL = STATIC_URL
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = True
AWS_QUERYSTRING_AUTH = False

MEDIAFILES_LOCATION = 'media'
MEDIA_URL = "https://%s/%s/" % (AWS_STORAGE_BUCKET_NAME, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = 'custom_storages.MediaStorage'

# youtube search API
YTB_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'

PORTALS_TO_SYNC = [
    'https://www.mathefragen.de',
    'https://www.bio-fragen.de',
    'https://www.informatikfragen.de',
    'https://www.chemie-fragen.de',
    'https://www.physik-fragen.de'
]

HOT_NETWORK_QUESTIONS_API = []

for portal in PORTALS_TO_SYNC:
    if DOMAIN not in portal:
        HOT_NETWORK_QUESTIONS_API.append('%s/v1/question/hot/' % portal)

JWT_AUTH = {
    'JWT_ENCODE_HANDLER':
        'rest_framework_jwt.utils.jwt_encode_handler',

    'JWT_DECODE_HANDLER':
        'rest_framework_jwt.utils.jwt_decode_handler',

    'JWT_PAYLOAD_HANDLER':
        'rest_framework_jwt.utils.jwt_payload_handler',

    'JWT_PAYLOAD_GET_USER_ID_HANDLER':
        'mathefragen.apps.core.authentication.custom_jwt_payload_get_user_id_handler',

    'JWT_PAYLOAD_GET_USERNAME_HANDLER':
        'mathefragen.apps.core.authentication.custom_jwt_payload_get_username_handler',

    'JWT_RESPONSE_PAYLOAD_HANDLER':
        'mathefragen.apps.core.authentication.custom_jwt_response_payload_handler',

    'JWT_SECRET_KEY': SECRET_KEY,
    'JWT_GET_USER_SECRET_KEY': None,
    'JWT_PUBLIC_KEY': None,
    'JWT_PRIVATE_KEY': None,
    'JWT_ALGORITHM': 'HS256',
    'JWT_VERIFY': True,
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LEEWAY': 0,
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=7),
    'JWT_AUDIENCE': None,
    'JWT_ISSUER': None,

    'JWT_ALLOW_REFRESH': True,
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=7),

    'JWT_AUTH_HEADER_PREFIX': 'JWT',
    'JWT_AUTH_COOKIE': None,

}

ADMINS_TO_REPORT = [
    'office@danieljung.io'
]

ADMIN_URL = '/7uzeudwe8iewfij/'

PAYPAL_CLIENT_ID = env('PAYPAL_CLIENT_ID', default='xxx')
PAYPAL_SECRET_ID = env('PAYPAL_SECRET_ID', default='xxx')

CLOUDINARY_URL = env('CLOUDINARY_URL', default='')

# share % for company for each tutoring transaction
TUTORING_COMPANY_SHARE = 10
TUTORING_ENABLED = env('TUTORING_ENABLED', default=False)

# Configure auto field (for Django 3.2)
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# production hooks
if not DEBUG:
    SESSION_ENGINE = 'redis_sessions.session'

    SESSION_REDIS = {
        'host': None,
        'port': None,
        'db': 0,
        'password': env('REDIS_PASSWORD', default=''),
        'prefix': 'session',
        'socket_timeout': 1,
        'retry_on_timeout': True
    }

    SESSION_REDIS_SENTINEL_LIST = [
        (
            env('REDIS_SENTINEL_1', default=''),
            env('REDIS_SENTINEL_1_PORT', default='')
        ),
        (
            env('REDIS_SENTINEL_2', default=''),
            env('REDIS_SENTINEL_2_PORT', default='')
        )
    ]

    SESSION_REDIS_SENTINEL_MASTER_ALIAS = 'mymaster'

    SESSION_COOKIE_DOMAIN = '%s' % DOMAIN.replace('www', '')
    SESSION_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    CSRF_COOKIE_SECURE = True
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    X_FRAME_OPTIONS = 'SAMEORIGIN'
    SECURE_SSL_REDIRECT = False  # False, because Cloudflare makes the SSL termination
    # SECURE_HSTS_SECONDS = 3600
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    COMPRESS_ENABLED = False  # True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'standard',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'mathefragen': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
    }
}
