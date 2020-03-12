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
import cv2 as cv

import numpy as np
import requests
import torch.multiprocessing as mp
from django import db
from django.conf import settings
from django.utils.timezone import make_aware
from dnfal import mtypes
from dnfal.settings import Settings
from dnfal.vision import FacesVision
from dnfal.engine import VideoAnalyzer
from requests import Response

from .exceptions import ServiceError
from .notifications import task_notificate
from ..models import (
    Subject,
    Face,
    Frame,
    HuntMatch,
    VideoRecord,
    Camera,
    VdfTaskConfig,
    VhfTaskConfig,
    PgaTaskConfig,
    Task
)

MAX_WORKERS = 4
MAX_EXECUTOR_THREADS = 8
MAX_TASKS_PER_WORKER = 8
PROGRESS_UPDATE_INTERVAL = 5
WORKER_WAIT_TIMEOUT = 60
WORKER_PUT_TIMEOUT = 10
WORKER_QUEUE_MAX_SIZE = 24

TEST_CONN_TIMEOUT = 1

TASK_FLAG_RUN = 0
TASK_FLAG_PAUSE = 1
TASK_FLAG_RESUME = 2
TASK_FLAG_STOP = 3
TASK_FLAG_KILL = 4

PAUSE_DURATION = 1

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


def update_face_detect(face: mtypes.Face, task_id: int):

    if face.subject is None:
        logger.error('Invalid operation. Face subject can not be empty.')
        return

    subject_id = face.subject.data.get('subject_id', None)
    if subject_id is None:
        subject_instance = Subject.objects.create(task_id=task_id)
        face.subject.data['subject_id'] = subject_instance.pk
    create_face(face, face.subject.data['subject_id'])


def update_face_hunt(face: mtypes.Face, task_id: int):

    if face.subject is None:
        logger.error('Invalid operation. Face subject can not be empty.')
        return

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
        'info',
        'progress'
    ]

    def __init__(self, task: Task, daemon: bool = True):
        super().__init__(daemon=daemon)

        self.task: Task = task
        self.status = task.status
        self.last_progress_update = 0
        self.executor = ThreadPoolExecutor(max_workers=MAX_EXECUTOR_THREADS)

    def run(self):
        try:
            self.task.status = Task.STATUS_RUNNING
            self.task.started_at = make_aware(datetime.now())
            self.send_progress()
            self.main_run()
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

    def pause(self):
        self.task.status = Task.STATUS_PAUSED
        self.send_progress()

    def resume(self):
        self.task.status = Task.STATUS_RUNNING
        self.send_progress()

    def stop(self):
        self.task.status = Task.STATUS_STOPPED
        self.send_progress()

    def kill(self):
        self.task.status = Task.STATUS_KILLED
        self.send_progress()

    def failed(self):
        self.task.status = Task.STATUS_FAILURE
        self.send_progress()

    def send_progress(self):
        if self.task.status != self.status:
            task_notificate(self.task.pk, self.status, self.task.status)
            self.status = self.task.status

        self.task.save(update_fields=self.TASK_UPDATE_FIELDS)
        # self.executor.submit(
        #     update_task,
        #     task=self.task,
        #     update_fields=self.TASK_UPDATE_FIELDS
        # )

    def main_run(self):
        pass


