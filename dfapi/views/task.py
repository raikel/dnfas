from rest_framework import status, viewsets, mixins
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.decorators import action

from .mixins import (
    RetrieveMixin,
    ListMixin
)
from ..models import Task
from ..serializers import TaskSerializer
from .. import services


class TaskView(
    RetrieveMixin,
    ListMixin,
    viewsets.GenericViewSet,
):
    """
    retrieve:
        Return a task instance.

    list:
        Return all task.

    create:
        Create a new task.

    destroy:
        Remove an existing task.

    start:
        Start task execution.

    pause:
        Start task execution.

    resume:
        Resume task execution.

    stop:
        Stop task execution.
    """

    model_name = 'Task'
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
        return self._do_action(request, pk, 'start')

    @action(detail=True, methods=['post'])
    def pause(self, request, pk):
        return self._do_action(request, pk, 'pause')

    @action(detail=True, methods=['post'])
    def resume(self, request, pk):
        return self._do_action(request, pk, 'resume')

    @action(detail=True, methods=['post'])
    def stop(self, request, pk):
        return self._do_action(request, pk, 'stop')

    def _do_action(self, request, pk, action_name):
        serializer_context = {'request': request}

        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound(f'A task with pk={pk} does not exists.')

        try:
            if action_name == 'start':
                services.tasks.start(task)
            elif action_name == 'pause':
                services.tasks.pause(task)
            elif action_name == 'resume':
                services.tasks.resume(task)
            elif action_name == 'stop':
                services.tasks.stop(task)
        except services.ServiceError as err:
            raise ValidationError(err)

        serializer = self.serializer_class(
            task,
            context=serializer_context
        )
        return Response(serializer.data, status=status.HTTP_200_OK)