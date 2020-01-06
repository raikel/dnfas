import datetime
import logging
import signal
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from json import JSONDecodeError
from os import path
from queue import Empty as QueueEmptyError
from queue import Full as QueueFullError
from threading import Thread
from time import time, sleep
from typing import Dict, List
from uuid import uuid4

import numpy as np
import requests
import torch.multiprocessing as mp
from django import db
from django.conf import settings
from django.utils.timezone import make_aware
from dnfal import mtypes
from dnfal.settings import Settings
from dnfal.vision import FacesVision
from requests import Response

from .exceptions import ServiceError
from .notifications import task_notificate
from ..models import Task, Subject, Face, Frame, HuntMatch

MAX_WORKERS = 4
MAX_EXECUTOR_THREADS = 8
MAX_TASKS_PER_WORKER = 8
PROGRESS_UPDATE_INTERVAL = 5
WORKER_WAIT_TIMEOUT = 60
WORKER_PUT_TIMEOUT = 10
WORKER_QUEUE_MAX_SIZE = 24

TASK_FLAG_RUN = 0
TASK_FLAG_PAUSE = 1
TASK_FLAG_RESUME = 2
TASK_FLAG_STOP = 3
TASK_FLAG_KILL = 4

logger_name = settings.LOGGER_NAME
logger = logging.getLogger(logger_name)


def create_frame(frame: mtypes.Frame):

    frame_name = f'frame_{uuid4()}.jpg'
    rel_path = path.join(settings.FACES_IMAGES_PATH, frame_name)
    full_path = path.join(settings.MEDIA_ROOT, rel_path)
    with open(full_path, 'wb') as f:
        f.write(frame.image_bytes)

    instance = Frame.objects.create(
        image=rel_path
    )

    frame.data['frame_id'] = instance.pk


def create_face(face: mtypes.Face, subject_id: int):

    frame_id = None
    if face.frame is not None:
        frame_id = face.frame.data.get('frame_id', None)
        if frame_id is None:
            create_frame(face.frame)
            frame_id = face.frame.data['frame_id']

    image_name = f'face_{uuid4()}.jpg'
    rel_path = path.join(settings.FACES_IMAGES_PATH, image_name)
    full_path = path.join(settings.MEDIA_ROOT, rel_path)
    with open(full_path, 'wb') as f:
        f.write(face.image_bytes)

    timestamp = make_aware(
        datetime.fromtimestamp(face.timestamp)
    )

    instance = Face.objects.create(
        subject_id=subject_id,
        frame_id=frame_id,
        image=rel_path,
        box=face.box,
        embeddings=face.embeddings,
        landmarks=face.landmarks,
        timestamp=timestamp
    )

    face.data['key'] = instance.pk


def update_face(face: mtypes.Face, task_id: int, mode: str):

    if face.subject is None:
        logger.error('Invalid operation. Face subject can not be empty.')
        return

    if mode == Task.MODE_HUNT:
        hunt_match_id = face.subject.data.get('hunt_key', None)
        try:
            hunt_match: HuntMatch = HuntMatch.objects.get(pk=hunt_match_id)
        except HuntMatch.DoesNotExist:
            logger.error(f'Hunt match <{hunt_match_id}> does not exist.')
            return
        subject_instance = hunt_match.matched_subject
        if subject_instance is None:
            subject_instance = Subject.objects.create(task_id=task_id)
            face.subject.data['subject_id'] = subject_instance.pk
            hunt_match.matched_subject = subject_instance
            hunt_match.save(update_fields=['matched_subject'])
        create_face(face, subject_instance.pk)
    elif mode == Task.MODE_ALL:
        subject_id = face.subject.data.get('subject_id', None)
        if subject_id is None:
            subject_instance = Subject.objects.create(task_id=task_id)
            face.subject.data['subject_id'] = subject_instance.pk
        create_face(face, face.subject.data['subject_id'])


def update_task(
    task: Task,
    update_fields: list
):
    try:
        task.save(update_fields=update_fields)
    except Exception as err:
        logger.exception(err)


