"""
Django settings for dnfas project.

Generated by 'django-admin startproject' using Django 2.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
from celery.schedules import crontab

# Unique name of this server in a cluster of servers, case insensitive
WORKER_NAME = 'master'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPA_DIR = '/home/ronin/Projects/active/dnfas-ui/dist/'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '0x%&1gj_3hgzbo)$=ddjhr_x=xzc6rkrhub&g7r=%jpazk#kx+'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1'
]

INTERNAL_IPS = [
    '127.0.0.1'
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'dfapi',
    'users',
    'sysinf',
    'corsheaders',
    'drf_yasg'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dnfas.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [SPA_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dnfas.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Mexico_City'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.realpath(os.path.join(BASE_DIR, 'storage/static'))
STATICFILES_DIRS = [
  os.path.realpath(os.path.join(SPA_DIR, 'static')),
]
# Tell Django about the custom `User` model we created. The string
# `users.User` tells Django we are referring to the `User` model in
# the `users` app. This module is registered above in a setting
# called `INSTALLED_APPS`.
AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 120,
}

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.realpath(os.path.join(BASE_DIR, 'storage/media'))
DATA_ROOT = os.path.realpath(os.path.join(BASE_DIR, 'storage/data'))

VIDEO_RECORDS_PATH = 'video/'
VIDEO_THUMBS_PATH = 'video/thumbs'
FACES_IMAGES_PATH = 'faces/'
MODELS_DATA_PATH = 'models/'

VIDEO_THUMBS_COUNT = 5
VIDEO_THUMBS_SIZE = 256
VIDEO_SUPPORTED_EXT = ('mp4', 'avi', 'mkv')

DEFAULT_SEGMENT_TITLE = 'segment_f90fc1b8-4e84-4f69-85f4-105481605612'

SERVER_URL = 'http://localhost:8000'

# Celery settings
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Other Celery settings
CELERY_BEAT_SCHEDULE = {
    'update_hourly_stats': {
        'task': 'dfapi.tasks.update_hourly_stats',
        'schedule': crontab(minute=1)
    },
    'update_daily_stats': {
        'task': 'dfapi.tasks.update_daily_stats',
        'schedule': crontab(hour=1)
    },
    'clean_database': {
        'task': 'dfapi.tasks.clean_database',
        'schedule': crontab(hour=3)
    },
    'check_tasks': {
        'task': 'dfapi.tasks.check_tasks',
        'schedule': 60
    },
}

# Dnfal library
DNFAL_FORCE_CPU = False

DNFAL_MODELS_PATHS = {
    'detector': 'weights_detector.pth',
    'marker': 'weights_marker.npy',
    'encoder': 'weights_encoder.pth'
}

for key, filename in DNFAL_MODELS_PATHS.items():
    DNFAL_MODELS_PATHS[key] = os.path.join(
        DATA_ROOT, MODELS_DATA_PATH, filename
    )

# Logging
LOGGER_NAME = 'dnfas'
LOGGER_FILE = os.path.realpath(os.path.join(BASE_DIR, 'dnfas.log'))
LOGGER_FORMAT = '[{asctime}] {levelname} {module}:{lineno:d} "{message}"'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        }
    },
    'formatters': {
        'default': {
            'format': LOGGER_FORMAT,
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'formatter': 'default',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'default',
            'class': 'logging.handlers.RotatingFileHandler',
            'filters': ['require_debug_false'],
            'filename': LOGGER_FILE,
            'maxBytes': 100 * 1024,
            'backupCount': 10
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO'
        },
        LOGGER_NAME: {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
    }
}
