from os import path
from glob import iglob
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from dfapi.models.face import Face
from dfapi.models.subject import Subject

logger_name = settings.LOGGER_NAME
logger = logging.getLogger(logger_name)


IMAGES_PATH = '/home/ronin/Projects/datasets/faces/cplfw/'
IMAGE_EXTS = ('_1.jpg',)
NMAX_SUBJECTS = 10000000


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

            with open(file_path, 'rb') as img_file:

                filename = path.splitext(path.basename(file_path))[0]
                subject_name = ' '.join(filename.split('_')[0:-1])
                subject = Subject.objects.create(name=subject_name)
                subject.save()

                face = Face()
                face.subject = subject

                face.image.save(path.basename(file_path), img_file)
                face.save()

            print(f'Progress {(100 * index / files_count):.1f}%.')

        print(f'Image processing finished.')

    def handle(self, *args, **options):
        self._run()