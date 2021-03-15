from psychopy.iohub.devices import eyetracker as iohub
#from psychopy.iohub.devices.eyetracker import models, eventTypes
models = [None]
eventTypes = [None]
from ast import literal_eval as listify
import numpy as np
import pandas as pd
from psychopy.visual.basevisual import ContainerMixin
from psychopy.constants import NOT_STARTED


class EyeTrackerRecorder:
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

    def getPosition(self):
        # Get x and y coords of eye
        return

    def poll(self):
        x, y = (0.2, 0.2)
        pupil = 1
        # Check if x and y are in any rois
        rois = []
        for name, roi in self.rois.items():
            if roi.contains(x, y):
                rois.append(name)
        self.data = self.data.append({'x': x, 'y': y, 'roi': rois, 'pupil': pupil}, ignore_index=True)


class EyeTrackerConfig(dict):
    # Default values for each key
    _defaults = {'name': "",
                 'save_events': True,
                 'stream_events': True,
                 'auto_report_events': False,
                 'interval': 0.001,
                 'event_buffer_length': 1024,
                 'monitor_event_types': eventTypes,
                 'sampling_rate': 250,
                 'model_name': models[0],
                 'device_number': 0,
                 }
    # Required value types for each key
    _valTypes = {'name': str,
                 'save_events': bool,
                 'stream_events': bool,
                 'auto_report_events': bool,
                 'interval': float,
                 'event_buffer_length': int,
                 'monitor_event_types': list,
                 'sampling_rate': int,
                 'model_name': str,
                 'device_number': int,
                 }

    def __init__(self,
                 name=_defaults['name'],
                 save_events=_defaults['save_events'],
                 stream_events=_defaults['stream_events'],
                 auto_report_events=_defaults['auto_report_events'],
                 interval=_defaults['interval'],
                 event_buffer_length=_defaults['event_buffer_length'],
                 monitor_event_types=_defaults['monitor_event_types'],
                 sampling_rate=_defaults['sampling_rate'],
                 model_name=_defaults['model_name'],
                 device_number=_defaults['device_number'],
                 ):
        # Initialise dict with default values
        dict.__init__(self,
                      name=self._defaults['name'],
                      save_events=self._defaults['save_events'],
                      stream_events=self._defaults['stream_events'],
                      auto_report_events=self._defaults['auto_report_events'],
                      interval=self._defaults['interval'],
                      event_buffer_length=self._defaults['event_buffer_length'],
                      monitor_event_types=self._defaults['monitor_event_types'],
                      sampling_rate=self._defaults['sampling_rate'],
                      model_name=self._defaults['model_name'],
                      device_number=self._defaults['device_number'],
                      )
        # Set values as specified, going through __setitem__ method
        self['name'] = name
        self['save_events'] = save_events
        self['stream_events'] = stream_events
        self['auto_report_events'] = auto_report_events
        self['interval'] = interval
        self['event_buffer_length'] = event_buffer_length
        self['monitor_event_types'] = monitor_event_types
        self['sampling_rate'] = sampling_rate
        self['model_name'] = model_name
        self['device_number'] = device_number

    def __setitem__(self, key, value):
        # Limit setting to just existing keys
        if key not in self:
            raise KeyError("{} is not a recognised as an eye tracker congifuration option.".format(key))
        # Start off as invalid
        valid = False
        # Validate val types
        if self._valTypes[key] in [str, bool, int, float]:
            # Validate basic types
            try:
                value = self._valTypes[key](value)
                valid = True
            except ValueError:
                valid = False
        elif self._valTypes[key] == list:
            if isinstance(value, str):
                # Handle strings which look like a list
                try:
                    value = listify(value)
                except ValueError:
                    value = listify(f"\"{value}\"") # Try again with extra quotes
            if isinstance(value, str):
                # If it's still a string after listification, just wrap it
                value = [value]
            # Validate lists
            valid = isinstance(value, (list, tuple))
        # Raise error if valType isn't valid
        if valid:
            # Validate special cases
            if key == 'interval':
                # Interval must be between 0.001 and 0.020
                valid = 0.001 <= value <= 0.020
            if key == 'event_buffer_length':
                # Buffer length must be an integer between 0 and 2048
                valid = value in range(2048+1)
            if key == 'monitor_event_types':
                # All event types must be in eventTypes list
                for v in value:
                    if str(v) not in eventTypes:
                        valid = False
            if key == 'sampling_rate':
                # Sampling rate must be an integer between 0 and 2000
                valid = value in range(2000+1)
            if key == 'model_name':
                valid = value in models

        # Do actual setting
        if valid:
            dict.__setitem__(self, key, value)
        else:
            raise ValueError("{} is not a valid value for eye tracker configuration option `{}`.".format(value, key))

    def __delitem__(self, key):
        # Limit deleting to just existing keys
        if key not in self:
            raise KeyError("{} is not a recognised as an eye tracker congifuration option.".format(key))
        # Reset that key to default
        self[key] = self._defaults[key]
