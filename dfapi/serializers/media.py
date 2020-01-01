from rest_framework import serializers
from rest_framework.serializers import ValidationError

from ..models import Camera, VideoRecord, VideoThumb
from .. import services
from .abstracts import MaskFieldsSerializer


class VideoThumbSerializer(serializers.ModelSerializer):

    class Meta:
        model = VideoThumb
        fields = ('id', 'image', 'video')
        read_only_fields = ('id', 'image', 'video')


def video_path_validator(value):
    message = services.media.is_valid_video_path(value)
    if message:
        raise ValidationError(message)


class VideoRecordSerializer(MaskFieldsSerializer):

    path = serializers.CharField(
        write_only=True,
        validators=[video_path_validator],
        help_text='The relative path of the video file.'
    )
    url = serializers.CharField(read_only=True)
    thumbs = VideoThumbSerializer(many=True, read_only=True)
    running_tasks = serializers.IntegerField(read_only=True)
    frames_count = serializers.IntegerField(read_only=True)
    processing_time = serializers.FloatField(read_only=True)
    frame_rate = serializers.FloatField(read_only=True)
    faces_count = serializers.FloatField(read_only=True)
    last_task_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = VideoRecord
        fields = (
            'id',
            'path',
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
        )
        read_only_fields = (
            'id',
            'url',
            'created_at',
            'updated_at',
            'running_tasks',
            'frames_count',
            'processing_time',
            'frame_rate',
            'faces_count',
            'last_task_at'
        )


class CameraSerializer(MaskFieldsSerializer):

    stream_url = serializers.CharField()
    name = serializers.CharField()
    location_lat = serializers.FloatField(required=False, allow_null=True)
    location_lon = serializers.FloatField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    running_tasks = serializers.IntegerField(read_only=True)
    frames_count = serializers.IntegerField(read_only=True)
    processing_time = serializers.FloatField(read_only=True)
    frame_rate = serializers.FloatField(read_only=True)
    faces_count = serializers.FloatField(read_only=True)
    last_task_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Camera
        fields = (
            'id',
            'created_at',
            'updated_at',
            'stream_url',
            'name',
            'location_lat',
            'location_lon',
            'address',
            'running_tasks',
            'frames_count',
            'processing_time',
            'frame_rate',
            'faces_count',
            'last_task_at'
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
            'running_tasks',
            'frames_count',
            'processing_time',
            'frame_rate',
            'faces_count',
            'last_task_at'
        )