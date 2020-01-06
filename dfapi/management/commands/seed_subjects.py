from os import path
from glob import iglob
import logging
from uuid import uuid4
import cv2 as cv

from django.conf import settings
from django.core.management.base import BaseCommand

from dfapi.models.face import Face
from dfapi.models.subject import Subject

logger_name = settings.LOGGER_NAME
logger = logging.getLogger(logger_name)


IMAGES_PATH = '/home/ronin/Projects/datasets/faces/cplfw/'
IMAGE_EXTS = ('_1.jpg',)
NMAX_SUBJECTS = 10


def create_image(file_path, media_path):
    image_name = f'face_{uuid4()}.jpg'
    rel_path = path.join(media_path, image_name)
    full_path = path.join(settings.MEDIA_ROOT, rel_path)
    image = cv.imread(file_path)
    cv.imwrite(full_path, image)
    return rel_path


class Command(BaseCommand):
    help = 'Insert subjects in the database'

    def _run(self):
        print(f'Listing images from {IMAGES_PATH}...')
        file_paths = []
        for ext in IMAGE_EXTS:
            path_ext = path.join(IMAGES_PATH, f'*{ext}')
            file_paths.extend(iglob(path_ext))

        files_count = len(file_paths)
        print(f'Found {files_count} images.')
        print(f'Starting processing images.')

        for index, file_path in enumerate(file_paths):

            if index >= NMAX_SUBJECTS:
                break

            filename = path.splitext(path.basename(file_path))[0]
            subject_name = ' '.join(filename.split('_')[0:-1])
            subject = Subject.objects.create(name=subject_name)
            subject.save()

            Face.objects.create(
                image=create_image(file_path, settings.FACES_IMAGES_PATH),
                subject=subject,
            )

            print(f'Progress {(100 * index / min(files_count, NMAX_SUBJECTS) ):.1f}%.')

        print(f'Image processing finished.')

    def handle(self, *args, **options):
        self._run()