class TaskRunner(Thread):

    TASK_UPDATE_FIELDS = [
        'status',
        'started_at',
        'finished_at',
        'frames_count',
        'processing_time',
        'faces_count',
        'frame_rate'
    ]

    def __init__(self, task_id: int, daemon: bool = True):
        super().__init__(daemon=daemon)

        task = Task.objects.get(pk=task_id)

        self.task: Task = task
        self.status = task.status
        self.last_progress_update = 0
        self.executor = ThreadPoolExecutor(max_workers=MAX_EXECUTOR_THREADS)

        se = Settings()

        se.force_cpu = settings.DNFAL_FORCE_CPU
        se.detector_weights_path = settings.DNFAL_MODELS_PATHS['detector']
        se.marker_weights_path = settings.DNFAL_MODELS_PATHS['marker']
        se.encoder_weights_path = settings.DNFAL_MODELS_PATHS['encoder']

        if task.camera is not None and task.video is not None:
            raise ValueError('A Task can not have set both the camera and the video fields.')
        if task.camera is not None:
            se.video_capture_source = task.camera.stream_url
            se.video_real_time = True
        elif task.video is not None:
            se.video_capture_source = task.video.full_path
            se.video_real_time = False
        else:
            raise ValueError('A Task must have at least the camera or the video field not null.')

        if task.schedule_start_at is not None:
            se.video_start_at = task.schedule_start_at.timestamp()

        if task.schedule_stop_at is not None:
            se.video_stop_at = task.schedule_stop_at.timestamp()

        if task.detection_min_height is not None:
            se.detection_min_height = task.detection_min_height

        if task.detection_min_score is not None:
            se.detection_min_score = task.detection_min_score

        if task.similarity_thresh is not None:
            se.similarity_thresh = task.similarity_thresh

        if task.max_frame_size is not None:
            se.max_frame_size = task.max_frame_size

        if task.frontal_faces is not None:
            se.align_max_deviation = (0.4, 0.3)

        if task.video_detect_interval is not None:
            se.video_detect_interval = task.video_detect_interval

        if task.faces_time_memory is not None:
            se.faces_time_memory = task.faces_time_memory

        if task.store_face_frames is not None:
            se.store_face_frames = task.store_face_frames

        if task.mode:
            se.video_mode = task.mode

        if task.mode == Task.MODE_HUNT:
            embeddings = []
            keys = []
            for subject in task.hunted_subjects.all():
                hunt_match = HuntMatch.objects.create(
                    target_subject=subject,
                    task=task
                )
                for face in subject.faces.all():
                    keys.append(hunt_match.pk)
                    embeddings.append(face.embeddings)

            se.video_hunt_embeddings = np.array(embeddings)
            se.video_hunt_keys = keys

        self.faces_vision = FacesVision(se)

    def run(self):
        try:
            self.task.status = Task.STATUS_RUNNING
            self.task.started_at = make_aware(datetime.now())
            self.send_progress()

            self.faces_vision.video_analyzer.run(
                frame_callback=self.on_frame,
                update_subject_callback=self.on_subject_updated
            )
            if self.task.status not in (Task.STATUS_KILLED, Task.STATUS_STOPPED):
                self.task.status = Task.STATUS_SUCCESS

            self.task.finished_at = make_aware(datetime.now())
            self.send_progress()
            self.executor.shutdown(wait=True)
        except Exception as err:
            logger.error(err)
            logger.debug(traceback.format_exc())
            self.failed()
            self.executor.shutdown(wait=True)

    def on_subject_updated(self, face: Face):
        self.executor.submit(
            update_face,
            face=face,
            task_id=self.task.pk,
            mode=self.task.mode
        )

    def on_frame(self):
        now = time()
        if (now - self.last_progress_update) > PROGRESS_UPDATE_INTERVAL:
            self.last_progress_update = now
            video_analyzer = self.faces_vision.video_analyzer
            try:
                self.task.frames_count = video_analyzer.frames_count
                self.task.processing_time = video_analyzer.processing_time
                self.task.faces_count = video_analyzer.faces_count
                if video_analyzer.start_at > 0:
                    self.task.frame_rate = video_analyzer.frames_count / (
                        now - video_analyzer.start_at
                    )
            except Exception as err:
                logger.error(err)

            self.send_progress()

    def pause(self):
        self.faces_vision.video_analyzer.pause()
        self.task.status = Task.STATUS_PAUSED
        self.send_progress()

    def resume(self):
        self.faces_vision.video_analyzer.pause()
        self.task.status = Task.STATUS_RUNNING
        self.send_progress()

    def stop(self):
        self.faces_vision.video_analyzer.stop()
        self.task.status = Task.STATUS_STOPPED
        self.send_progress()

    def kill(self):
        self.faces_vision.video_analyzer.stop()
        self.task.status = Task.STATUS_KILLED
        self.send_progress()

    def failed(self):
        self.faces_vision.video_analyzer.stop()
        self.task.status = Task.STATUS_FAILURE
        self.send_progress()

    def send_progress(self):
        if self.task.status != self.status:
            task_notificate(self.task.pk, self.status, self.task.status)
            self.status = self.task.status

        self.executor.submit(
            update_task,
            task=self.task,
            update_fields=self.TASK_UPDATE_FIELDS
        )


