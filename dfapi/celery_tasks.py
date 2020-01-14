import logging
from datetime import timedelta, datetime, time

from celery import shared_task
from django.conf import settings

from dfapi.models import stat

from django.db.models import Count
from django.utils.timezone import make_aware

from .models import Face, Frame, Subject, Task, Recognition
from . import services


logger_name = settings.LOGGER_NAME
logger = logging.getLogger(logger_name)


@shared_task
def update_hourly_stats():
    services.stats.update_time_stats(stat.Stat.RESOLUTION_HOUR)


@shared_task
def update_daily_stats():
    services.stats.update_time_stats(stat.Stat.RESOLUTION_DAY)


@shared_task
def clean_database():
    delete_orphan_faces = True
    delete_frames_without_faces = True
    delete_unnamed_subjects = True
    delete_unnamed_subjects_days = 365
    delete_recognitions = True
    delete_recognitions_days = 7

    now = make_aware(datetime.now())

    if delete_orphan_faces:
        Face.objects.filter(subject__isnull=True).delete()

    if delete_frames_without_faces:
        Frame.objects.annotate(
            faces_count=Count('faces')
        ).filter(
            faces_count=0
        ).delete()

    if delete_unnamed_subjects:
        max_timestamp = now - timedelta(days=delete_unnamed_subjects_days)
        Subject.objects.filter(
            name='',
            last_name='',
            updated_at__lt=max_timestamp
        ).delete()

    if delete_recognitions:
        max_timestamp = now - timedelta(days=delete_recognitions_days)
        Recognition.objects.filter(
            created_at__lt=max_timestamp
        ).delete()


CHECK_TASKS_MAX_AGE_DAYS = 7
CREATED_TASK_TIMEOUT_DAYS = 1


@shared_task
def check_tasks():
    now = make_aware(datetime.now())
    min_timestamp = now - timedelta(days=CHECK_TASKS_MAX_AGE_DAYS)
    tasks = Task.objects.filter(
        updated_at__gt=min_timestamp,
        repeat=False
    )

    timeout_timestamp = now - timedelta(days=CREATED_TASK_TIMEOUT_DAYS)

    for task in tasks:
        if task.status in (Task.STATUS_CREATED, Task.STATUS_FAILURE):
            # If task is in status "CREATED" for more than a certain number
            # of days, delete it
            if (
                task.schedule_start_at is None and
                task.updated_at < timeout_timestamp
            ) or (
                task.schedule_start_at is not None and
                task.schedule_start_at < timeout_timestamp
            ) or (
                task.schedule_stop_at is not None and
                now > task.schedule_stop_at
            ):
                try:
                    services.tasks.stop(task)
                except services.ServiceError:
                    pass
                task.status = Task.STATUS_KILLED
                task.save(update_fields=['status'])
            elif (
                task.schedule_start_at is not None and
                now > task.schedule_start_at
            ) or task.schedule_start_at is None:
                try:
                    services.tasks.start(task)
                except services.ServiceError as err:
                    logger.error(err)

        elif task.status in (Task.STATUS_RUNNING, Task.STATUS_PAUSED):
            if (
                task.schedule_stop_at is not None and
                now > task.schedule_stop_at
            ):
                try:
                    services.tasks.stop(task)
                except services.ServiceError as err:
                    logger.error(err)

    weekday = str(now.weekday())
    tasks = Task.objects.exclude.filter(
        repeat=True,
        camera__isnull=False,
        repeat_days__icontains=weekday
    )
    time_max_stop = time(hour=23)
    time_now = now.time()

    for task in tasks:
        schedule_stop_at = time_max_stop
        if task.schedule_stop_at is not None:
            schedule_stop_at = task.schedule_stop_at.time()

        schedule_start_at = None
        if task.schedule_stop_at is not None:
            schedule_stop_at = task.schedule_stop_at.time()

        if task.status in (Task.STATUS_RUNNING, Task.STATUS_PAUSED):
            if time_now > schedule_stop_at:
                try:
                    services.tasks.stop(task)
                except services.ServiceError as err:
                    logger.error(err)
        else:
            if schedule_start_at is None or (
                schedule_start_at is not None and
                time_now > schedule_start_at
            ):
                try:
                    services.tasks.start(task)
                except services.ServiceError as err:
                    logger.error(err)
