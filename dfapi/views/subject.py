from django.conf import settings
from rest_framework import viewsets

from .mixins import (
    RetrieveMixin,
    ListMixin,
    CreateMixin,
    UpdateMixin,
    DestroyMixin
)
from .. import services
from ..models import Subject, SubjectSegment
from ..serializers import (
    SubjectSerializer,
    SubjectEditSerializer,
    SubjectSegmentSerializer
)


class SubjectView(
    RetrieveMixin,
    ListMixin,
    CreateMixin,
    UpdateMixin,
    DestroyMixin,
    viewsets.GenericViewSet
):
    """
    retrieve:
        Return a subject instance.

    list:
        Return all subjects.

    create:
        Create a new subject.

    destroy:
        Remove an existing subject.

    partial_update:
        Update one or more fields on an existing subject.
    """

    model_name = 'Subject'
    lookup_field = 'pk'
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    create_serializer_class = SubjectEditSerializer
    update_serializer_class = SubjectEditSerializer

    def get_queryset(self):
        queryset, _ = services.subjects.build_queryset(
            self.queryset, self.request.query_params
        )
        return queryset


class SubjectSegmentView(
    RetrieveMixin,
    ListMixin,
    CreateMixin,
    UpdateMixin,
    DestroyMixin,
    viewsets.GenericViewSet
):
    """
    retrieve:
        Return a subject segment instance.

    list:
        Return all subject segments.

    create:
        Create a new subject segment.

    destroy:
        Remove an existing subject segment.

    partial_update:
    """

    model_name = 'SubjectSegment'
    lookup_field = 'pk'
    queryset = SubjectSegment.objects.exclude(
        title=settings.DEFAULT_SEGMENT_TITLE
    ).filter(disk_cached=True)

    serializer_class = SubjectSegmentSerializer