class VdfTaskRunner(TaskRunner):

    def __init__(self, task: Task, daemon: bool = True):
        super().__init__(task, daemon)

        task = self.task

        se = Settings()

        se.force_cpu = settings.DNFAL_FORCE_CPU
        se.detector_weights_path = settings.DNFAL_MODELS_PATHS['detector']
        se.marker_weights_path = settings.DNFAL_MODELS_PATHS['marker']
        se.encoder_weights_path = settings.DNFAL_MODELS_PATHS['encoder']

        task_config = VdfTaskConfig(**task.config)
        video_source_type = task_config.video_source_type

        if video_source_type == VdfTaskConfig.VIDEO_SOURCE_RECORD:
            video = VideoRecord.objects.get(pk=task_config.video_source_id)
            se.video_capture_source = video.full_path
            se.video_real_time = False
        elif video_source_type == VdfTaskConfig.VIDEO_SOURCE_CAMERA:
            camera = Camera.objects.get(pk=task_config.video_source_id)
            se.video_capture_source = camera.stream_url
            se.video_real_time = True

        se.video_mode = VideoAnalyzer.MODE_ALL
        se.video_start_at = task_config.start_at
        se.video_stop_at = task_config.stop_at
        se.detection_min_height = task_config.detection_min_height
        se.detection_min_score = task_config.detection_min_score
        se.similarity_thresh = task_config.similarity_thresh
        se.max_frame_size = task_config.max_frame_size
        se.video_detect_interval = task_config.video_detect_interval
        se.faces_time_memory = task_config.faces_time_memory
        se.store_face_frames = task_config.store_face_frames

        if task_config.frontal_faces:
            se.align_max_deviation = (0.4, 0.3)

        # noinspection PyTypeChecker
        self.faces_vision: FacesVision = None

        self.init_vision(se)

    def init_vision(self, vision_settings):
        self.faces_vision = FacesVision(vision_settings)

    def main_run(self):
        self.faces_vision.video_analyzer.run(
            frame_callback=self.on_frame,
            update_subject_callback=self.on_subject_updated
        )

    def on_subject_updated(self, face: Face):
        self.executor.submit(
            update_face_detect,
            face=face,
            task_id=self.task.pk
        )

    def on_frame(self):
        now = time()
        if (now - self.last_progress_update) > PROGRESS_UPDATE_INTERVAL:
            self.last_progress_update = now
            video_analyzer = self.faces_vision.video_analyzer
            info = self.task.info
            try:
                info['frames_count'] = video_analyzer.frames_count
                info['processing_time'] = video_analyzer.processing_time
                info['faces_count'] = video_analyzer.faces_count
                if video_analyzer.start_at > 0:
                    self.task.frame_rate = video_analyzer.frames_count / (
                        now - video_analyzer.start_at
                    )
            except Exception as err:
                logger.error(err)

            self.send_progress()

    def pause(self):
        self.faces_vision.video_analyzer.pause()
        super().pause()

    def resume(self):
        self.faces_vision.video_analyzer.pause()
        super().resume()

    def stop(self):
        self.faces_vision.video_analyzer.stop()
        super().stop()

    def kill(self):
        self.faces_vision.video_analyzer.stop()
        super().kill()

    def failed(self):
        self.faces_vision.video_analyzer.stop()
        super().failed()


class VhfTaskRunner(VdfTaskRunner):

    def __init__(self, task: Task, daemon: bool = True):
        super().__init__(task, daemon)

    def init_vision(self, vision_settings: Settings):
        task_config = VhfTaskConfig(**self.task.config)

        embeddings = []
        keys = []
        subjects = Subject.objects.filter(
            pk__in=task_config.hunted_subjects
        )

        for subject in subjects:
            hunt_match = HuntMatch.objects.create(
                target_subject=subject,
                task=self.task
            )
            for face in subject.faces.all():
                keys.append(hunt_match.pk)
                embeddings.append(face.embeddings)

        vision_settings.video_hunt_embeddings = np.array(embeddings)
        vision_settings.video_hunt_keys = keys

        super().init_vision(vision_settings)

    def on_subject_updated(self, face: Face):
        self.executor.submit(
            update_face_hunt,
            face=face,
            task_id=self.task.pk
        )


