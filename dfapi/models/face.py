from django.db import models
from django.conf import settings
from django.utils import timezone
import numpy as np

# from os import path
#
# from ..services.faces import face_analyzer


class Frame(models.Model):
    image = models.ImageField(upload_to=settings.FACES_IMAGES_PATH)
    timestamp = models.DateTimeField(null=True, blank=True)
    size_bytes = models.IntegerField(blank=True, default=0)


class Face(models.Model):

    image = models.ImageField(upload_to=settings.FACES_IMAGES_PATH, null=True, blank=True)
    box_bytes = models.BinaryField(null=True, blank=True)
    landmarks_bytes = models.BinaryField(null=True, blank=True)
    embeddings_bytes = models.BinaryField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    size_bytes = models.IntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(null=True, blank=True, default=timezone.now)

    frame = models.ForeignKey(
        'Frame',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='faces'
    )

    subject = models.ForeignKey(
        'Subject',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='faces'
    )

    # def save(self, *args, **kwargs):
    #
    #     if self.size_bytes is None:
    #         self.size_bytes = self.image.size
    #
    #     if (
    #         self.embeddings_bytes is None or
    #         self.landmarks_bytes is None or
    #         self.box_bytes is None
    #     ):
    #         if path.isfile(self.image.path):
    #             face_analyzer.analyze_face(self.pk)
    #
    #     super().save(*args, **kwargs)

    @property
    def landmarks(self):
        if self.landmarks_bytes is not None:
            return np.frombuffer(self.landmarks_bytes, np.float32).reshape((-1, 2))
        return []

    @landmarks.setter
    def landmarks(self, val: [list, np.ndarray]):
        self.landmarks_bytes = np.array(val, np.float32).tobytes()

    @property
    def box(self):
        if self.box_bytes is not None:
            return np.frombuffer(self.box_bytes, np.float32)
        return []

    @box.setter
    def box(self, val: [list, tuple, np.ndarray]):
        self.box_bytes = np.array(val, np.float32).tobytes()

    @property
    def embeddings(self):
        if self.embeddings_bytes is not None:
            return np.frombuffer(self.embeddings_bytes, np.float32)
        return []

    @embeddings.setter
    def embeddings(self, val: [list, np.ndarray]):
        self.embeddings_bytes = np.array(val, np.float32).tobytes()

    def __str__(self):
        return f'{self.pk}'

    class Meta:
        ordering = ['-frame__timestamp']
