from rest_framework import serializers
from ..models import Face, Frame, SubjectSegment

from dnfal.engine import EMBEDDINGS_LENGTH


import numpy as np
import base64
import binascii


class NpArrayField(serializers.Field):

    def __init__(self, **kwargs):
        self.dtype = kwargs.pop('dtype', np.float32)
        self.shape = kwargs.pop('shape', None)
        super().__init__(**kwargs)

    def to_representation(self, value):
        data = np.frombuffer(value, self.dtype)
        if self.shape is not None:
            data = data.reshape(self.shape)

        return data.tolist()

    def to_internal_value(self, data):
        if not isinstance(data, str):
            msg = f'Incorrect type. Expected a string, but got {type(data).__name__}.'
            raise serializers.ValidationError(msg)

        try:
            data_bytes = base64.b64decode(data, validate=True)
        except binascii.Error:
            msg = f'Incorrect type. Can not decode the data to base64.'
            raise serializers.ValidationError(msg)

        try:
            self.to_representation(data_bytes)
        except ValueError:
            msg = f'Incorrect type. Can not convert the data to numpy array.'
            raise serializers.ValidationError(msg)

        return data_bytes


class FramesSerializer(serializers.ModelSerializer):

    image = serializers.ImageField()
    timestamp = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = Frame
        fields = ('id', 'image', 'timestamp')
        read_only_fields = ('id',)


class FaceSerializer(serializers.ModelSerializer):

    image = serializers.ImageField(required=False, allow_null=True)
    frame = FramesSerializer(required=False, allow_null=True)

    box = serializers.ListSerializer(
        required=False,
        allow_null=True,
        child=serializers.FloatField(),
        read_only=True
    )

    box_bytes = NpArrayField(
        required=False,
        allow_null=True,
        dtype=np.float32,
        shape=(4,),
        write_only=True
    )

    landmarks_bytes = NpArrayField(
        required=False,
        allow_null=True,
        dtype=np.float32,
        shape=(-1, 2),
        write_only=True
    )

    embeddings_bytes = NpArrayField(
        required=False,
        allow_null=True,
        dtype=np.float32,
        write_only=True,
        shape=(-1, EMBEDDINGS_LENGTH)
    )

    class Meta:
        model = Face
        fields = (
            'id',
            'frame',
            'image',
            'box',
            'box_bytes',
            'landmarks_bytes',
            'embeddings_bytes',
            'subject',
            'created_at',
            'timestamp'
        )
        read_only_fields = (
            'id',
            'created_at',
            'task',
            'box'
        )

    # def create(self, validated_data):
    #     face = Face.objects.create(**validated_data)
    #     return face

    # def to_representation(self, instance):
    #     return {
    #         'id': instance.id,
    #         'image': instance.image.url,
    #         'subject': None if instance.subject is None else instance.subject.id,
    #         'landmarks': instance.landmarks
    #     }


class FacesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Face
        fields = ('id', 'frame', 'image', 'box', 'subject')
        read_only_fields = ('id', 'frame', 'image', 'box', 'subject')


class FrameSerializer(serializers.ModelSerializer):

    image = serializers.ImageField()
    timestamp = serializers.DateTimeField(required=False, allow_null=True)
    faces = FacesSerializer(many=True, read_only=True)

    class Meta:
        model = Frame
        fields = ('id', 'image', 'timestamp', 'faces')
        read_only_fields = ('id', 'faces')


# class RecognitionSerializer(serializers.Serializer):
#
#     similarity_threshold = serializers.FloatField(required=False, allow_null=True)
#     max_matches = serializers.IntegerField(required=False, allow_null=True)
#     segments = serializers.PrimaryKeyRelatedField(
#         queryset=SubjectSegment.objects.all(),
#         many=True,
#         required=False
#     )