class PgaTaskRunner(TaskRunner):

    def __init__(self, task: Task, daemon: bool = True):
        super().__init__(task, daemon)

        task = self.task

        se = Settings()

        se.force_cpu = settings.DNFAL_FORCE_CPU
        se.genderage_weights_path = settings.DNFAL_MODELS_PATHS['genderage']
        se.face_align_size = 256

        self.task_config: PgaTaskConfig = PgaTaskConfig(**task.config)

        self.faces_vision: FacesVision = FacesVision(se)

        self._run: bool = False
        self._pause: bool = False

    def main_run(self):

        if self.task_config.overwrite:
            queryset = Face.objects.all()
        else:
            queryset = (
                Face.objects.filter(pred_sex__exact='') |
                Face.objects.filter(pred_age__isnull=True)
            )

        queryset = queryset.exclude(image__isnull=True)

        if self.task_config.min_created_at is not None:
            queryset = queryset.filter(
                created_at__gt=self.task_config.min_created_at
            )

        if self.task_config.max_created_at is not None:
            queryset = queryset.filter(
                created_at__lt=self.task_config.max_created_at
            )

        batch_size = 64
        faces_count = 0
        started_at = time()
        faces_batch = []
        total = queryset.count()

        self._run = True
        for face in queryset.iterator():
            if not self._run:
                break

            while self._pause:
                sleep(PAUSE_DURATION)

            faces_batch.append(face)
            faces_count += 1
            last_face = faces_count == total

            if len(faces_batch) == batch_size or last_face:
                self.predict_genderage(faces_batch)
                now = time()
                elapsed = now - self.last_progress_update
                if elapsed > PROGRESS_UPDATE_INTERVAL or last_face:
                    self.last_progress_update = now
                    self.task.progress = 100 * faces_count / total
                    info = self.task.info
                    info['faces_count'] = faces_count
                    info['processing_time'] = now - started_at
                    self.send_progress()

    def predict_genderage(self, faces: List[Face]):
        genderage_predictor = self.faces_vision.genderage_predictor
        face_aligner = self.faces_vision.face_aligner

        faces_images = []
        faces_inds = []
        for ind, face in enumerate(faces):
            face_image = face.image
            landmarks = face.landmarks
            if face_image is not None and len(landmarks):
                face_image = cv.imread(face_image.path)
                face_image_align, _ = face_aligner.align(face_image, landmarks)
                faces_images.append(face_image_align)
                faces_inds.append(ind)
                # color = (0, 255, 0)
                # for point in landmarks:
                #     point = (int(point[0]), int(point[1]))
                #     cv.circle(face_image, point, 2, color, -1)
                # cv.imshow('Face', face_image)
                # ret = cv.waitKey()
                # cv.imshow('Face aligned', face_image_align)
                # ret = cv.waitKey()

        n_images = len(faces_images)
        if n_images:
            genders, _, ages, _ = genderage_predictor.predict(faces_images)
            for ind in range(n_images):
                face = faces[faces_inds[ind]]
                if genders[ind] == genderage_predictor.GENDER_WOMAN:
                    face.pred_sex = Face.SEX_WOMAN
                elif genders[ind] == genderage_predictor.GENDER_MAN:
                    face.pred_sex = Face.SEX_MAN

                face.pred_age = int(ages[ind])

                face.save(update_fields=['pred_sex', 'pred_age'])

    def pause(self):
        self._pause = True
        super().pause()

    def resume(self):
        self._pause = False
        super().resume()

    def stop(self):
        self._run = False
        super().stop()

    def kill(self):
        self._run = False
        super().kill()

    def failed(self):
        self._run = False
        super().failed()


class WorkerMessage:

    START_TASK = 'start_task'
    STOP_TASK = 'stop_task'
    KILL_TASK = 'kill_task'
    PAUSE_TASK = 'pause_task'
    RESUME_TASK = 'resume_task'

    def __init__(self, message_data: dict):
        self.task_id: int = message_data['task_id']
        self.command: str = message_data['command']


def create_task_runner(task: Task) -> TaskRunner:
    if task.task_type == Task.TYPE_VIDEO_DETECT_FACES:
        return VdfTaskRunner(task)
    elif task.task_type == Task.TYPE_VIDEO_HUNT_FACES:
        return VhfTaskRunner(task)
    elif task.task_type == Task.TYPE_PREDICT_GENDERAGE:
        return PgaTaskRunner(task)
    else:
        raise ValueError(f'Invalid task type "{task.task_type}"')


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
                task = Task.objects.get(pk=task_id)
                task_runner = create_task_runner(task)
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
            raise ServiceError(
                f'Unable to start task <{task_id}>, worker queue timeout.'
            )

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
            raise ServiceError(
                f'Unable to stop task <{task_id}>, worker queue timeout.'
            )

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
            raise ServiceError(
                f'Unable to pause task <{task_id}>, worker queue timeout.'
            )

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
            raise ServiceError(
                f'Unable to resume task <{task_id}>, worker queue timeout.'
            )


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
                raise ServiceError(
                    f'Can not create a new task. All workers are full.'
                )
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

    def __init__(self, api_url: str):
        self.token = None
        self.api_url = api_url

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

    def _login(self, username: str, password: str):
        login_url = self.build_url(self.ACTION_LOGIN)
        response = self._make_request(
            login_url,
            data={
                'username': username,
                'password': password
            }
        )

        token = None
        if response is not None:
            try:
                response_data = response.json()
            except JSONDecodeError:
                pass
            else:
                if isinstance(response_data, dict):
                    token = response_data.get('token', None)

        if token is None:
            logger.warning(f'Unable to login at "{login_url}"')

        return token

    def execute(
        self,
        resource: [str, int],
        action: str,
        username: str,
        password: str
    ):
        if action not in self.ACTION_CHOICES:
            raise ValueError(f'Invalid action "{action}".')

        url = self.build_url(resource, action)

        if self.token is None and username and password:
            self.token = self._login(username=username, password=password)
            if self.token is None:
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

    def is_online(self):
        try:
            requests.head(
                self.api_url,
                timeout=TEST_CONN_TIMEOUT,
                allow_redirects=False
            )
        except:
            return False
        return True

    def build_url(self, *args):
        paths = [self.api_url] + [str(arg) for arg in args]
        return '/'.join(p.strip('/') for p in paths if p) + '/'
