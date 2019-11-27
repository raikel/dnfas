from rest_framework import serializers
from .face import FaceSerializer
from .abstracts import FieldMaskingSerializer
from ..models import Subject, SubjectSegment, Camera, VideoRecord, Task, Face


class SubjectSerializer(FieldMaskingSerializer):

    faces = FaceSerializer(many=True, read_only=True)
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    last_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    birthdate = serializers.DateField(input_formats=['%m/%d/%Y'], required=False, allow_null=True)
    sex = serializers.CharField(required=False, allow_blank=True)
    skin = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Subject
        fields = (
            'id',
            'faces',
            'name',
            'last_name',
            'full_name',
            'age',
            'birthdate',
            'sex',
            'skin',
            'created_at',
            'updated_at',
            'task'
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
            'full_name',
            'age'
        )


class SubjectEditSerializer(SubjectSerializer):

    faces = serializers.PrimaryKeyRelatedField(
        queryset=Face.objects.all(),
        many=True,
        required=False
    )


class SubjectSegmentSerializer(FieldMaskingSerializer):

    title = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    naming = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    min_age = serializers.IntegerField(required=False, allow_null=True)
    max_age = serializers.IntegerField(required=False, allow_null=True)
    min_timestamp = serializers.DateField(required=False, allow_null=True)
    max_timestamp = serializers.DateField(required=False, allow_null=True)
    sex = serializers.CharField(required=False, allow_blank=True)
    skin = serializers.CharField(required=False, allow_blank=True)
    count = serializers.IntegerField(read_only=True)

    cameras = serializers.PrimaryKeyRelatedField(
        queryset=Camera.objects.all(),
        many=True,
        required=False
    )

    videos = serializers.PrimaryKeyRelatedField(
        queryset=VideoRecord.objects.all(),
        many=True,
        required=False
    )

    tasks = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = SubjectSegment
        fields = '__all__'
        read_only_fields = (
            'id',
            'count',
            'camera',
            'video'
        )