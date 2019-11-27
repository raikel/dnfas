from django.core.management.base import BaseCommand
from dfapi.models import Face, Subject, Frame


class Command(BaseCommand):
    help = 'Insert subjects in the database'

    def _run(self):

        queryset = Subject.objects.all()
        print(f'Deleting {len(queryset)} subjects...')
        queryset.delete()
        print(f'All subjects deleted.')

        queryset = Face.objects.all()
        print(f'Deleting {len(queryset)} faces...')
        queryset.delete()
        print(f'All faces deleted.')

        queryset = Frame.objects.all()
        print(f'Deleting {len(queryset)} frames...')
        queryset.delete()
        print(f'All frames deleted.')

    def handle(self, *args, **options):
        self._run()