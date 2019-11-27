from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Application definition
INSTALLED_APPS = INSTALLED_APPS + [
    'django_extensions',
]

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
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
