from os import path, mkdir, system
import shutil
from datetime import timedelta
from uuid import uuid4

import numpy as np
import cv2 as cv
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from faker import Faker
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITransactionTestCase

from ..models import (
    Face,
    Frame,
    Subject,
    VideoRecord
)

FAKER = Faker()

CURR_DIR = path.abspath(path.dirname(__file__))
FACE_IMAGE_PATH = path.join(CURR_DIR, 'data/face.jpg')
FRAME_IMAGE_PATH = path.join(CURR_DIR, 'data/frame.jpg')
VIDEO_PATH = path.join(CURR_DIR, 'data/video.mp4')


class ModelFactory:

    model_cls = None
    MODEL_REQUIRED_FIELDS = []
    API_REQUIRED_FIELDS = []
    API_READ_FIELDS = []

    def create_instance(self, full: bool = True):
        data = self.instance_data()
        if not full:
            data = filter_keys(data, self.MODEL_REQUIRED_FIELDS)
        return self.model_cls.objects.create(**data)

    def instance_data(self):
        return {}

    def api_post_data(self, full: bool = True):
        data = {}
        if not full:
            return filter_keys(data, self.API_REQUIRED_FIELDS)
        return data


def filter_keys(data: dict, keys: list):
    data_filtered = {}
    for key in keys:
        if key in data.keys():
            data_filtered[key] = data[key]
    return data_filtered


def create_video_file(file_path, media_path):
    _, ext = path.splitext(file_path)
    video_name = f'video_{uuid4()}{ext}'
    video_dir = path.join(settings.MEDIA_ROOT, media_path)
    if not path.exists(video_dir):
        mkdir(video_dir)
    shutil.copy2(file_path, path.join(video_dir, video_name))
    return video_name


def create_image_file(file_path, media_path):
    image_name = f'face_{uuid4()}.jpg'
    rel_path = path.join(media_path, image_name)
    full_path = path.join(settings.MEDIA_ROOT, rel_path)
    image = cv.imread(file_path)
    cv.imwrite(full_path, image)
    return rel_path


class FrameFactory(ModelFactory):

    model_cls = Frame
    MODEL_REQUIRED_FIELDS = ['image']
    API_REQUIRED_FIELDS = ['image']
    API_READ_FIELDS = [
        'id',
        'image',
        'timestamp',
        'faces'
    ]

    def instance_data(self):
        return dict(
            image=create_image_file(
                FRAME_IMAGE_PATH,
                settings.FACES_IMAGES_PATH
            ),
            timestamp=timezone.now()
        )

    def api_post_data(self, full: bool = True):
        with open(FRAME_IMAGE_PATH, 'rb') as image_file:
            image = SimpleUploadedFile(
                'frame.jpg',
                image_file.read(),
                content_type="image/[jpg,png,gif]"
            )
            data = {
                'image': image,
                'timestamp': timezone.now()
            }

        if not full:
            return filter_keys(data, self.API_REQUIRED_FIELDS)

        return data


class SubjectFactory:

    @staticmethod
    def create():
        return Subject.objects.create(
            unique_id=uuid4(),
            name=FAKER.first_name(),
            last_name=FAKER.last_name(),
            birthdate=FAKER.date_of_birth(),
            sex=Subject.SEX_MAN,
            skin=Subject.SKIN_WHITE,
            task=None
        )


class FaceFactory(ModelFactory):

    model_cls = Face
    MODEL_REQUIRED_FIELDS = []
    API_REQUIRED_FIELDS = ['image']
    API_READ_FIELDS = [
        'id',
        'image',
        'frame',
        'box',
        'subject',
        'created_at',
        'timestamp'
    ]

    def instance_data(self):
        frame_factory = FrameFactory()
        return dict(
            frame=frame_factory.create_instance(),
            image=create_image_file(
                FACE_IMAGE_PATH,
                settings.FACES_IMAGES_PATH
            ),
            subject=SubjectFactory.create(),
            box=(0, 0, 1, 1),
            embeddings=np.random.uniform(0, 1, 512),
            landmarks=np.random.uniform(0, 1, 10),
            timestamp=timezone.now()
        )

    def api_post_data(self, full: bool = True):
        with open(FACE_IMAGE_PATH, 'rb') as image_file:
            image = SimpleUploadedFile(
                'face.jpg',
                image_file.read(),
                content_type="image/[jpg,png,gif]"
            )
            data = {
                'image': image,
                'subject': SubjectFactory.create().pk
            }

        if not full:
            return filter_keys(data, self.API_REQUIRED_FIELDS)

        return data


class VideoFactory(ModelFactory):

    model_cls = VideoRecord
    MODEL_REQUIRED_FIELDS = ['path']
    API_REQUIRED_FIELDS = ['path']
    API_READ_FIELDS = [
        'id',
        'starts_at',
        'finish_at',
        'created_at',
        'updated_at',
        'frame_width',
        'frame_height',
        'duration_seconds',
        'size',
        'url',
        'thumbs',
        'running_tasks',
        'frames_count',
        'processing_time',
        'frame_rate',
        'faces_count',
        'last_task_at'
    ]

    def instance_data(self):
        return dict(
            path=create_video_file(VIDEO_PATH, settings.VIDEO_RECORDS_PATH),
            starts_at=timezone.now(),
            finish_at=timezone.now() + timedelta(seconds=60)
        )

    def api_post_data(self, full: bool = True):
        data = {
            'path': create_video_file(
                VIDEO_PATH,
                settings.VIDEO_RECORDS_PATH
            ),
            'starts_at': timezone.now(),
            'finish_at': timezone.now() + timedelta(seconds=60)
        }

        if not full:
            return filter_keys(data, self.API_REQUIRED_FIELDS)

        return data


