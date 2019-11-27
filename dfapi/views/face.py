from rest_framework import status, viewsets, mixins
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from ..models import Face
from ..serializers import FaceSerializer, FacesSerializer


class FaceView(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):

    # permission_classes = (IsAuthenticated,)
    # permission_classes = (AllowAny,)
    lookup_field = 'pk'
    queryset = Face.objects.all()
    # parser_classes = (MultiPartParser, FormParser)
    serializer_class = FaceSerializer

    def get_queryset(self):
        queryset = self.queryset

        camera = self.request.query_params.get('camera', None)
        if camera is not None:
            queryset = queryset.filter(task__camera=camera)

        order_by = self.request.query_params.get('order_by', None)
        if order_by is not None:
            queryset = queryset.order_by(order_by)

        return queryset

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

        serializer = FacesSerializer(
            page,
            context=serializer_context,
            many=True
        )
        return self.get_paginated_response(serializer.data)

    def partial_update(self, request, pk=None):
        try:
            face = Face.objects.get(pk=pk)
        except Face.DoesNotExist:
            raise NotFound(f'Face with pk={pk} does not exist.')

        serializer_context = {'request': request}
        serializer = self.serializer_class(
            face,
            data=request.data,
            context=serializer_context,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        try:
            face = Face.objects.get(pk=pk)
        except Face.DoesNotExist:
            raise NotFound(f'Face with pk={pk} does not exist.')

        face.delete()

        return Response(None, status=status.HTTP_204_NO_CONTENT)