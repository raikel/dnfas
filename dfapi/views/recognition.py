from rest_framework import status, viewsets, mixins
from rest_framework.response import Response

from ..models import Recognition
from ..serializers import RecognitionSerializer

from ..services.faces import face_analyzer


class RecognitionView(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    lookup_field = 'pk'
    queryset = Recognition.objects.all()
    serializer_class = RecognitionSerializer

    def create(self, request):
        serializer_context = {'request': request}
        serializer = self.serializer_class(
            data=request.data,
            context=serializer_context
        )
        serializer.is_valid(raise_exception=True)
        recognition = serializer.save()

        face_analyzer.recognize_face(recognition.pk)
        recognition = Recognition.objects.get(pk=recognition.pk)
        serializer = self.serializer_class(
            recognition,
            context=serializer_context
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
