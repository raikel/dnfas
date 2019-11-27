from rest_framework import status, viewsets, mixins
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.decorators import action

from ..models import Notification
from ..serializers import NotificationSerializer


class NotificationView(
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):

    lookup_field = 'pk'
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = self.queryset
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

    def destroy(self, request, pk=None):
        try:
            notification = Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            raise NotFound(f'Notification with pk={pk} does not exist.')

        notification.delete()

        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def see(self, request, pk=None):
        serializer_context = {'request': request}

        try:
            notification = Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            raise NotFound(f'Notification with pk={pk} does not exist.')

        notification.seen = True
        notification.save()

        serializer = self.serializer_class(
            notification,
            context=serializer_context
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
