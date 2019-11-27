from rest_framework import status, viewsets, mixins
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.decorators import action

from ..models import Task
from ..serializers import TaskSerializer
from .. import services


class TaskView(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):

    lookup_field = 'pk'
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = self.queryset
        params = self.request.query_params

        if params.getlist('status', None) is not None and len(params.getlist('status', None)):
            queryset = queryset.filter(status__in=params.getlist('status'))
        elif params.get('status', None) is not None:
            queryset = queryset.filter(status=params['status'])

        if params.get('camera', None) is not None:
            queryset = queryset.filter(camera=params['camera'])

        if params.get('video', None) is not None:
            queryset = queryset.filter(video=params['video'])

        if params.get('order_by', None) is not None:
            queryset = queryset.order_by(params['order_by'])

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
            task = self.queryset.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound(f'A task with pk={pk} does not exist.')

        serializer = self.serializer_class(
            task,
            context=serializer_context
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):

        serializer_context = {'request': request}
        serializer = self.serializer_class(
            data=request.data,
            context=serializer_context
        )
        serializer.is_valid(raise_exception=True)
        task = serializer.save()

        try:
            services.tasks.create(task)
        except services.ServiceError as err:
            raise ValidationError(err)

        serializer = self.serializer_class(
            task,
            context=serializer_context
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk):

        try:
            task = self.queryset.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound(f'A task with pk={pk} does not exist.')

        try:
            services.tasks.stop(task)
        except services.ServiceError as err:
            pass

        task.delete()

        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def start(self, request, pk):

        serializer_context = {'request': request}

        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound(f'A task with pk={pk} does not exists.')

        try:
            services.tasks.pause(task)
        except services.ServiceError as err:
            raise ValidationError(err)

        serializer = self.serializer_class(
            task,
            context=serializer_context
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def pause(self, request, pk):

        serializer_context = {'request': request}

        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound(f'A task with pk={pk} does not exists.')

        try:
            services.tasks.pause(task)
        except services.ServiceError as err:
            raise ValidationError(err)

        serializer = self.serializer_class(
            task,
            context=serializer_context
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def resume(self, request, pk):

        serializer_context = {'request': request}

        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound(f'A task with pk={pk} does not exists.')

        try:
            services.tasks.resume(task)
        except services.ServiceError as err:
            raise ValidationError(err)

        serializer = self.serializer_class(
            task,
            context=serializer_context
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def stop(self, request, pk):
        serializer_context = {'request': request}

        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound(f'A task with pk={pk} does not exists.')

        try:
            services.tasks.stop(task)
        except services.ServiceError as err:
            raise ValidationError(err)

        serializer = self.serializer_class(
            task,
            context=serializer_context
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
