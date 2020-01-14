from os import path

from django.db import models
from django.db.models import Sum, Avg
from django.utils.functional import cached_property
from django.conf import settings

from .task import Task


class MediaSource(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @cached_property
    def running_tasks(self):
        return self.tasks.filter(status=Task.STATUS_RUNNING).count()

    @cached_property
    def frames_count(self):
        result = self.tasks.aggregate(Sum('frames_count'))['frames_count__sum']
        return result if result is not None else 0

    @cached_property
    def processing_time(self):
        result = self.tasks.aggregate(Sum('processing_time'))['processing_time__sum']
        return result if result is not None else 0

    @cached_property
    def frame_rate(self):
        result = self.tasks.aggregate(Avg('frame_rate'))['frame_rate__avg']
        return result if result is not None else 0
        # processing_time = self.processing_time
        # if processing_time > 0:
        #     return self.frames_count / processing_time
        # return 0

    @cached_property
    def faces_count(self):
        result = self.tasks.aggregate(Sum('faces_count'))['faces_count__sum']
        return result if result is not None else 0

    @cached_property
    def last_task(self):
        try:
            return self.tasks.all().latest('finished_at')
        except Task.DoesNotExist:
            return None

    @cached_property
    def last_task_at(self):
        if self.last_task:
            return self.last_task.finished_at
        return None

    class Meta:
        abstract = True


class Camera(MediaSource):

    stream_url = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    location_lat = models.FloatField(null=True, blank=True)
    location_lon = models.FloatField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class VideoRecord(MediaSource):

    path = models.CharField(max_length=255, unique=True, db_index=True)
    starts_at = models.DateTimeField(blank=True, null=True)
    finish_at = models.DateTimeField(blank=True, null=True)
    frame_width = models.IntegerField(blank=True, null=True)
    frame_height = models.IntegerField(blank=True, null=True)
    size_bytes = models.IntegerField(blank=True, null=True)
    duration_seconds = models.FloatField(blank=True, null=True)

    @cached_property
    def size(self):
        if self.size_bytes is not None:
            size = float(self.size_bytes)
            for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024.0:
                    return "%3.1f %s" % (size, x)
                size /= 1024.0
        return ''

    @cached_property
    def url(self):
        return settings.SERVER_URL + settings.MEDIA_URL + settings.VIDEO_RECORDS_PATH + self.path

    @cached_property
    def full_path(self):
        return path.join(settings.MEDIA_ROOT, settings.VIDEO_RECORDS_PATH, str(self.path))

    def __str__(self):
        return path.basename(self.path)


class VideoThumb(models.Model):
    image = models.ImageField(upload_to=settings.VIDEO_THUMBS_PATH)

    video = models.ForeignKey(
        VideoRecord,
        null=False,
        blank=True,
        on_delete=models.CASCADE,
        related_name='thumbs'
    )