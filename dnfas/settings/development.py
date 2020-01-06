from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'dnfas_dev',
        'USER': 'dnfas_dev',
        'PASSWORD': '123',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# Django rest framework
REST_FRAMEWORK.update({
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.backends.JWTAuthentication',
    ),
    # 'DEFAULT_PERMISSION_CLASSES': [
    #     'rest_framework.permissions.IsAuthenticated',
    # ]
})

# Enable CORS for all domains
CORS_ORIGIN_ALLOW_ALL = True

# Logging
# LOGGING.update({
#     'loggers': {
#         'dfapi': {
#             'level': 'DEBUG',
#             'handlers': ['console'],
#         },
#     }
# })
