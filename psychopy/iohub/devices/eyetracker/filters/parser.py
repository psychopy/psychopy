# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).

"""
ioHub Eye Tracker Online Sample Event Parser

WORK IN PROGRESS - VERY EXPERIMENTAL

Copyright (C) 2012-2014 iSolver Software Solutions
Distributed under the terms of the GNU General Public License
(GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com>
.. fileauthor:: Sol Simpson <sol@isolver-software.com>

NOTES:

* The parser is designed to work with monocular and binocular eye data,
but only binocular input samples have been tested so far.
* If binocular input samples are being used, they are converted to monocular
samples for parsing. If both left and right eye position data is available
for a sample, the positions are averaged together. If only one of the two eyes
has valid data, then that eye data is used for the sample. So the only case
where a sample will be tagged as missing data is when both eyes do not have
valid eye position / pupil size data.

POSITION_FILTER and VELOCITY_FILTER can be set to one of the following event
field filter types. Example values for any input arguments are given. The filter
is selected by giving the filter class name followed by a dictionary of values
to use for the filter. Valid filter options depend on the filter selected.

eventfilters.MovingWindowFilter
--------------------------------

This is a standard averaging filter. Any samples within the window buffer are
simply averaged together to give the filtered value for a given sample.

Parameters:
    * length: The size of the moving window in samples. Minimum of 2 required.
    * knot_pos: The index within the moving window that should be used to extract
                a sample from and apply the current window filtered value.

Example:

POSITION_FILTER = eventfilters.MovingWindowFilter, {length: 3, knot_pos:'center'}

Applies the MovingWindowFilter to x and y gaze data fields of eye samples. The
window size is three, and each sample position is filtered using data from the
previous and next samples as well as itself.

eventfilters.PassThroughFilter
---------------------------------

A NULL filter. In other words, the filter does not do any filtering.

Parameters: None

Example:

VELOCITY_FILTER = eventfilters.PassThroughFilter, {}

Velocity data is calculated from (filtered) sample positions, but is not
filtered itself.

eventfilters.MedianFilter
-----------------------------

MedianFilter applies the median value of the filter window to the knot_pos
window sample.

Parameters:
    * length: The size of the moving window in samples. Minimum of 3 is
      required and the length must be odd.
    * knot_pos: The index within the moving window that should be used to extract
                a sample from and apply the current window filtered value.
Example:

POSITION_FILTER = eventfilters.MedianFilter, {length: 3, knot_pos: 0}

Sample position fields are filtered by the median value of three samples, those
being the current sample and the two following samples (so the current sample is
at index 0.

eventfilters.WeightedAverageFilter
-----------------------------------

WeightedAverageFilter is similar to the standard MovingWindowFilter field filter,
however each element in the window is assigned a weighting factor that is used
during averaging.

Parameters:
    * weights: A list of weights to be applied to the window values. The window
    length is == len(weights). The weight values are all normalized to sum to 1
    before use in the filter. For example, a weight list of (25,50,25) will be
    converted to (0.25,0.50,0.25) for use in the filter, with window value index
    i being multiplied by weith list index i.
    * knot_pos: The index within the moving window that should be used to extract
                a sample from and apply the current window filtered value.

Example:

VELOCITY_FILTER = eventfilters.WeightedAverageFilter, {weights: (25,50,25), knot_pos: 1}

A weighted average window filter will be applied to x and y velocity fields.
The length of the window is 3 samples, and the filtered sample index retrieved
is 1, the same as using 'center' in this case. The filtered sample index will
count toward 1/2 the weighted average, with the previous and next samples
contributing 1/4 of the weighted average each.

eventfilters.StampFilter
--------------------------

A variant of the filter proposed by Dr. David Stampe (1993 ???). A window of
length 3 is used, with the knot_pos centered, or at index 1. If the current
3 values in the window list are monotonic, then the sample is not filtered.
If the values are non-monotonic, then v[1] = (v[0]+v[2])/2.0

Parameters:
    * levels: The number of iterations (recursive) that should be applied to the
              windowed data. Minimum value is 1. The number of levels equals
              the number of samples the filtered sample will be delayed
              compared to the non filtered sample time.

Example:

POSITION_FILTER = eventfilters.StampFilter, {level: 1}

Data is filtered once, similar to what a 'normal' filter level would be in the
  eyelink<tm> system. Level = 2 would be similar to the 'extra' filter level
  setting of eyelink<tm>.
"""
import numpy as np
from ....constants import EventConstants
from ....errors import print2err
from ... import DeviceEvent, eventfilters
from collections import OrderedDict
from ....util.visualangle import VisualAngleCalc

