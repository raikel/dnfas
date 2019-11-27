from rest_framework import status, viewsets, mixins
from rest_framework.response import Response

from ..models import Stat
from ..serializers import StatSerializer


class StatView(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):

    lookup_field = 'pk'
    queryset = Stat.objects.all()
    # permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = StatSerializer

    def get_queryset(self):
        queryset = self.queryset

        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(name=name)

        resolution = self.request.query_params.get('resolution', None)
        if resolution is not None:
            queryset = queryset.filter(resolution=resolution)

        order_by = self.request.query_params.get('order_by', None)
        if order_by is not None:
            queryset = queryset.order_by(order_by)

        return queryset

    def list(self, request):
        serializer_context = {'request': request}
        # page = self.paginate_queryset(self.get_queryset())

        serializer = self.serializer_class(
            self.get_queryset(),
            context=serializer_context,
            many=True
        )
        return Response({
            'results': serializer.data
        }, status=status.HTTP_200_OK)