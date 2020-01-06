import logging
from datetime import datetime

from django.conf import settings
from django.db.models import Count
from django.utils.timezone import make_aware

from ..models import Task, Worker
from .exceptions import ServiceError
from .workers import RunnerManager, WorkerApi

logger_name = settings.LOGGER_NAME
logger = logging.getLogger(logger_name)

runner_manager = RunnerManager()
worker_api = WorkerApi()


def select_worker():
    active_status = (
        Task.STATUS_CREATED,
        Task.STATUS_RUNNING,
        Task.STATUS_PAUSED
    )
    queryset = Worker.objects.exclude(tasks__status__in=active_status)
    if len(queryset) > 0:
        return queryset[0]
    else:
        queryset = Worker.objects.filter(
            tasks__status__in=active_status
        ).annotate(
            tasks_count=Count('tasks')
        ).order_by('tasks_count')
        if len(queryset) > 0:
            worker = queryset[0]
            if worker.tasks_count < worker.max_load:
                return worker

    return None


def create(task: Task):
    datetime_now = make_aware(datetime.now())
    if task.schedule_start_at is None or (
        task.schedule_start_at is not None and
        datetime_now >= task.schedule_start_at
    ):
        start(task)


def start(task: Task):

    worker: Worker = select_worker()
    if worker is None:
        return

    task.worker = worker
    task.save(update_fields=['worker'])

    # if worker is None:
    #     raise ServiceError(f'Can not start task <{task.pk}> because its worker is undefined.')

    if worker.name.lower() == settings.WORKER_NAME.lower():
        runner_manager.create(task.pk)
    else:
        worker_api.execute(
            base_url=worker.api_url,
            resource=str(task.pk),
            action=WorkerApi.ACTION_START,
            username=worker.username,
            password=worker.password
        )


def pause(task: Task):
    worker: Worker = task.worker

    if worker is None:
        raise ServiceError(f'Can not pause task <{task.pk}> because its worker is undefined.')

    if worker.name.lower() == settings.WORKER_NAME.lower():
        runner_manager.pause(task.pk)
    else:
        worker_api.execute(
            base_url=worker.api_url,
            resource=str(task.pk),
            action=WorkerApi.ACTION_PAUSE,
            username=worker.username,
            password=worker.password
        )


def resume(task):
    worker: Worker = task.worker

    if worker is None:
        raise ServiceError(f'Can not resume task <{task.pk}> because its worker is undefined.')

    if worker.name.lower() == settings.WORKER_NAME.lower():
        runner_manager.resume(task.pk)
    else:
        worker_api.execute(
            base_url=worker.api_url,
            resource=str(task.pk),
            action=WorkerApi.ACTION_RESUME,
            username=worker.username,
            password=worker.password
        )


def stop(task):
    worker: Worker = task.worker

    if worker is None:
        raise ServiceError(f'Can not stop task <{task.pk}> because its worker is undefined.')

    if worker.name.lower() == settings.WORKER_NAME.lower():
        runner_manager.stop(task.pk)
    else:
        worker_api.execute(
            base_url=worker.api_url,
            resource=str(task.pk),
            action=WorkerApi.ACTION_STOP,
            username=worker.username,
            password=worker.password
        )