MONOCULAR_EYE_SAMPLE = EventConstants.MONOCULAR_EYE_SAMPLE
BINOCULAR_EYE_SAMPLE = EventConstants.BINOCULAR_EYE_SAMPLE
FIXATION_START = EventConstants.FIXATION_START
FIXATION_END = EventConstants.FIXATION_END
SACCADE_START = EventConstants.SACCADE_START
SACCADE_END = EventConstants.SACCADE_END
BLINK_START = EventConstants.BLINK_START
BLINK_END = EventConstants.BLINK_END

NO_EYE = 0
LEFT_EYE = 1
RIGHT_EYE = 2
BOTH_EYE = 3


class EyeTrackerEventParser(eventfilters.DeviceEventFilter):

    def __init__(self, **kwargs):
        eventfilters.DeviceEventFilter.__init__(self, **kwargs)
        self.sample_type = None
        self.io_sample_class = None
        self.io_event_ix = None
        self.last_valid_sample = None
        self.last_sample = None
        self.invalid_samples_run = []
        self._last_parser_sample = None
        self.open_parser_events = OrderedDict()
        self.convertEvent = None
        self.isValidSample = None
        self.vel_thresh_history_dur = kwargs.get(
            'adaptive_vel_thresh_history', 3.0)
        position_filter = kwargs.get('position_filter')
        velocity_filter = kwargs.get('velocity_filter')
        display_device = kwargs.get('display_device')
        sampling_rate = kwargs.get('sampling_rate')

        if position_filter:
            pos_filter_class_name = position_filter.get(
                'name', 'PassThroughFilter')
            pos_filter_class = getattr(eventfilters, pos_filter_class_name)
            del position_filter['name']
            pos_filter_kwargs = position_filter
        else:
            pos_filter_class, pos_filter_kwargs = eventfilters.PassThroughFilter, {}

        if velocity_filter:
            vel_filter_class_name = position_filter.get(
                'name', 'PassThroughFilter')
            vel_filter_class = getattr(eventfilters, vel_filter_class_name)
            del velocity_filter['name']
            vel_filter_kwargs = velocity_filter
        else:
            vel_filter_class, vel_filter_kwargs = eventfilters.PassThroughFilter, {}

        self.adaptive_x_vthresh_buffer = np.zeros(
            self.vel_thresh_history_dur * sampling_rate)
        self.x_vthresh_buffer_index = 0
        self.adaptive_y_vthresh_buffer = np.zeros(
            self.vel_thresh_history_dur * sampling_rate)
        self.y_vthresh_buffer_index = 0

        pos_filter_kwargs['event_type'] = MONOCULAR_EYE_SAMPLE
        pos_filter_kwargs['inplace'] = True
        pos_filter_kwargs['event_field_name'] = 'angle_x'
        self.x_position_filter = pos_filter_class(**pos_filter_kwargs)
        pos_filter_kwargs['event_field_name'] = 'angle_y'
        self.y_position_filter = pos_filter_class(**pos_filter_kwargs)

        vel_filter_kwargs['event_type'] = MONOCULAR_EYE_SAMPLE
        vel_filter_kwargs['inplace'] = True
        vel_filter_kwargs['event_field_name'] = 'velocity_x'
        self.x_velocity_filter = vel_filter_class(**vel_filter_kwargs)
        vel_filter_kwargs['event_field_name'] = 'velocity_y'
        self.y_velocity_filter = vel_filter_class(**vel_filter_kwargs)
        vel_filter_kwargs['event_field_name'] = 'velocity_xy'
        self.xy_velocity_filter = vel_filter_class(**vel_filter_kwargs)

        ###
        mm_size = display_device.get('mm_size')
        if mm_size:
            mm_size = mm_size['width'], mm_size['height'],
        pixel_res = display_device.get('pixel_res')
        eye_distance = display_device.get('eye_distance')
        self.visual_angle_calc = VisualAngleCalc(mm_size,
                                                 pixel_res,
                                                 eye_distance)
        self.pix2deg = self.visual_angle_calc.pix2deg

    @property
    def filter_id(self):
        return 23

    @property
    def input_event_types(self):
        event_type_and_filter_ids = dict()
        event_type_and_filter_ids[BINOCULAR_EYE_SAMPLE] = [0, ]
        event_type_and_filter_ids[MONOCULAR_EYE_SAMPLE] = [0, ]
        return event_type_and_filter_ids

    def process(self):
        """"""
        samples_for_processing = []
        for in_evt in self.getInputEvents():
            if self.sample_type is None:
                self.initializeForSampleType(in_evt)

            # If event is binocular, convert to monocular.
            # Regardless of type, convert pix to angle positions and calculate
            # unfiltered velocity data.
            current_mono_evt = self.convertEvent(self.last_sample, in_evt)

            is_valid = self.isValidSample(current_mono_evt)
            if is_valid:
                # If sample is valid (no missing pos data), first
                # check for a previous missing data run and handle.
                if self.invalid_samples_run:
                    if self.last_valid_sample:
                        samples_for_processing.extend(
                            self.interpolateMissingData(current_mono_evt))
                        self._addVelocity(
                            samples_for_processing[-1], current_mono_evt)
                    # Discard all invalid samples that occurred prior
                    # to the first valid sample.
                    del self.invalid_samples_run[:]

                # Then add current event to field filters. If a filtered event
                # is returned, add it to the to be processed sample list.
                filtered_event = self.addToFieldFilters(current_mono_evt)
                if filtered_event:
                    filtered_event, _junk = filtered_event
                    x_vel_thresh, y_vel_thresh = self.addVelocityToAdaptiveThreshold(
                        filtered_event)
                    filtered_event[self.io_event_ix('raw_x')] = x_vel_thresh
                    filtered_event[self.io_event_ix('raw_y')] = y_vel_thresh
                    samples_for_processing.append(filtered_event)
                self.last_valid_sample = current_mono_evt
            else:
                self.invalid_samples_run.append(current_mono_evt)
                self.addOutputEvent(current_mono_evt)

            self.last_sample = current_mono_evt

        # Add any new filtered samples to be output.
        # Also create parsed events with no heuristics being used
        # at this point.
        for s in samples_for_processing:
            self.parseEvent(s)
            if self.isValidSample(s):
                self.addOutputEvent(s)

        self.clearInputEvents()

    def parseEvent(self, sample):
        if self._last_parser_sample:
            last_sec = self.getSampleEventCategory(self._last_parser_sample)
            current_sec = self.getSampleEventCategory(sample)
            if last_sec and last_sec != current_sec:
                start_event, end_event = self.createEyeEvents(
                    last_sec, current_sec, self._last_parser_sample, sample)
                if start_event:
                    self.addOutputEvent(start_event)
                if end_event:
                    self.addOutputEvent(end_event)
            else:
                self.open_parser_events.setdefault(
                    current_sec + '_SAMPLES', []).append(sample)
        self._last_parser_sample = sample

    def getSampleEventCategory(self, sample):
        if self.isValidSample(sample):
            x_velocity_threshold = sample[self.io_event_ix('raw_x')]
            y_velocity_threshold = sample[self.io_event_ix('raw_y')]
            if x_velocity_threshold == np.NaN:
                return None
            sample_vx = sample[self.io_event_ix('velocity_x')]
            sample_vy = sample[self.io_event_ix('velocity_y')]
            if sample_vx >= x_velocity_threshold or sample_vy >= y_velocity_threshold:
                return 'SAC'
            return 'FIX'
        return 'MIS'

    def createEyeEvents(
            self,
            last_sample_category,
            current_sample_category,
            last_sample,
            current_sample):
        start_event = None
        end_event = None

        if last_sample_category == 'MIS':
            # Create end blink event
            existing_start_event = self.open_parser_events.get('MIS')
            evt_samples = self.open_parser_events.get('MIS_SAMPLES')
            if evt_samples:
                del self.open_parser_events['MIS_SAMPLES']

            if existing_start_event:
                end_event = self.createBlinkEndEventArray(
                    last_sample, existing_start_event, evt_samples)
                del self.open_parser_events['MIS']
            else:
                # print2err("PARSER Warning: Blink Start Event not found; Blink End event being dropped: ", end_event)
                pass
        elif last_sample_category == 'FIX':
            # Create end fix event
            existing_start_event = self.open_parser_events.get('FIX')
            evt_samples = self.open_parser_events.get('FIX_SAMPLES')
            if evt_samples:
                del self.open_parser_events['FIX_SAMPLES']
            if existing_start_event:
                end_event = self.createFixationEndEventArray(
                    last_sample, existing_start_event, evt_samples)
                del self.open_parser_events['FIX']
            else:
                # print2err("PARSER Warning: Fixation Start Event not found; Fixation End event being dropped: ", end_event)
                pass
        elif last_sample_category == 'SAC':
            # Create end sac event
            existing_start_event = self.open_parser_events.get('SAC')
            evt_samples = self.open_parser_events.get('SAC_SAMPLES')
            if evt_samples:
                del self.open_parser_events['SAC_SAMPLES']
            if existing_start_event:
                end_event = self.createSaccadeEndEventArray(
                    last_sample, existing_start_event, evt_samples)
                del self.open_parser_events['SAC']
            else:
                # print2err("PARSER Warning: Saccade Start Event not found; Saccade End event being dropped: ", end_event)
                pass

        if current_sample_category == 'MIS':
            # Create start blink event
            start_event = self.createBlinkStartEventArray(current_sample)
            self.open_parser_events['MIS_SAMPLES'] = [current_sample, ]
            existing_start_event = self.open_parser_events.get('MIS')
            if existing_start_event:
                print2err(
                    'PARSER ERROR: Blink Start Event already Open and is being dropped: ',
                    existing_start_event)
            self.open_parser_events['MIS'] = current_sample

        elif current_sample_category == 'FIX':
            # Create start fix event
            start_event = self.createFixationStartEventArray(current_sample)
            self.open_parser_events['FIX_SAMPLES'] = [current_sample, ]
            existing_start_event = self.open_parser_events.get('FIX')
            if existing_start_event:
                print2err(
                    'PARSER ERROR: Fixation Start Event already Open and is being dropped: ',
                    existing_start_event)
            self.open_parser_events['FIX'] = current_sample

        elif current_sample_category == 'SAC':
            # Create start sac event
            start_event = self.createSaccadeStartEventArray(current_sample)
            self.open_parser_events['SAC_SAMPLES'] = [current_sample, ]
            existing_start_event = self.open_parser_events.get('SAC')
            if existing_start_event:
                print2err(
                    'PARSER ERROR: Saccade Start Event already Open and is being dropped: ',
                    existing_start_event)
            self.open_parser_events['SAC'] = current_sample

        return end_event, start_event

    def addVelocityToAdaptiveThreshold(self, sample):
        velocity_x = sample[self.io_event_ix('velocity_x')]
        velocity_y = sample[self.io_event_ix('velocity_y')]
        velocity_buffers = [
            self.adaptive_x_vthresh_buffer,
            self.adaptive_y_vthresh_buffer]
        velocity_buffer_indexs = [
            self.x_vthresh_buffer_index,
            self.y_vthresh_buffer_index]
        vthresh_values = []
        for v, velocity in enumerate([velocity_x, velocity_y]):
            current_velocity_buffer = velocity_buffers[v]
            current_vbuffer_index = velocity_buffer_indexs[v]
            blen = len(current_velocity_buffer)
            if velocity > 0.0:
                i = current_vbuffer_index % blen
                current_velocity_buffer[i] = velocity
                full = current_vbuffer_index >= blen
                if v == 0:
                    self.x_vthresh_buffer_index += 1
                else:
                    self.y_vthresh_buffer_index += 1
                if full:
                    PT = current_velocity_buffer.min() + current_velocity_buffer.std() * 3.0
                    velocity_below_thresh = current_velocity_buffer[
                        current_velocity_buffer < PT]
                    PTd = 2.0
                    pt_list = [PT, ]
                    while PTd >= 1.0:
                        if len(pt_list) > 0:
                            PT = velocity_below_thresh.mean() + 3.0 * velocity_below_thresh.std()
                            velocity_below_thresh = current_velocity_buffer[
                                current_velocity_buffer < PT]
                            PTd = np.abs(PT - pt_list[-1])
                        pt_list.append(PT)
                    vthresh_values.append(PT)
            if len(vthresh_values) != v + 1:
                vthresh_values.append(np.NaN)
        return vthresh_values

    def reset(self):
        eventfilters.DeviceEventFilter.reset(self)
        self._last_parser_sample = None
        self.last_valid_sample = None
        self.last_sample = None
        self.invalid_samples_run = []
        self.open_parser_events.clear()
        self.x_position_filter.clear()
        self.y_position_filter.clear()
        self.x_velocity_filter.clear()
        self.y_velocity_filter.clear()
        self.xy_velocity_filter.clear()
        self.x_vthresh_buffer_index = 0
        self.y_vthresh_buffer_index = 0

    def initializeForSampleType(self, in_evt):
        # in_evt[DeviceEvent.EVENT_TYPE_ID_INDEX]
        self.sample_type = MONOCULAR_EYE_SAMPLE
        #print2err("self.sample_type: ",self.sample_type,", ",EventConstants.getName(self.sample_type))
        self.io_sample_class = EventConstants.getClass(self.sample_type)
        self.io_event_fields = self.io_sample_class.CLASS_ATTRIBUTE_NAMES
        #print2err("self.io_sample_class: ",self.io_sample_class,", ",len(self.io_event_fields),"\n>>",self.io_event_fields)
        self.io_event_ix = self.io_sample_class.CLASS_ATTRIBUTE_NAMES.index

        if in_evt[DeviceEvent.EVENT_TYPE_ID_INDEX] == BINOCULAR_EYE_SAMPLE:
            self.convertEvent = self._convertToMonoAveraged
            self.isValidSample = lambda x: x[self.io_event_ix('status')] != 22
        else:
            self.convertEvent = self._convertMonoFields
            self.isValidSample = lambda x: x[self.io_event_ix('status')] == 0

    def interpolateMissingData(self, current_sample):
        samples_for_processing = []
        invalid_sample_count = len(self.invalid_samples_run)
        gx_ix = self.io_event_ix('angle_x')
        gy_ix = self.io_event_ix('angle_y')
        ps_ix = self.io_event_ix('pupil_measure1')
        starting_gx = self.last_valid_sample[gx_ix]
        starting_gy = self.last_valid_sample[gy_ix]
        starting_ps = self.last_valid_sample[ps_ix]
        ending_gx = current_sample[gx_ix]
        ending_gy = current_sample[gy_ix]
        ending_ps = current_sample[ps_ix]
        x_interp = np.linspace(starting_gx, ending_gx,
                               num=invalid_sample_count + 2)[1:-1]
        y_interp = np.linspace(starting_gy, ending_gy,
                               num=invalid_sample_count + 2)[1:-1]
        p_interp = np.linspace(starting_ps, ending_ps,
                               num=invalid_sample_count + 2)[1:-1]
