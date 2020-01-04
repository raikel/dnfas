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
router.register(r'subjects', SubjectView, 'subjects')
router.register(r'cameras', CameraView, 'cameras')
router.register(r'videos', VideoRecordView, 'videos')
router.register(r'tasks', TaskView, 'tasks')
router.register(r'frames', FrameView, 'frames')
router.register(r'faces', FaceView, 'faces')
router.register(r'segments', SubjectSegmentView, 'segments')
router.register(r'stats', StatView, 'stats')
router.register(r'notifications', NotificationView, 'notifications')
router.register(r'recognition', RecognitionView, 'recognition')

urlpatterns = router.urls
