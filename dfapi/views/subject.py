from rest_framework import status, viewsets, mixins
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.conf import settings

from ..models import Subject, SubjectSegment
from ..serializers import SubjectSerializer, SubjectEditSerializer, SubjectSegmentSerializer
from .. import services


class SubjectView(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):

    lookup_field = 'pk'
    queryset = Subject.objects.all()
    # permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = SubjectSerializer
    serializers_class = {
        'create': SubjectEditSerializer,
        'update': SubjectEditSerializer,
        'partial_update': SubjectEditSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.serializers_class[self.action]
        except (KeyError, AttributeError):
            return super(SubjectView, self).get_serializer_class()

    def get_queryset(self):
        queryset, _ = services.subjects.build_queryset(
            self.queryset, self.request.query_params
        )
        return queryset

    def create(self, request):
        serializer_context = {'request': request}
        serializer = SubjectEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        serializer = self.serializer_class(
            serializer.instance,
            context=serializer_context
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        serializer_context = {'request': request}
        page = self.paginate_queryset(self.get_queryset())

        fields = request.query_params.get('fields', None)
        if fields is not None:
            fields = fields.split(',')

        serializer = self.serializer_class(
            page,
            context=serializer_context,
            many=True,
            fields=fields
        )
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, pk):
        serializer_context = {'request': request}

        try:
            subject = self.queryset.get(pk=pk)
        except Subject.DoesNotExist:
            raise NotFound('A subject with this pk does not exist.')

        serializer = self.serializer_class(
            subject,
            context=serializer_context
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        try:
            subject = Subject.objects.get(pk=pk)
        except Subject.DoesNotExist:
            raise NotFound(f'Subject with pk={pk} does not exist.')

        subject.delete()

        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def update(self, request, pk):
        serializer_context = {'request': request}

        try:
            subject = self.queryset.get(pk=pk)
        except Subject.DoesNotExist:
            raise NotFound('An subject with this pk does not exist.')

        serializer = SubjectEditSerializer(
            subject,
            context=serializer_context,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        serializer = self.serializer_class(
            serializer.instance,
            context=serializer_context
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        try:
            subject = Subject.objects.get(pk=pk)
        except Subject.DoesNotExist:
            raise NotFound(f'Subject with pk={pk} does not exist.')

        serializer_context = {'request': request}
        serializer = SubjectEditSerializer(
            subject,
            data=request.data,
            context=serializer_context,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        serializer = self.serializer_class(
            serializer.instance,
            context=serializer_context
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SubjectSegmentView(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):

    # permission_classes = (IsAuthenticated,)
    lookup_field = 'pk'
    queryset = SubjectSegment.objects.exclude(
        title=settings.DEFAULT_SEGMENT_TITLE
    ).filter(disk_cached=True)

    serializer_class = SubjectSegmentSerializer

    def create(self, request):
        serializer_context = {'request': request}
        serializer = self.serializer_class(
            data=request.data,
            context=serializer_context
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        serializer_context = {'request': request}
        page = self.paginate_queryset(self.get_queryset())

        serializer = self.serializer_class(
            page,
            context=serializer_context,
            many=True
        )
        return self.get_paginated_response(serializer.data)