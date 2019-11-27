from rest_framework import status, viewsets, mixins
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from ..models import Camera, VideoRecord, Task
from ..serializers import CameraSerializer, VideoRecordSerializer


class CameraView(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    lookup_field = 'pk'
    queryset = Camera.objects.all()
    # permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = CameraSerializer

    def get_queryset(self):
        queryset = self.queryset

        tasks_running = self.request.query_params.get('tasks_running', None)
        if tasks_running is not None:
            queryset = queryset.filter(tasks__status=Task.STATUS_RUNNING)

        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(name__icontains=name)

        address = self.request.query_params.get('address', None)
        if address is not None:
            queryset = queryset.filter(address__icontains=address)

        order_by = self.request.query_params.get('order_by', None)
        if order_by is not None:
            queryset = queryset.order_by(order_by)

        return queryset

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
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

    def retrieve(self, request, pk):
        serializer_context = {'request': request}

        try:
            camera = self.queryset.get(pk=pk)
        except Camera.DoesNotExist:
            raise NotFound(f'A camera with pk={pk} does not exist.')

        serializer = self.serializer_class(
            camera,
            context=serializer_context
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk):
        serializer_context = {'request': request}

        try:
            camera = self.queryset.get(pk=pk)
        except Camera.DoesNotExist:
            raise NotFound(f'A camera with pk={pk} does not exist.')

        serializer = self.serializer_class(
            camera,
            context=serializer_context,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk):

        try:
            camera = self.queryset.get(pk=pk)
        except Camera.DoesNotExist:
            raise NotFound(f'A camera with pk={pk} does not exist.')

        camera.delete()

        return Response(None, status=status.HTTP_204_NO_CONTENT)


class VideoRecordView(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):

    lookup_field = 'pk'
    queryset = VideoRecord.objects.all()
    # permission_classes = (IsAuthenticatedOrReadOnly,)
    # renderer_classes = (PropertyJSONRenderer,)
    serializer_class = VideoRecordSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        queryset = self.queryset

        tasks_running = self.request.query_params.get('tasks_running', None)
        if tasks_running is not None:
            queryset = queryset.filter(tasks__status=Task.STATUS_RUNNING)

        min_timestamp = self.request.query_params.get('min_timestamp', None)
        if min_timestamp is not None:
            queryset = queryset.filter(created_at__gt=min_timestamp)

        max_timestamp = self.request.query_params.get('max_timestamp', None)
        if max_timestamp is not None:
            queryset = queryset.filter(created_at__lt=max_timestamp)

        min_duration = self.request.query_params.get('min_duration', None)
        if min_duration is not None:
            try:
                queryset = queryset.filter(duration_seconds__gt=float(min_duration))
            except ValueError:
                pass

        max_duration = self.request.query_params.get('max_duration', None)
        if max_duration is not None:
            try:
                queryset = queryset.filter(duration_seconds__lt=float(max_duration))
            except ValueError:
                pass

        order_by = self.request.query_params.get('order_by', None)
        if order_by is not None:
            queryset = queryset.order_by(order_by)

        return queryset

    def list(self, request):
        serializer_context = {'request': request}
        page = self.paginate_queryset(self.get_queryset())

        serializer = self.serializer_class(
            page,
            context=serializer_context,
            many=True
        )
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, pk):
        serializer_context = {'request': request}

        try:
            video_record = self.queryset.get(pk=pk)
        except VideoRecord.DoesNotExist:
            raise NotFound('A subject with this pk does not exist.')

        serializer = self.serializer_class(
            video_record,
            context=serializer_context
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk):

        try:
            video = self.queryset.get(pk=pk)
        except VideoRecord.DoesNotExist:
            raise NotFound(f'A video record with pk={pk} does not exist.')

        video.delete()

        return Response(None, status=status.HTTP_204_NO_CONTENT)


