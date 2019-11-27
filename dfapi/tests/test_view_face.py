from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from os import path
from django.core.files.uploadedfile import SimpleUploadedFile

PASSWORD = '123'
USERNAME = 'lame'
EMAIL = 'lameboy@gmail.com'


def create_user(username=USERNAME, password=PASSWORD, email=EMAIL):
    return get_user_model().objects.create_user(
        username=username, password=password, email=email
    )


curr_dir = path.abspath(path.dirname(__file__))
FACE_IMAGE_PATH = path.join(curr_dir, 'data/face.jpg')


class AuthenticationTest(APITestCase):

    def test_user_can_login(self):
        with open(FACE_IMAGE_PATH, 'rb') as image_file:
            image = SimpleUploadedFile(
                'face.jpg',
                image_file.read(),
                content_type="image/[jpg,png,gif]"
            )
            response = self.client.post(
                reverse('dfapi:faces'), data={'image': image}
            )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
