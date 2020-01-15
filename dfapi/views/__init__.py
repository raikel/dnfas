from .face import FaceView
from .frame import FrameView
from .media import CameraView, VideoRecordView
from .subject import SubjectView, SubjectSegmentView
from .task import TaskView
from .stat import StatView
from .notification import NotificationView
from .recognition import RecognitionView


class ServiceError(Exception):
    pass
