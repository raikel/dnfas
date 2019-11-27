from .base import *

DEBUG = False

MIDDLEWARE.remove('corsheaders.middleware.CorsMiddleware')

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'dnfas',
        'USER': 'dnfas',
        'PASSWORD': '123',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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

# Django rest framework
REST_FRAMEWORK.update({
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.backends.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
})

# Enable CORS for specified domains:
CORS_ORIGIN_ALLOW_ALL = True
#
# CORS_ORIGIN_WHITELIST = (
#     'http://localhost',
# )

# Logging
# LOGGING.update({
#     'loggers': {
#         'dfapi': {
#             'level': 'INFO',
#             'handlers': ['file'],
#         },
#     }
# })
