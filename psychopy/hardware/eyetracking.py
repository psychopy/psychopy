import psychopy.iohub as iohub
from psychopy.iohub.devices.eyetracker import models, eventTypes
from ast import literal_eval as listify
import numpy as np
import pandas as pd
from psychopy.visual.basevisual import ContainerMixin
from psychopy.constants import NOT_STARTED


class EyeTrackerRecording:
    def __init__(self, win, config,
                 rois=None):
        self.win = win
        self.config = config
        self.rois = rois
        self.status = NOT_STARTED

        self.data = pd.DataFrame({'x': [], 'y': [], 'roi': [], 'pupil': []})

    @property
    def rois(self):
        if hasattr(self, "_rois"):
            return self._rois
        else:
            return {}

    @rois.setter
    def rois(self, value):
        if value is None:
            return
        if not isinstance(value, (list, tuple)):
            value = [value]
        rois = {}
        for obj in value:
            if isinstance(obj, ContainerMixin):
                rois[obj.name] = obj
            else:
                raise TypeError("Region of interest must be a PsychoPy object with vertices and a `contains` method")
        self._rois = rois

    def poll(self):
        x, y = (0.2, 0.2)
        pupil = 1
        # Check if x and y are in any rois
        rois = []
        for name, roi in self.rois.items():
            if roi.contains(x, y):
                rois.append(name)
        self.data = self.data.append({'x': x, 'y': y, 'roi': rois, 'pupil': pupil}, ignore_index=True)


class EyeTrackerConfig:
    def __init__(self, model,
                 name="eyetracker",
                 auto_report_events=None,
                 interval=None,
                 sampling_rate=None,
                 device_number=None,
                 ):
        # Set values as specified, going through __setitem__ method
        self.settings = config = {
            'save_events': True,
            'stream_events': False,
            'monitor_event_types': eventTypes,
            'auto_report_events': auto_report_events,
            'interval': interval,
            'event_buffer_length': 1,
            'sampling_rate': sampling_rate,
            'device_number': device_number
        }
        self.name = name
        self.model = config['model_name'] = model

        self.stream = iohub.client.ioHubConnection(iohubConfig=config)

