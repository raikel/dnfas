from rest_framework import serializers
from ..models import Stat


class StatSerializer(serializers.ModelSerializer):

    class Meta:
        model = Stat
        fields = '__all__'
        read_only_fields = (
            'id',
            'name',
            'timestamp',
            'updated_at',
            'value',
            'resolution'
        )