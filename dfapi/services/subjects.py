from typing import Tuple

from django.db.models import QuerySet
from django.http import QueryDict

from ..models import Subject, SubjectSegment


def build_queryset(
    queryset: QuerySet,
    params: QueryDict
) -> Tuple[QuerySet, bool]:

    filtered = False

    name = params.get('name', None)
    if name is not None:
        queryset = queryset.filter(name__icontains=name)
        filtered = True

    last_name = params.get('last_name', None)
    if last_name is not None:
        queryset = queryset.filter(last_name__icontains=last_name)
        filtered = True

    naming = params.get('naming', None)
    if naming == SubjectSegment.NAMING_NAMED:
        queryset = queryset.exclude(
            name='', last_name=''
        )
        filtered = True
    elif naming == SubjectSegment.NAMING_UNNAMED:
        queryset = queryset.filter(
            name='', last_name=''
        )
        filtered = True

    tasks = params.getlist('tasks', None)
    cameras = params.getlist('cameras', None)
    videos = params.getlist('videos', None)
    if tasks is not None and len(tasks):
        queryset = queryset.filter(task__in=tasks)
        filtered = True
    elif cameras is not None and len(cameras):
        queryset = queryset.filter(task__camera__in=cameras)
        filtered = True
    elif videos is not None and len(videos):
        queryset = queryset.filter(task__video__in=videos)
        filtered = True

    min_timestamp = params.get('min_timestamp', None)
    if min_timestamp is not None:
        queryset = queryset.filter(created_at__gt=min_timestamp)
        filtered = True

    max_timestamp = params.get('max_timestamp', None)
    if max_timestamp is not None:
        queryset = queryset.filter(created_at__lt=max_timestamp)
        filtered = True

    max_age = params.get('max_age', None)
    if max_age is not None:
        try:
            max_age = int(max_age)
        except ValueError:
            pass
        else:
            queryset = queryset.filter(
                birthdate__gt=Subject.birthdate_from_age(max_age)
            )
            filtered = True

    min_age = params.get('min_age', None)
    if min_age is not None:
        try:
            min_age = int(min_age)
        except ValueError:
            pass
        else:
            queryset = queryset.filter(
                birthdate__lt=Subject.birthdate_from_age(min_age)
            )
            filtered = True

    sex = params.get('sex', None)
    if sex is not None:
        queryset = queryset.filter(sex=sex)
        filtered = True

    skin = params.get('skin', None)
    if skin is not None:
        queryset = queryset.filter(skin=skin)
        filtered = True

    order_by = params.get('order_by', None)
    if order_by is not None:
        queryset = queryset.order_by(order_by)

    if filtered:
        queryset = queryset.distinct()

    return queryset, filtered
