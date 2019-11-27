from django.core.management.base import BaseCommand
from dfapi.services.media import load_videos


class Command(BaseCommand):
    args = '<foo bar ...>'
    help = 'Read video files from disk and create corresponding "VideoRecord" objects in the database'

    def _run(self):
        load_videos(dir_path='')

    def handle(self, *args, **options):
        self._run()