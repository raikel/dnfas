from .development import *


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'dnfas_test',
        'USER': 'dnfas_test',
        'PASSWORD': 'dnfas_test',
        'HOST': 'localhost',
        'PORT': '',
        'TEST': {
            'NAME': 'dnfas_test'
        }
    }
}

# Dnfal library
DNFAL_FORCE_CPU = True
