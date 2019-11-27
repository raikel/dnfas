from rest_framework.routers import SimpleRouter

from .views import (
    SubjectView,
    SubjectSegmentView,
    FaceView,
    RecognitionView,
    FrameView,
    CameraView,
    VideoRecordView,
    TaskView,
    StatView,
    NotificationView
)

app_name = 'dfapi'

router = SimpleRouter()
router.register(r'subjects', SubjectView)
router.register(r'cameras', CameraView)
router.register(r'videos', VideoRecordView)
router.register(r'tasks', TaskView)
router.register(r'frames', FrameView)
router.register(r'faces', FaceView, basename='faces')
router.register(r'segments', SubjectSegmentView)
router.register(r'stats', StatView)
router.register(r'notifications', NotificationView)
router.register(r'recognition', RecognitionView)

urlpatterns = router.urls
