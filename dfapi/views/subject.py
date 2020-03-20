from django.conf import settings
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .mixins import (
    RetrieveMixin,
    ListMixin,
    CreateMixin,
    UpdateMixin,
    DestroyMixin
)
from .. import services
from ..models import Subject
from ..models import SubjectSegment
from ..serializers import (
    SubjectSerializer,
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

    def get_queryset(self):
        queryset, _ = services.subjects.build_queryset(
            self.queryset, self.request.query_params
        )
        return queryset


class DemograpView(
    ListMixin,
    viewsets.GenericViewSet
):
    """
    list:
        Return all subjects.
    """

    model_name = 'Subject'
    lookup_field = 'pk'
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

    def get_queryset(self):
        queryset = self.queryset.exclude(pred_sex__exact='')
        queryset = queryset.exclude(pred_age__isnull=True)

        queryset, _ = services.subjects.build_queryset(
            queryset, self.request.query_params
        )
        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        data = services.subjects.demograp(self.get_queryset())
        return Response(data, status=status.HTTP_200_OK)


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

