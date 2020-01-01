from rest_framework import serializers
from .abstracts import MaskFieldsSerializer
from ..models import Recognition, RecognitionMatch, SubjectSegment
from .subject import SubjectSegmentSerializer, SubjectSerializer


class RecognitionMatchSerializer(serializers.ModelSerializer):

    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = RecognitionMatch
        fields = (
            'id',
            'score',
            'subject',
        )
        read_only_fields = (
            'id',
            'score',
            'subject'
        )


class RecognitionSerializer(MaskFieldsSerializer):
    matches = RecognitionMatchSerializer(
        many=True,
        read_only=True
    )

    segments = serializers.PrimaryKeyRelatedField(
        queryset=SubjectSegment.objects.all(),
        many=True,
        required=False
    )

    filter = SubjectSegmentSerializer(
        allow_null=True,
        required=False
    )

    class Meta:
        model = Recognition
        fields = (
            'id',
            'similarity_threshold',
            'max_matches',
            'created_at',
            'face',
            'segments',
            'filter',
            'matches'
        )
        read_only_fields = (
            'id',
            'created_at',
            'matches'
        )

    def create(self, validated_data):
        segment = None
        segment_data = validated_data.pop('filter')
        if len(segment_data):
            segment_serializer = SubjectSegmentSerializer(
                data=segment_data,
                context=self.context
            )
            segment_serializer.is_valid(raise_exception=True)
            segment = segment_serializer.save()

        if segment is not None:
            validated_data['filter_id'] = segment.pk
        return super().create(validated_data)
