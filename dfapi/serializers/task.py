from rest_framework import serializers
from ..models import Task, Subject
from .abstracts import MaskFieldsSerializer


class TaskSerializer(MaskFieldsSerializer):

    hunted_subjects = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = (
            'id',
            'started_at',
            'finished_at',
            'created_at',
            'updated_at',
            'worker'
        )
