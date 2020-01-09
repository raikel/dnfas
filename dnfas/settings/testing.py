from .development import *
from os import path, mkdir


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

MEDIA_ROOT = path.realpath(path.join(BASE_DIR, 'storage/testing'))
DATA_ROOT = MEDIA_ROOT

MEDIA_PATHS = [
    VIDEO_RECORDS_PATH,
    VIDEO_THUMBS_PATH,
    FACES_IMAGES_PATH,
    MODELS_DATA_PATH
]

if not path.exists(MEDIA_ROOT):
    mkdir(MEDIA_ROOT)

for media_path in MEDIA_PATHS:
    full_path = path.join(MEDIA_ROOT, media_path)
    if not path.exists(full_path):
        mkdir(full_path)