#       print2err('>>>>')
#        print2err('invalid_sample_count: ', invalid_sample_count)
#        print2err('starting_gx, ending_gx: ', starting_gx,', ',ending_gx)
#        print2err('x_interp: ', x_interp)
#        print2err('starting_gy, ending_gy: ', starting_gx,', ',ending_gx)
#        print2err('y_interp: ', y_interp)
#        print2err('<<<<')

        prev_samp = self.last_valid_sample
        # interpolate missing sample values, adding to pos and vel filters
        for ix, curr_samp in enumerate(self.invalid_samples_run):
            curr_samp[gx_ix] = x_interp[ix]
            curr_samp[gy_ix] = y_interp[ix]
            curr_samp[ps_ix] = p_interp[ix]
            self._addVelocity(prev_samp, curr_samp)
            filtered_event = self.addToFieldFilters(curr_samp)
            if filtered_event:
                filtered_event, _junk = filtered_event
                samples_for_processing.append(filtered_event)
            prev_samp = curr_samp
        return samples_for_processing

    def addToFieldFilters(self, sample):
        self.x_position_filter.add(sample)
        self.y_position_filter.add(sample)
        self.x_velocity_filter.add(sample)
        self.y_velocity_filter.add(sample)
        return self.xy_velocity_filter.add(sample)

    def _convertPosToAngles(self, mono_event):
        gx_ix = self.io_event_ix('gaze_x')
        gx_iy = self.io_event_ix('gaze_y')
        mono_event[
            self.io_event_ix('angle_x')], mono_event[
            self.io_event_ix('angle_y')] = self.pix2deg(
            mono_event[gx_ix], mono_event[gx_iy])

    def _addVelocity(self, prev_event, current_event):
        io_ix = self.io_event_ix

        dx = np.abs(
            current_event[
                io_ix('angle_x')] -
            prev_event[
                io_ix('angle_x')])
        dy = np.abs(
            current_event[
                io_ix('angle_y')] -
            prev_event[
                io_ix('angle_y')])
        dt = current_event[io_ix('time')] - prev_event[io_ix('time')]

        current_event[io_ix('velocity_x')] = dx / dt
        current_event[io_ix('velocity_y')] = dy / dt
        current_event[io_ix('velocity_xy')] = np.hypot(dx / dt, dy / dt)

    def _convertMonoFields(self, prev_event, current_event):
        if self.isValidSample(current_event):
            self._convertPosToAngles(self, current_event)
            if prev_event:
                self._addVelocity(prev_event, current_event)

    def _convertToMonoAveraged(self, prev_event, current_event):
        mono_evt = []
        binoc_field_names = EventConstants.getClass(
            EventConstants.BINOCULAR_EYE_SAMPLE).CLASS_ATTRIBUTE_NAMES
        #print2err("binoc_field_names: ",len(binoc_field_names),"\n",binoc_field_names)
        status = current_event[binoc_field_names.index('status')]
        for field in self.io_event_fields:
            if field in binoc_field_names:
                mono_evt.append(current_event[binoc_field_names.index(field)])
            elif field == 'eye':
                mono_evt.append(LEFT_EYE)
            elif field.endswith('_type'):
                mono_evt.append(
                    int(current_event[binoc_field_names.index('left_%s' % (field))]))
            else:
                #print2err("binoc status: ",status)
                if status == 0:
                    lfv = float(
                        current_event[
                            binoc_field_names.index(
                                'left_%s' %
                                (field))])
                    rfv = float(
                        current_event[
                            binoc_field_names.index(
                                'right_%s' %
                                (field))])
                    mono_evt.append((lfv + rfv) / 2.0)
                elif status == 2:
                    mono_evt.append(
                        float(
                            current_event[
                                binoc_field_names.index(
                                    'left_%s' %
                                    (field))]))
                elif status == 20:
                    mono_evt.append(
                        float(
                            current_event[
                                binoc_field_names.index(
                                    'right_%s' %
                                    (field))]))
                elif status == 22:
                    # both eyes have missing data, so use data from left eye
                    # (does not really matter)
                    mono_evt.append(
                        float(
                            current_event[
                                binoc_field_names.index(
                                    'left_%s' %
                                    (field))]))
                else:
                    ValueError('Unknown Sample Status: %d' % (status))
        mono_evt[self.io_event_fields.index(
            'type')] = EventConstants.MONOCULAR_EYE_SAMPLE
        if self.isValidSample(mono_evt):
            self._convertPosToAngles(mono_evt)
            if prev_event:
                self._addVelocity(prev_event, mono_evt)
        return mono_evt

    def _binocSampleValidEyeData(self, sample):
        evt_status = sample[self.io_event_ix('status')]
        if evt_status == 0:
            # both eyes are valid
            return BOTH_EYE
        elif evt_status == 20:  # right eye data only
            return RIGHT_EYE
        elif evt_status == 2:  # left eye data only
            return LEFT_EYE
        elif evt_status == 22:  # both eye data missing
            return NO_EYE

    def createFixationStartEventArray(self, sample):
        return [sample[self.io_event_ix('experiment_id')],
                sample[self.io_event_ix('session_id')],
                sample[self.io_event_ix('device_id')],
                sample[self.io_event_ix('event_id')],
                EventConstants.FIXATION_START,
                sample[self.io_event_ix('device_time')],
                sample[self.io_event_ix('logged_time')],
                sample[self.io_event_ix('time')],
                0.0,
                0.0,
                0,
                sample[self.io_event_ix('eye')],
                sample[self.io_event_ix('gaze_x')],
                sample[self.io_event_ix('gaze_y')],
                0.0,
                sample[self.io_event_ix('angle_x')],
                sample[self.io_event_ix('angle_y')],
                # used to hold online x velocity threshold calculated for
                # sample
                sample[self.io_event_ix('raw_x')],
                # used to hold online y velocity threshold calculated for
                # sample
                sample[self.io_event_ix('raw_y')],
                sample[self.io_event_ix('pupil_measure1')],
                sample[self.io_event_ix('pupil_measure1_type')],
                0.0,
                0,
                0.0,
                0.0,
                sample[self.io_event_ix('velocity_x')],
                sample[self.io_event_ix('velocity_y')],
                sample[self.io_event_ix('velocity_xy')],
                sample[self.io_event_ix('status')]
                ]

    def createFixationEndEventArray(
            self,
            sample,
            existing_start_event,
            event_samples):
        evt_sample_array = np.asarray(event_samples)
        vx = self.io_event_ix('velocity_x')
        vy = self.io_event_ix('velocity_y')
        vxy = self.io_event_ix('velocity_xy')
        gx = self.io_event_ix('gaze_x')
        gy = self.io_event_ix('gaze_y')
        return [sample[self.io_event_ix('experiment_id')],
                sample[self.io_event_ix('session_id')],
                sample[self.io_event_ix('device_id')],
                sample[self.io_event_ix('event_id')],
                EventConstants.FIXATION_END,
                sample[self.io_event_ix('device_time')],
                sample[self.io_event_ix('logged_time')],
                sample[self.io_event_ix('time')],
                0.0,
                0.0,
                0,
                sample[self.io_event_ix('eye')],
                sample[self.io_event_ix(
                    'time')] - existing_start_event[self.io_event_ix('time')],
                existing_start_event[gx],
                existing_start_event[gy],
                0.0,
                existing_start_event[self.io_event_ix('angle_x')],
                existing_start_event[self.io_event_ix('angle_y')],
                # used to hold online x velocity threshold calculated for
                # sample
                existing_start_event[self.io_event_ix('raw_x')],
                # used to hold online y velocity threshold calculated for
                # sample
                existing_start_event[self.io_event_ix('raw_y')],
                existing_start_event[self.io_event_ix('pupil_measure1')],
                existing_start_event[self.io_event_ix('pupil_measure1_type')],
                0.0,
                0,
                0.0,
                0.0,
                existing_start_event[vx],
                existing_start_event[vy],
                existing_start_event[vxy],
                sample[gx],
                sample[gy],
                0.0,
                sample[self.io_event_ix('angle_x')],
                sample[self.io_event_ix('angle_y')],
                # used to hold online x velocity threshold calculated for
                # sample
                sample[self.io_event_ix('raw_x')],
                # used to hold online y velocity threshold calculated for
                # sample
                sample[self.io_event_ix('raw_y')],
                sample[self.io_event_ix('pupil_measure1')],
                sample[self.io_event_ix('pupil_measure1_type')],
                0.0,
                0,
                0.0,
                0.0,
                sample[vx],
                sample[vy],
                sample[vxy],
                evt_sample_array[:, gx].mean(),  # average_gaze_x,
                evt_sample_array[:, gy].mean(),  # average_gaze_y,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                evt_sample_array[
            :,
            self.io_event_ix('pupil_measure1')].mean(),
            # average_pupil_measure1,
            # average_pupil_measure1_type,
            sample[self.io_event_ix('pupil_measure1_type')],
            0.0,
            0.0,
            0.0,
            0.0,
            evt_sample_array[:, vx].mean(),  # average_velocity_x,
            evt_sample_array[:, vy].mean(),  # average_velocity_y,
            evt_sample_array[:, vxy].mean(),  # average_velocity_xy,
            evt_sample_array[:, vx].max(),  # peak_velocity_x,
            evt_sample_array[:, vy].max(),  # peak_velocity_y,
            evt_sample_array[:, vxy].max(),  # peak_velocity_xy,
            sample[self.io_event_ix('status')]
        ]

    ################### Saccade Event Types ##########################

    def createSaccadeStartEventArray(self, sample):
        return [sample[self.io_event_ix('experiment_id')],
                sample[self.io_event_ix('session_id')],
                sample[self.io_event_ix('device_id')],
                sample[self.io_event_ix('event_id')],
                EventConstants.SACCADE_START,
                sample[self.io_event_ix('device_time')],
                sample[self.io_event_ix('logged_time')],
                sample[self.io_event_ix('time')],
                0.0,
                0.0,
                0,
                sample[self.io_event_ix('eye')],
                sample[self.io_event_ix('gaze_x')],
                sample[self.io_event_ix('gaze_y')],
                0.0,
                sample[self.io_event_ix('angle_x')],
                sample[self.io_event_ix('angle_y')],
                # used to hold online x velocity threshold calculated for
                # sample
                sample[self.io_event_ix('raw_x')],
                # used to hold online y velocity threshold calculated for
                # sample
                sample[self.io_event_ix('raw_y')],
                sample[self.io_event_ix('pupil_measure1')],
                sample[self.io_event_ix('pupil_measure1_type')],
                0.0,
                0,
                0.0,
                0.0,
                sample[self.io_event_ix('velocity_x')],
                sample[self.io_event_ix('velocity_y')],
                sample[self.io_event_ix('velocity_xy')],
                sample[self.io_event_ix('status')]
                ]

    def createSaccadeEndEventArray(
            self,
            sample,
            existing_start_event,
            event_samples):
        evt_sample_array = np.asarray(event_samples)
        gx = self.io_event_ix('gaze_x')
        gy = self.io_event_ix('gaze_y')
        x1 = existing_start_event[gx]
        y1 = existing_start_event[gy]
        x2 = sample[gx]
        y2 = sample[gy]
        xDiff = x2 - x1
        yDiff = y2 - y1
        vx = self.io_event_ix('velocity_x')
        vy = self.io_event_ix('velocity_y')
        vxy = self.io_event_ix('velocity_xy')
        return [sample[self.io_event_ix('experiment_id')],
                sample[self.io_event_ix('session_id')],
                sample[self.io_event_ix('device_id')],
                sample[self.io_event_ix('event_id')],
                EventConstants.SACCADE_END,
                sample[self.io_event_ix('device_time')],
                sample[self.io_event_ix('logged_time')],
                sample[self.io_event_ix('time')],
                0.0,
                0.0,
                0,
                sample[self.io_event_ix('eye')],
                sample[self.io_event_ix(
                    'time')] - existing_start_event[self.io_event_ix('time')],
                xDiff,
                yDiff,
                np.rad2deg(np.arctan(yDiff, xDiff)),
                existing_start_event[gx],
                existing_start_event[gy],
                0.0,
                existing_start_event[self.io_event_ix('angle_x')],
                existing_start_event[self.io_event_ix('angle_y')],
                # used to hold online x velocity threshold calculated for
                # sample
                existing_start_event[self.io_event_ix('raw_x')],
                # used to hold online y velocity threshold calculated for
                # sample
                existing_start_event[self.io_event_ix('raw_y')],
                existing_start_event[self.io_event_ix('pupil_measure1')],
                existing_start_event[self.io_event_ix('pupil_measure1_type')],
                0.0,
                0,
                0.0,
                0.0,
                existing_start_event[vx],
                existing_start_event[vy],
                existing_start_event[vxy],
                sample[gx],
                sample[gy],
                0.0,
                sample[self.io_event_ix('angle_x')],
                sample[self.io_event_ix('angle_y')],
                # used to hold online x velocity threshold calculated for
                # sample
                sample[self.io_event_ix('raw_x')],
                # used to hold online y velocity threshold calculated for
                # sample
                sample[self.io_event_ix('raw_y')],
                sample[self.io_event_ix('pupil_measure1')],
                sample[self.io_event_ix('pupil_measure1_type')],
                0.0,
                0,
                0.0,
                0.0,
                sample[vx],
                sample[vy],
                sample[vxy],
                evt_sample_array[:, vx].mean(),  # average_velocity_x,
                evt_sample_array[:, vy].mean(),  # average_velocity_y,
                evt_sample_array[:, vxy].mean(),  # average_velocity_xy,
                evt_sample_array[:, vx].max(),  # peak_velocity_x,
                evt_sample_array[:, vy].max(),  # peak_velocity_y,
                evt_sample_array[:, vxy].max(),  # peak_velocity_xy,
                sample[self.io_event_ix('status')]
                ]

    ################### Blink Event Types ##########################

    def createBlinkStartEventArray(self, sample):
        return [sample[self.io_event_ix('experiment_id')],
                sample[self.io_event_ix('session_id')],
                sample[self.io_event_ix('device_id')],
                sample[self.io_event_ix('event_id')],
                EventConstants.BLINK_START,
                sample[self.io_event_ix('device_time')],
                sample[self.io_event_ix('logged_time')],
                sample[self.io_event_ix('time')],
                0.0,
                0.0,
                0,
                sample[self.io_event_ix('eye')],
                sample[self.io_event_ix('status')]
                ]

    def createBlinkEndEventArray(
            self,
            sample,
            existing_start_event,
            event_samples):
        return [
            sample[
                self.io_event_ix('experiment_id')], sample[
                self.io_event_ix('session_id')], sample[
                self.io_event_ix('device_id')], sample[
                    self.io_event_ix('event_id')], EventConstants.BLINK_END, sample[
                        self.io_event_ix('device_time')], sample[
                            self.io_event_ix('logged_time')], sample[
                                self.io_event_ix('time')], 0.0, 0.0, 0, sample[
                                    self.io_event_ix('eye')], sample[
                                        self.io_event_ix('time')] - existing_start_event[
                                            self.io_event_ix('time')], sample[
                                                self.io_event_ix('status')]]
