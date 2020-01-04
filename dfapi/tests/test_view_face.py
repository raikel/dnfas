import json
from multiprocessing import Process
from os import path
from time import sleep
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
from django import db

from ..models import (
    Face,
    Frame,
    Subject
)
from ..serializers import (
    FaceSerializer
)

FAKER = Faker()

CURR_DIR = path.abspath(path.dirname(__file__))
FACE_IMAGE_PATH = path.join(CURR_DIR, 'data/face.jpg')
FRAME_IMAGE_PATH = path.join(CURR_DIR, 'data/frame.jpg')


def filter_keys(data: dict, keys: list):
    data_filtered = {}
    for key in keys:
        if key in data.keys():
            data_filtered[key] = data[key]
    return  data_filtered


class ImageFactory:

    @staticmethod
    def create(file_path, media_path):
        image_name = f'face_{uuid4()}.jpg'
        rel_path = path.join(media_path, image_name)
        full_path = path.join(settings.MEDIA_ROOT, rel_path)
        image = cv.imread(file_path)
        cv.imwrite(full_path, image)
        return rel_path


class FrameFactory:

    @staticmethod
    def create():
        frame = Frame.objects.create(
            image=ImageFactory.create(
                FRAME_IMAGE_PATH,
                settings.FACES_IMAGES_PATH
            ),
            timestamp=timezone.now()
        )
        return frame


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


class FaceFactory:

    model = Face
    MODEL_REQUIRED_FIELDS = []
    API_REQUIRED_FIELDS = ['image']

    @staticmethod
    def create_instance(full: bool = True):
        data = FaceFactory.instance_data()
        if not full:
            data = filter_keys(data, FaceFactory.MODEL_REQUIRED_FIELDS)
        return Face.objects.create(**data)

    @staticmethod
    def instance_data():
        return dict(
            frame=FrameFactory.create(),
            image=ImageFactory.create(
                FACE_IMAGE_PATH,
                settings.FACES_IMAGES_PATH
            ),
            subject=SubjectFactory.create(),
            box=(0, 0, 1, 1),
            embeddings=np.random.uniform(0, 1, 512),
            landmarks=np.random.uniform(0, 1, 10),
            timestamp=timezone.now()
        )

    @staticmethod
    def api_post_data(full: bool = True):
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
            return filter_keys(data, FaceFactory.API_REQUIRED_FIELDS)

        return data


class _ViewTest(APITransactionTestCase):

    url_list = ''
    url_detail = ''
    serializer_class = None
    model_factory = None
    list_count = 5

    def setUp(self):
        self.invalid_data = {}

        self.valid_data = {
            'Full data': self.model_factory.api_post_data(),
            'Minimal data': self.model_factory.api_post_data(full=False)
        }

        # self.instances = [
        #     self.model_factory.create_instance()
        #     for n in range(self.list_count)
        # ]

    def get_all_instances(self):
        return self.model_factory.model.objects.all()


# noinspection PyUnresolvedReferences
class _MixinViewCreateTest():

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


# class _ViewTest(APITestCase):
#
#     url_list = ''
#     url_detail = ''
#
#     serializer_class = None
#
#     def setUp(self):
#         self.valid_data = {}
#         self.invalid_data = {}
#         self.instances = []
#
#     def get_all_instances(self):
#         return []
#
#     def test_create_valid(self):
#         for label, data in self.valid_data.items():
#             with self.subTest(msg=label):
#                 response = self.client.post(
#                     reverse(self.url_list),
#                     data=data
#                 )
#                 self.assertEqual(
#                     status.HTTP_201_CREATED,
#                     response.status_code,
#                     msg=repr(response.data)
#                 )
#
#     def test_create_invalid(self):
#         for label, data in self.invalid_data.items():
#             with self.subTest(msg=label):
#                 response = self.client.post(
#                     reverse(self.url_list),
#                     data=data
#                 )
#                 self.assertEqual(
#                     status.HTTP_400_BAD_REQUEST,
#                     response.status_code,
#                     msg=repr(response.data)
#                 )
#
#     def test_list_all(self):
#         response = self.client.get(reverse(self.url_list))
#         instances = self.get_all_instances()
#         serializer = self.serializer_class(instances, many=True)
#         self.assertEqual(response.data['results'], serializer.data)
#         self.assertEqual(
#             response.status_code,
#             status.HTTP_200_OK,
#             msg=repr(response.data)
#         )
#
#     def test_retrieve_valid(self):
#         instance = self.instances[0]
#         response = self.client.get(
#             reverse(self.url_detail, kwargs={'pk': instance.pk})
#         )
#         serializer = self.serializer_class(instance)
#         self.assertEqual(response.data, serializer.data)
#         self.assertEqual(
#             response.status_code,
#             status.HTTP_200_OK,
#             msg=repr(response.data)
#         )
#
#     def test_retrieve_invalid(self):
#         response = self.client.get(
#             reverse(self.url_detail, kwargs={'pk': -1})
#         )
#         self.assertEqual(
#             response.status_code,
#             status.HTTP_404_NOT_FOUND,
#             msg=repr(response.data)
#         )
#
#     def test_update_valid(self):
#         instance = self.instances[0]
#         for label, data in self.valid_data.items():
#             with self.subTest(msg=label):
#                 response = self.client.patch(
#                     reverse(self.url_detail, kwargs={'pk': instance.pk}),
#                     data=json.dumps(data),
#                     content_type='application/json'
#                 )
#                 self.assertEqual(
#                     status.HTTP_200_OK,
#                     response.status_code,
#                     msg=repr(response.data)
#                 )
#
#     def test_delete_valid(self):
#         instance = self.instances[0]
#         response = self.client.delete(
#             reverse(self.url_detail, kwargs={'pk': instance.pk})
#         )
#         self.assertEqual(
#             response.status_code,
#             status.HTTP_204_NO_CONTENT,
#             msg=repr(response.data)
#         )
#
#     def test_invalid_delete(self):
#         response = self.client.delete(
#             reverse(self.url_detail, kwargs={'pk': -1})
#         )
#         self.assertEqual(
#             response.status_code,
#             status.HTTP_404_NOT_FOUND,
#             msg=repr(response.data)
#         )

# from django.test import TestCase, TransactionTestCase
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


class FaceViewTest(_ViewTest,_MixinViewCreateTest):

    url_list = 'dfapi:faces-list'
    url_detail = 'dfapi:faces-detail'
    serializer_class = FaceSerializer
    model_factory = FaceFactory


del _ViewTest, _MixinViewCreateTest
