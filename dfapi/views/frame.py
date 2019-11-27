from rest_framework import status, viewsets, mixins
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.decorators import action

from ..models import Frame
from ..serializers import FrameSerializer, FacesSerializer

from ..services.faces import face_analyzer


class FrameView(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    lookup_field = 'pk'
    queryset = Frame.objects.all()
    serializer_class = FrameSerializer

    def create(self, request):
        serializer_context = {'request': request}
        serializer = self.serializer_class(
            data=request.data,
            context=serializer_context,
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

    def retrieve(self, request, pk):
        serializer_context = {'request': request}

        try:
            frame = self.queryset.get(pk=pk)
        except Frame.DoesNotExist:
            raise NotFound('A subject with this pk does not exist.')

        serializer = self.serializer_class(
            frame,
            context=serializer_context
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        try:
            frame = Frame.objects.get(pk=pk)
        except Frame.DoesNotExist:
            raise NotFound(f'Frame with pk={pk} does not exist.')

        frame.delete()

        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def detect_faces(self, request, pk=None):

        try:
            frame = Frame.objects.get(pk=pk)
        except Frame.DoesNotExist:
            raise NotFound(f'A frame with pk={pk} does not exists.')

        for face in frame.faces.all():
            face.delete()

        face_analyzer.analyze_frame(frame.pk)
        frame = Frame.objects.get(pk=pk)
        faces = frame.faces.all()

        serializer_context = {'request': request}

        serializer = FacesSerializer(
            faces,
            context=serializer_context,
            many=True
        )

        return Response(serializer.data, status=status.HTTP_200_OK)