class WorkerMessage:

    START_TASK = 'start_task'
    STOP_TASK = 'stop_task'
    KILL_TASK = 'kill_task'
    PAUSE_TASK = 'pause_task'
    RESUME_TASK = 'resume_task'

    def __init__(self, message_data: dict):
        self.task_id: int = message_data['task_id']
        self.command: str = message_data['command']


def run_worker(recv_queue: mp.Queue):

    task_runners: Dict[int, TaskRunner] = {}

    def handle_signal(_signal_number, _stack_frame):
        for runner in task_runners.values():
            runner.kill()

    signal.signal(signal.SIGQUIT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    def check_tasks():
        for key in tuple(task_runners):
            runner = task_runners[key]
            if not runner.is_alive():
                del task_runners[key]

    while True:
        try:
            message_data: dict = recv_queue.get(timeout=WORKER_WAIT_TIMEOUT)
        except QueueEmptyError:
            check_tasks()
            if len(task_runners) == 0:
                sleep(WORKER_WAIT_TIMEOUT)
                break
        else:
            message = WorkerMessage(message_data)
            command = message.command
            task_id = message.task_id

            if command == WorkerMessage.START_TASK:
                check_tasks()
                task_runner = TaskRunner(task_id)
                task_runner.start()
                task_runners[task_id] = task_runner
            elif command == WorkerMessage.STOP_TASK:
                try:
                    task_runner = task_runners[task_id]
                except KeyError:
                    logger.error(f'Invalid task id <{task_id}>.')
                else:
                    task_runner.stop()
                    del task_runners[task_id]
            elif command == WorkerMessage.KILL_TASK:
                try:
                    task_runner = task_runners[task_id]
                except KeyError:
                    logger.error(f'Invalid task id <{task_id}>.')
                else:
                    task_runner.kill()
                    del task_runners[task_id]
            elif command == WorkerMessage.PAUSE_TASK:
                try:
                    task_runner = task_runners[task_id]
                except KeyError:
                    logger.error(f'Invalid task id <{task_id}>.')
                else:
                    task_runner.pause()
            elif command == WorkerMessage.RESUME_TASK:
                try:
                    task_runner = task_runners[task_id]
                except KeyError:
                    logger.error(f'Invalid task id <{task_id}>.')
                else:
                    task_runner.resume()
            else:
                logger.error(f'Invalid command "{command}".')


class Worker:

    def __init__(self):
        self.send_queue: mp.Queue = mp.Queue(
            maxsize=WORKER_QUEUE_MAX_SIZE
        )
        self.process: mp.Process = mp.Process(
            target=run_worker,
            kwargs={'recv_queue': self.send_queue}
        )
        self.task_ids: list = []

    def is_alive(self):
        return self.process.is_alive()

    def start(self):
        self.process.start()

    @property
    def task_count(self) -> int:
        task_ids = []
        for task_id in self.task_ids:
            try:
                task = Task.objects.get(pk=task_id)
            except Task.DoesNotExist:
                logger.error(f'Task <{task_id}> does not exists.')
            else:
                if task.status in (
                    Task.STATUS_CREATED,
                    Task.STATUS_RUNNING,
                    Task.STATUS_PAUSED
                ):
                    task_ids.append(task_id)

        self.task_ids = task_ids
        return len(self.task_ids)

    def start_task(self, task_id: int):
        try:
            self.send_queue.put({
                'task_id': task_id,
                'command': WorkerMessage.START_TASK
            }, timeout=WORKER_PUT_TIMEOUT)
            self.task_ids.append(task_id)
        except QueueFullError:
            raise ServiceError(f'Unable to start task <{task_id}>, worker queue timeout.')

    def stop_task(self, task_id: int):
        if task_id not in self.task_ids:
            logger.error(f'Invalid task <{task_id}>.')
            return
        try:
            self.send_queue.put({
                'task_id': task_id,
                'command': WorkerMessage.STOP_TASK
            }, timeout=WORKER_PUT_TIMEOUT)
            self.task_ids.remove(task_id)
        except QueueFullError:
            raise ServiceError(f'Unable to stop task <{task_id}>, worker queue timeout.')

    def pause_task(self, task_id: int):
        if task_id not in self.task_ids:
            logger.error(f'Invalid task <{task_id}>')
            return
        try:
            self.send_queue.put({
                'task_id': task_id,
                'command': WorkerMessage.PAUSE_TASK
            }, timeout=WORKER_PUT_TIMEOUT)
        except QueueFullError:
            raise ServiceError(f'Unable to pause task <{task_id}>, worker queue timeout.')

    def resume_task(self, task_id: int):
        if task_id not in self.task_ids:
            logger.error(f'Invalid task <{task_id}>')
            return
        try:
            self.send_queue.put({
                'task_id': task_id,
                'command': WorkerMessage.RESUME_TASK
            }, timeout=WORKER_PUT_TIMEOUT)
        except QueueFullError:
            raise ServiceError(f'Unable to resume task <{task_id}>, worker queue timeout.')


class RunnerManager:
    def __init__(self):
        self.workers: List[Worker] = []
        self.tasks_worker: Dict[int, Worker] = {}
        self._id_count = 0

    def create(self, task_id: int):

        if task_id in self.tasks_worker:
            raise ServiceError(f'Task <{task_id}> is already running.')

        self.workers = [
            worker for worker in self.workers
            if worker.is_alive()
        ]

        if len(self.workers) < MAX_WORKERS:
            worker = Worker()
            db.connections.close_all()
            worker.start()
            self.workers.append(worker)
        else:
            task_count = [
                worker.task_count for worker in self.workers
            ]
            worker_ind = int(np.argmin(task_count))
            if task_count[worker_ind] >= MAX_TASKS_PER_WORKER:
                raise ServiceError(f'Can not create a new task. All workers are full.')
            worker = self.workers[worker_ind]

        worker.start_task(task_id)
        self.tasks_worker[task_id] = worker

    def pause(self, task_id: int):
        task_id = self.validate_task(task_id)
        self.tasks_worker[task_id].pause_task(task_id)

    def resume(self, task_id: int):
        task_id = self.validate_task(task_id)
        self.tasks_worker[task_id].resume_task(task_id)

    def stop(self, task_id: int):
        task_id = self.validate_task(task_id)
        self.tasks_worker[task_id].stop_task(task_id)
        del self.tasks_worker[task_id]

    def validate_task(self, task_id) -> int:
        try:
            task_id = int(task_id)
            if task_id not in self.tasks_worker:
                raise ValueError
            return task_id
        except ValueError:
            raise ServiceError(f'Invalid task <{task_id}>.')


class WorkerApi:
    ACTION_START = 'start/'
    ACTION_PAUSE = 'pause/'
    ACTION_RESUME = 'resume/'
    ACTION_STOP = 'stop/'
    ACTION_LOGIN = 'login/'

    ACTION_CHOICES = [
        ACTION_START,
        ACTION_PAUSE,
        ACTION_RESUME,
        ACTION_STOP,
        ACTION_LOGIN
    ]

    def __init__(self):
        self.token = None

    def _make_request(
        self,
        url: str,
        data: dict = None,
        headers: dict = None
    ):
        try:
            response = requests.post(
                url,
                data=data,
                headers=headers
            )
            if not response:
                logger.error(f'Http request error {response.status_code}.')
                self.handle_error(response)
            return response
        except requests.RequestException as err:
            logger.error(err)
            return None

    def _login(self, url: str, username: str, password: str):

        response = self._make_request(
            url,
            data={
                'username': username,
                'password': password
            }
        )

        if response is not None:
            try:
                response_data = response.json()
            except JSONDecodeError:
                return None
            else:
                if isinstance(response_data, dict):
                    return response_data.get('token', None)
                return None

    def execute(
        self,
        base_url: str,
        resource: str,
        action: str,
        username: str,
        password: str
    ):
        if action not in self.ACTION_CHOICES:
            raise ValueError(f'Invalid action "{action}".')

        url = path.join(base_url, resource, action)

        if self.token is None and username and password:
            login_url = path.join(base_url, self.ACTION_LOGIN)
            self.token = self._login(
                url=login_url,
                username=username,
                password=password
            )

            if self.token is None:
                logger.warning(f'Unable to login at "{login_url}"')
                return

        headers = None
        if self.token is not None:
            headers = {
                'Authorization': f'Token {self.token}'
            }

        self._make_request(url, headers=headers)

    @staticmethod
    def handle_error(response: Response):
        try:
            response_data = response.json()
        except JSONDecodeError:
            return

        if isinstance(response_data, list):
            for msg in response_data:
                logger.error(msg)
        elif isinstance(response_data, dict):
            for msg_key in response_data:
                logger.error(f'{msg_key}: {response_data[msg_key]}')