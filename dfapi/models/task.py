from django.db import models


class Task(models.Model):

    STATUS_CREATED = 'created'
    STATUS_RUNNING = 'running'
    STATUS_PAUSED = 'paused'
    STATUS_STOPPED = 'stopped'
    STATUS_KILLED = 'killed'
    STATUS_SUCCESS = 'success'
    STATUS_FAILURE = 'failure'
    STATUS_REVOKED = 'revoked'
    STATUS_RETRY = 'retry'

    STATUS_CHOICES = [
        (STATUS_CREATED, 'Created'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_PAUSED, 'Paused'),
        (STATUS_STOPPED, 'Stopped'),
        (STATUS_KILLED, 'Killed'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILURE, 'Failure'),
        (STATUS_REVOKED, 'Revoked'),
        (STATUS_RETRY, 'Retry')
    ]

    MODE_ALL = 'all'
    MODE_HUNT = 'hunt'

    MODE_CHOICES = [
        (MODE_ALL, 'Find all faces'),
        (MODE_HUNT, 'Hunt faces'),
    ]

    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_CREATED
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    schedule_start_at = models.DateTimeField(null=True, blank=True)
    schedule_stop_at = models.DateTimeField(null=True, blank=True)
    repeat = models.BooleanField(blank=True, default=False)
    repeat_days = models.CharField(max_length=7, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    frames_count = models.IntegerField(blank=True, default=0)
    faces_count = models.IntegerField(blank=True, default=0)
    processing_time = models.FloatField(blank=True, default=0)
    frame_rate = models.FloatField(blank=True, default=0)
    progress = models.FloatField(blank=True, default=-1)
    mode = models.CharField(
        max_length=16, choices=MODE_CHOICES, blank=True, default=MODE_ALL
    )
    detection_min_height = models.IntegerField(null=True, blank=True)
    detection_min_score = models.FloatField(null=True, blank=True)
    similarity_thresh = models.FloatField(null=True, blank=True)
    max_frame_size = models.IntegerField(null=True, blank=True)
    frontal_faces = models.BooleanField(null=True, blank=True)
    video_detect_interval = models.FloatField(null=True, blank=True)
    faces_time_memory = models.FloatField(null=True, blank=True)
    store_face_frames = models.BooleanField(null=True, blank=True)
    video_start_at = models.FloatField(null=True, blank=True)
    video_stop_at = models.FloatField(null=True, blank=True)

    hunted_subjects = models.ManyToManyField(
        'Subject',
        related_name='hunting_tasks'
    )

    camera = models.ForeignKey(
        'Camera',
        null=True,
        blank=True,
        related_name='tasks',
        on_delete=models.CASCADE
    )

    video = models.ForeignKey(
        'VideoRecord',
        null=True,
        blank=True,
        related_name='tasks',
        on_delete=models.CASCADE
    )

    worker = models.ForeignKey(
        'Worker',
        null=True,
        blank=True,
        related_name='tasks',
        on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Task {self.pk}'


class HuntMatch(models.Model):
    target_subject = models.ForeignKey(
        'Subject',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='hunt_targets'
    )

    matched_subject = models.ForeignKey(
        'Subject',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='hunt_matches'
    )

    score = models.FloatField(blank=True, default=0)

    task = models.ForeignKey(
        'Task',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='hunts'
    )