class _ViewTest(APITransactionTestCase):

    url_list = ''
    url_detail = ''
    model_factory: ModelFactory = None
    list_count = 5

    def setUp(self):
        self.invalid_data = {}

        self.valid_data = {
            'Full data': self.model_factory.api_post_data(),
            'Minimal data': self.model_factory.api_post_data(full=False)
        }

        self.instances = [
            self.model_factory.create_instance()
            for n in range(self.list_count)
        ]

    def list_instances(self):
        return self.model_factory.model_cls.objects.all()


# noinspection PyUnresolvedReferences
class _MixinViewCreateTest:

    def test_create(self):
        for label, data in self.valid_data.items():
            with self.subTest(msg=label):
                response = self.client.post(
                    reverse(self.url_list),
                    data=data
                )
                self.assertEqual(
                    status.HTTP_201_CREATED,
                    response.status_code,
                    msg=repr(response.data)
                )


# noinspection PyUnresolvedReferences
class _MixinViewListTest:

    def test_list(self):
        response = self.client.get(reverse(self.url_list))
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=repr(response.data)
        )
        data = response.data['results']
        for index, item in enumerate(data):
            with self.subTest(msg=f'List index {index}'):
                self.assertSetEqual(
                    set(self.model_factory.API_READ_FIELDS),
                    set(item.keys())
                )


# noinspection PyUnresolvedReferences
class _MixinViewDeleteTest:

    def test_delete(self):
        for instance in self.instances:
            with self.subTest(msg=f'Model pk={instance.pk}'):
                response = self.client.delete(
                    reverse(self.url_detail, kwargs={'pk': instance.pk})
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_204_NO_CONTENT,
                    msg=repr(response.data)
                )


# noinspection PyUnresolvedReferences
class _MixinViewRetrieveTest:

    def test_retrieve(self):
        for instance in self.instances:
            with self.subTest(msg=f'Model pk={instance.pk}'):
                response = self.client.get(
                    reverse(self.url_detail, kwargs={'pk': instance.pk})
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                    msg=repr(response.data)
                )
                self.assertSetEqual(
                    set(self.model_factory.API_READ_FIELDS),
                    set(response.data.keys())
                )


# noinspection PyUnresolvedReferences
class _MixinViewUpdateTest:

    def test_update(self):
        instance = self.instances[0]
        for label, data in self.valid_data.items():
            with self.subTest(msg=label):
                response = self.client.patch(
                    reverse(self.url_detail, kwargs={'pk': instance.pk}),
                    data=data
                )
                self.assertEqual(
                    status.HTTP_200_OK,
                    response.status_code,
                    msg=repr(response.data)
                )
                self.assertSetEqual(
                    set(self.model_factory.API_READ_FIELDS),
                    set(response.data.keys())
                )


class FaceViewTest(
    _ViewTest,
    _MixinViewCreateTest,
    _MixinViewListTest,
    _MixinViewRetrieveTest,
    _MixinViewUpdateTest,
    _MixinViewDeleteTest
):

    url_list = 'dfapi:faces-list'
    url_detail = 'dfapi:faces-detail'
    model_factory = FaceFactory()


class FrameViewTest(
    _ViewTest,
    _MixinViewCreateTest,
    _MixinViewListTest,
    _MixinViewRetrieveTest,
    _MixinViewUpdateTest,
    _MixinViewDeleteTest
):

    url_list = 'dfapi:frames-list'
    url_detail = 'dfapi:frames-detail'
    url_detect_faces = 'dfapi:frames-detect-faces'
    model_factory = FrameFactory()

    def test_detect_faces(self):
        instance = self.instances[0]
        response = self.client.post(
            reverse(self.url_detect_faces, kwargs={'pk': instance.pk})
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=repr(response.data)
        )
        face_factory = FaceFactory()
        for index, item in enumerate(response.data):
            with self.subTest(msg=f'List index {index}'):
                self.assertSetEqual(
                    set(face_factory.API_READ_FIELDS),
                    set(item.keys())
                )


class VideoViewTest(
    _ViewTest,
    _MixinViewCreateTest,
    _MixinViewListTest,
    _MixinViewRetrieveTest,
    _MixinViewUpdateTest,
    _MixinViewDeleteTest
):

    url_list = 'dfapi:videos-list'
    url_detail = 'dfapi:videos-detail'
    model_factory = VideoFactory()
    list_count = 1


del (
    _ViewTest,
    _MixinViewCreateTest,
    _MixinViewListTest,
    _MixinViewRetrieveTest,
    _MixinViewUpdateTest,
    _MixinViewDeleteTest
)

# from django.test import TestCase, TransactionTestCase
# from multiprocessing import Process
# from time import sleep
# from django import db
#
# def execute_task():
#     print('Process started')
#     sleep(5)
#     print(Face.objects.all())
#
#
# class BugsTest(TransactionTestCase):
#
#     def test_multiprocessing(self):
#         face_1 = FaceFactory.create_instance()
#         print('Face 1 created')
#         db.connections.close_all()
#         process = Process(
#             target=execute_task
#         )
#         process.start()
#         face_2 = FaceFactory.create_instance()
#         print('Face 2 created')
#         sleep(10)
