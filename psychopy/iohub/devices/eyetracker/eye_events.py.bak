"""
ioHub
ioHub Common Eye Tracker Interface
.. file: ioHub/devices/eyetracker/eye_events.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

from .. import DeviceEvent
from ...constants import EventConstants
from . import EyeTrackerDevice

##################### Eye Tracker Sample Stream Types ################################
#
class EyeTrackerEvent(DeviceEvent):
    PARENT_DEVICE=EyeTrackerDevice

class MonocularEyeSampleEvent(EyeTrackerEvent):
    """
    A MonocularEyeSampleEvent represents the eye position and eye attribute data collected from one frame or reading
    of an eye tracker device that is recoding from only one eye, or is recording from both eyes and averaging the
    binocular data. The eye sample class contains a large number of attributes to try and accommodate for
    the different field types different eye trackers report at a sample level. therefore it will not be
    uncommon for a given eye tracker implementation to provide a NOT_SUPPORTED_FIELD value for many attributes.

    Please refer to the implementation specific documentation for the eye tracker of interest for more details.
    """
    _newDataTypes = [
        ('eye', 'u1'),      # The eye type that the sample is from. Valid values are:
                            #   EyeTrackerConstants.LEFT_EYE
                            #   EyeTrackerConstants.RIGHT_EYE
                            #   EyeTrackerConstants.BINOCULAR
                            #   EyeTrackerConstants.BINOCULAR_AVERAGED
                            #   EyeTrackerConstants.SIMULATED_MONOCULAR
                            #   EyeTrackerConstants.SIMULATED_BINOCULAR

        ('gaze_x','f4'),    # The calibrated horizontal eye position on the calibration plane.
                            # This value is specified in Display Coordinate Type Units.

        ('gaze_y','f4'),    # The calibrated vertical eye position on the calibration plane.
                            # This value is specified in Display Coordinate Type Units.

        ('gaze_z','f4'),    # The calculated point of gaze in depth. Generally  This can only be
                            # provided if binocular reporting is being performed.

        ('eye_cam_x','f4'), # The x eye position in an eye trackers 3D coordinate space.
                            # Generally this field is only available by systems that are also
                            # calculating eye data using a 3D model of eye position relative to
                            # the eye camera(s) for example.

        ('eye_cam_y','f4'), # The y eye position in an eye trackers 3D coordinate space.
                            # Generally this field is only available by systems that are also
                            # calculating eye data using a 3D model of eye position relative to
                            # the eye camera(s) for example.

        ('eye_cam_z','f4'), # The z eye position in an eye trackers 3D coordinate space.
                            # Generally this field is only available by systems that are also
                            # calculating eye data using a 3D model of eye position relative to
                            # the eye camera(s) for example.

        ('angle_x','f4'),   # The horizontal angle of eye the relative to the head.

        ('angle_y','f4'),   # The vertical angle of eye the relative to the head.

        ('raw_x','f4'),     # The non-calibrated x position of the calculated eye 'center'
                            # on the camera sensor image,
                            # factoring in any corneal reflection adjustments.
                            # This is typically reported in some arbitrary unit space that
                            # often has sub-pixel resolution due to image processing techniques
                            # being applied.

        ('raw_y','f4'),     # The non-calibrated y position of the calculated eye 'center'
                            # on the camera sensor image,
                            # factoring in any corneal reflection adjustments.
                            # This is typically reported in some arbitrary unit space that
                            # often has sub-pixel resolution due to image processing techniques
                            # being applied.

        ('pupil_measure1','f4'), # A measure related to pupil size or diameter. Attribute
                                 # pupil_measure1_type defines what type the measure represents.

        ('pupil_measure1_type','u1'),   # Several possible pupil_measure types available:
                                        #       EyeTrackerConstants.PUPIL_AREA
                                        #       EyeTrackerConstants.PUPIL_DIAMETER
                                        #       EyeTrackerConstants.PUPIL_WIDTH
                                        #       EyeTrackerConstants.PUPIL_HEIGHT
                                        #       EyeTrackerConstants.PUPIL_MAJOR_AXIS
                                        #       EyeTrackerConstants.PUPIL_MINOR_AXIS

        ('pupil_measure2','f4'), # A measure related to pupil size or diameter. Attribute
                                 # pupil_measure2_type defines what type the measure represents.

        ('pupil_measure2_type','u1'),   # Several possible pupil_measure types are available:
                                        #       EyeTrackerConstants.PUPIL_AREA
                                        #       EyeTrackerConstants.PUPIL_DIAMETER
                                        #       EyeTrackerConstants.PUPIL_WIDTH
                                        #       EyeTrackerConstants.PUPIL_HEIGHT
                                        #       EyeTrackerConstants.PUPIL_MAJOR_AXIS
                                        #       EyeTrackerConstants.PUPIL_MINOR_AXIS

        ('ppd_x','f4'),     # Horizontal pixels per visual degree for this eye position
                            # as reported by the eye tracker.

        ('ppd_y','f4'),     # Vertical pixels per visual degree for this eye position
                            # as reported by the eye tracker.

        ('velocity_x','f4'), # Horizontal velocity of the eye at the time of the sample;
                             # as reported by the eye tracker.

        ('velocity_y','f4'), # Vertical velocity of the eye at the time of the sample;
                             # as reported by the eye tracker.

        ('velocity_xy','f4'), # 2D Velocity of the eye at the time of the sample;
                              # as reported by the eye tracker.

        ('status', 'u1')    # An available status word for the eye tracker sample.
                            # Meaning is completely tracker dependent.
                    ]
    EVENT_TYPE_ID=EventConstants.MONOCULAR_EYE_SAMPLE
    EVENT_TYPE_STRING="MONOCULAR_EYE_SAMPLE"
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING

    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self, *args, **kwargs):
        #: The eye type that the sample is from. Valid values are:
        #: EyeTrackerConstants.LEFT_EYE
        #: EyeTrackerConstants.RIGHT_EYE
        #: EyeTrackerConstants.BINOCULAR_AVERAGED
        self.eye=None   
        
        #: The calibrated horizontal eye position on the calibration plane.
        #: This value is specified in Display Coordinate Type Units.
        self.gaze_x=None

        #: The calibrated vertical eye position on the calibration plane.
        #: This value is specified in Display Coordinate Type Units.
        self.gaze_y=None

        #: The calculated point of gaze in depth. Generally  This can only be
        #: provided if binocular reporting is being performed.
        self.gaze_z=None
        
        #: The x eye position in an eye trackers 3D coordinate space.
        #: Generally this field is only available by systems that are also
        #: calculating eye data using a 3D model of eye position relative to
        #: the eye camera(s) for example.
        self.eye_cam_x=None 

        #: The y eye position in an eye trackers 3D coordinate space.
        #: Generally this field is only available by systems that are also
        #: calculating eye data using a 3D model of eye position relative to
        #: the eye camera(s) for example.
        self.eye_cam_y=None

        #: The z eye position in an eye trackers 3D coordinate space.
        #: Generally this field is only available by systems that are also
        #: calculating eye data using a 3D model of eye position relative to
        #: the eye camera(s) for example.
        self.eye_cam_z=None

        #: The horizontal angle of eye the relative to the head.
        self.angle_x=None

        #: The vertical angle of eye the relative to the head.
        self.angle_y=None

        #: The non-calibrated x position of the calculated eye 'center'
        #: on the camera sensor image,
        #: factoring in any corneal reflection adjustments.
        #: This is typically reported in some arbitrary unit space that
        #: often has sub-pixel resolution due to image processing techniques
        #: being applied.
        self.raw_x=None

        #: The non-calibrated y position of the calculated eye 'center'
        #: on the camera sensor image,
        #: factoring in any corneal reflection adjustments.
        #: This is typically reported in some arbitrary unit space that
        #: often has sub-pixel resolution due to image processing techniques
        #: being applied.
        self.raw_y=None

        #: A measure related to pupil size or diameter. The attribute
        #: pupil_measure1_type defines what type the measure represents.
        self.pupil_measure1=None

        #: The type of pupil size or shape information provided in the pupil_measure1
        #: attribute. Several possible pupil_measure types available:
        #: EyeTrackerConstants.PUPIL_AREA
        #: EyeTrackerConstants.PUPIL_DIAMETER
        #: EyeTrackerConstants.PUPIL_WIDTH
        #: EyeTrackerConstants.PUPIL_HEIGHT
        #: EyeTrackerConstants.PUPIL_MAJOR_AXIS
        #: EyeTrackerConstants.PUPIL_MINOR_AXIS
        self.pupil_measure1_type=None

        #: A second measure related to pupil size or diameter. The attribute
        #: pupil_measure2_type defines what type the measure represents.
        self.pupil_measure2=None

        #: The type of pupil size or shape information provided in the pupil_measure2
        #: attribute. Several possible pupil_measure types available:
        #: EyeTrackerConstants.PUPIL_AREA
        #: EyeTrackerConstants.PUPIL_DIAMETER
        #: EyeTrackerConstants.PUPIL_WIDTH
        #: EyeTrackerConstants.PUPIL_HEIGHT
        #: EyeTrackerConstants.PUPIL_MAJOR_AXIS
        #: EyeTrackerConstants.PUPIL_MINOR_AXIS
        self.pupil_measure2_type=None

        #: Horizontal pixels per visual degree for this eye position
        #: as reported by the eye tracker.
        self.ppd_x=None

        #: Vertical pixels per visual degree for this eye position
        #: as reported by the eye tracker.
        self.ppd_y=None

        #: Horizontal velocity of the eye at the time of the sample;
        #: as reported by the eye tracker.
        self.velocity_x=None

        #: Vertical velocity of the eye at the time of the sample;
        #: as reported by the eye tracker.
        self.velocity_y=None

        #: 2D Velocity of the eye at the time of the sample;
        #: as reported by the eye tracker.
        self.velocity_xy=None 

        #: An available status byte for the eye tracker sample.
        #: Meaning is completely tracker dependent.        
        self.status=None

        DeviceEvent.__init__(self, *args, **kwargs)

class BinocularEyeSampleEvent(EyeTrackerEvent):
    """
    The BinocularEyeSampleEvent event represents the eye position and eye attribute data collected from
    one frame or reading of an eye tracker device that is recording both eyes of a participant.
    The BinocularEyeSample class contains a large number of attributes to try and accommodate
    for the different field types different eye trackers report at a sample level.
    Therefore it will be common for a given eye tracker implementation to provide a
    NOT_SUPPORTED_FIELD value for many attributes.

    Please refer to the implementation specific documentation for the eye tracker
    of interest for more details.
    """
    _newDataTypes = [
                    ('left_gaze_x','f4'),
                    ('left_gaze_y','f4'),
                    ('left_gaze_z','f4'),
                    ('left_eye_cam_x','f4'),
                    ('left_eye_cam_y','f4'),
                    ('left_eye_cam_z','f4'),
                    ('left_angle_x','f4'),
                    ('left_angle_y','f4'),
                    ('left_raw_x','f4'),
                    ('left_raw_y','f4'),
                    ('left_pupil_measure1','f4'),
                    ('left_pupil_measure1_type','u1'),
                    ('left_pupil_measure2','f4'),
                    ('left_pupil_measure2_type','u1'),
                    ('left_ppd_x','f4'),
                    ('left_ppd_y','f4'),
                    ('left_velocity_x','f4'),
                    ('left_velocity_y','f4'),
                    ('left_velocity_xy','f4'),
                    ('right_gaze_x','f4'),
                    ('right_gaze_y','f4'),
                    ('right_gaze_z','f4'),
                    ('right_eye_cam_x','f4'),
                    ('right_eye_cam_y','f4'),
                    ('right_eye_cam_z','f4'),
                    ('right_angle_x','f4'),
                    ('right_angle_y','f4'),
                    ('right_raw_x','f4'),
                    ('right_raw_y','f4'),
                    ('right_pupil_measure1','f4'),
                    ('right_pupil_measure1_type','u1'),
                    ('right_pupil_measure2','f4'),
                    ('right_pupil_measure2_type','u1'),
                    ('right_ppd_x','f4'),
                    ('right_ppd_y','f4'),
                    ('right_velocity_x','f4'),
                    ('right_velocity_y','f4'),
                    ('right_velocity_xy','f4'),
                    ('status', 'u1')
                    ]

    EVENT_TYPE_ID=EventConstants.BINOCULAR_EYE_SAMPLE
    EVENT_TYPE_STRING="BINOCULAR_EYE_SAMPLE"
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING

    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self,*args,**kwargs):

        DeviceEvent.__init__(self,*args,**kwargs)

#
################### Fixation Event Types ##########################
# 
class FixationStartEvent(EyeTrackerEvent):
    """
    A FixationStartEvent is generated when the beginning of an eye fixation ( in very general terms,
    a period of relatively stable eye position ) is detected by the eye trackers sample parsing algorithms.
    Please refer to the implementation specific interface documentation for your eye tracker, and even the
    eye tracker's reference material itself, it you are looking for a more precise definition of how the eye
    tracker manufacturer has implemented their parser and how it determines when a FixationStartEvent occurs,
    assuming it supports this event type at all.
    """
    _newDataTypes = [
                    ('eye', 'u1'),      # The eye type that the fixation is from. Valid values are:
                                        #   EyeTrackerConstants.LEFT_EYE
                                        #   EyeTrackerConstants.RIGHT_EYE
                                        #   EyeTrackerConstants.BINOCULAR_AVERAGED
                                        #   EyeTrackerConstants.SIMULATED_MONOCULAR

                    ('gaze_x','f4'),    # The calibrated horizontal eye position on the calibration plane.
                                        # This value is specified in Display Coordinate Type Units.

                    ('gaze_y','f4'),    # The calibrated vertical eye position on the calibration plane.
                                        # This value is specified in Display Coordinate Type Units.

                    ('gaze_z','f4'),    # The calculated point of gaze in depth. Generally  This can only be
                                        # provided if binocular reporting is being performed.

                    ('angle_x','f4'),   # The horizontal angle of eye the relative to the head.

                    ('angle_y','f4'),   # The vertical angle of eye the relative to the head.

                    ('raw_x','f4'),     # The non-calibrated x position of the calculated eye 'center'
                                        # on the camera sensor image,
                                        # factoring in any corneal reflection adjustments.
                                        # This is typically reported in some arbitrary unit space that
                                        # often has sub-pixel resolution due to image processing techniques
                                        # being applied.

                    ('raw_y','f4'),     # The non-calibrated y position of the calculated eye 'center'
                                        # on the camera sensor image,
                                        # factoring in any corneal reflection adjustments.
                                        # This is typically reported in some arbitrary unit space that
                                        # often has sub-pixel resolution due to image processing techniques
                                        # being applied.

                    ('pupil_measure1','f4'), # A measure related to pupil size or diameter. Attribute
                                             # pupil_measure1_type defines what type the measure represents.

                    ('pupil_measure1_type','u1'),   # Several possible pupil_measure types available:
                                                    #       EyeTrackerConstants.PUPIL_AREA
                                                    #       EyeTrackerConstants.PUPIL_DIAMETER
                                                    #       EyeTrackerConstants.PUPIL_WIDTH
                                                    #       EyeTrackerConstants.PUPIL_HEIGHT
                                                    #       EyeTrackerConstants.PUPIL_MAJOR_AXIS
                                                    #       EyeTrackerConstants.PUPIL_MINOR_AXIS

                    ('pupil_measure2','f4'), # A measure related to pupil size or diameter. Attribute
                                             # pupil_measure2_type defines what type the measure represents.

                    ('pupil_measure2_type','u1'),   # Several possible pupil_measure types are available:
                                                    #       EyeTrackerConstants.PUPIL_AREA
                                                    #       EyeTrackerConstants.PUPIL_DIAMETER
                                                    #       EyeTrackerConstants.PUPIL_WIDTH
                                                    #       EyeTrackerConstants.PUPIL_HEIGHT
                                                    #       EyeTrackerConstants.PUPIL_MAJOR_AXIS
                                                    #       EyeTrackerConstants.PUPIL_MINOR_AXIS

                    ('ppd_x','f4'),     # Horizontal pixels per visual degree for this eye position
                                        # as reported by the eye tracker.

                    ('ppd_y','f4'),     # Vertical pixels per visual degree for this eye position
                                        # as reported by the eye tracker.

                    ('velocity_x','f4'), # Horizontal velocity of the eye at the time of the fixation start sample;
                                         # as reported by the eye tracker.

                    ('velocity_y','f4'), # Vertical velocity of the eye at the time of the fixation start sample;
                                         # as reported by the eye tracker.

                    ('velocity_xy','f4'), # 2D Velocity of the eye at the time of the fixation start sample;
                                          # as reported by the eye tracker.

                    ('status', 'u1')    # An available status word for the eye tracker fixation start event.
                                        # Meaning is completely tracker dependent.
                    ]

    EVENT_TYPE_ID=EventConstants.FIXATION_START
    EVENT_TYPE_STRING=EventConstants.getName(EVENT_TYPE_ID)
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING

    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self, *args, **kwargs):
        DeviceEvent.__init__(self, *args, **kwargs)

       
class FixationEndEvent(EyeTrackerEvent):
    # 58 fields
    _newDataTypes = [
                    ('eye', 'u1'),
                    ('duration','f4'),
                    ('start_gaze_x','f4'),
                    ('start_gaze_y','f4'),
                    ('start_gaze_z','f4'),
                    ('start_angle_x','f4'),
                    ('start_angle_y','f4'),
                    ('start_raw_x','f4'),
                    ('start_raw_y','f4'),
                    ('start_pupil_measure1','f4'),
                    ('start_pupil_measure1_type','u1'),
                    ('start_pupil_measure2','f4'),
                    ('start_pupil_measure2_type','u1'),
                    ('start_ppd_x','f4'),
                    ('start_ppd_y','f4'),
                    ('start_velocity_x','f4'),
                    ('start_velocity_y','f4'),
                    ('start_velocity_xy','f4'),
                    ('end_gaze_x','f4'),
                    ('end_gaze_y','f4'),
                    ('end_gaze_z','f4'),
                    ('end_angle_x','f4'),
                    ('end_angle_y','f4'),
                    ('end_raw_x','f4'),
                    ('end_raw_y','f4'),
                    ('end_pupil_measure1','f4'),
                    ('end_pupil_measure1_type','u1'),
                    ('end_pupil_measure2','f4'),
                    ('end_pupil_measure2_type','u1'),
                    ('end_ppd_x','f4'),
                    ('end_ppd_y','f4'),
                    ('end_velocity_x','f4'),
                    ('end_velocity_y','f4'),
                    ('end_velocity_xy','f4'),
                    ('average_gaze_x','f4'),
                    ('average_gaze_y','f4'),
                    ('average_gaze_z','f4'),
                    ('average_angle_x','f4'),
                    ('average_angle_y','f4'),
                    ('average_raw_x','f4'),
                    ('average_raw_y','f4'),
                    ('average_pupil_measure1','f4'),
                    ('average_pupil_measure1_type','u1'),
                    ('average_pupil_measure2','f4'),
                    ('average_pupil_measure2_type','u1'),
                    ('average_ppd_x','f4'),
                    ('average_ppd_y','f4'),
                    ('average_velocity_x','f4'),
                    ('average_velocity_y','f4'),
                    ('average_velocity_xy','f4'),
                    ('peak_velocity_x','f4'),
                    ('peak_velocity_y','f4'),
                    ('peak_velocity_xy','f4'),
                    ('status','u1')
                    ]

    EVENT_TYPE_ID=EventConstants.FIXATION_END
    EVENT_TYPE_STRING=EventConstants.getName(EVENT_TYPE_ID)
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING

    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self,*args,**kwargs):
        DeviceEvent.__init__(self,*args,**kwargs)
 

################### Saccade Event Types ##########################
#         
class SaccadeStartEvent(FixationStartEvent):

    EVENT_TYPE_ID=EventConstants.SACCADE_START
    EVENT_TYPE_STRING=EventConstants.getName(EVENT_TYPE_ID)
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING
    __slots__=[]
    def __init__(self,*args,**kwargs):
        FixationStartEvent.__init__(self,*args,**kwargs)

class SaccadeEndEvent(EyeTrackerEvent):
    _newDataTypes = [
                    ('eye', 'u1'),
                    ('duration','f4'),
                    ('amplitude_x','f4'),
                    ('amplitude_y','f4'),
                    ('angle', 'f4'),
                    ('start_gaze_x','f4'),
                    ('start_gaze_y','f4'),
                    ('start_gaze_z','f4'),
                    ('start_angle_x','f4'),
                    ('start_angle_y','f4'),
                    ('start_raw_x','f4'),
                    ('start_raw_y','f4'),
                    ('start_pupil_measure1','f4'),
                    ('start_pupil_measure1_type','u1'),
                    ('start_pupil_measure2','f4'),
                    ('start_pupil_measure2_type','f4'),
                    ('start_ppd_x','f4'),
                    ('start_ppd_y','f4'),
                    ('start_velocity_x','f4'),
                    ('start_velocity_y','f4'),
                    ('start_velocity_xy','f4'),
                    ('end_gaze_x','f4'),
                    ('end_gaze_y','f4'),
                    ('end_gaze_z','f4'),
                    ('end_angle_x','f4'),
                    ('end_angle_y','f4'),
                    ('end_raw_x','f4'),
                    ('end_raw_y','f4'),
                    ('end_pupil_measure1','f4'),
                    ('end_pupil_measure1_type','u1'),
                    ('end_pupil_measure2','f4'),
                    ('end_pupil_measure2_type','u1'),
                    ('end_ppd_x','f4'),
                    ('end_ppd_y','f4'),
                    ('end_velocity_x','f4'),
                    ('end_velocity_y','f4'),
                    ('end_velocity_xy','f4'),
                    ('average_velocity_x','f4'),
                    ('average_velocity_y','f4'),
                    ('average_velocity_xy','f4'),
                    ('peak_velocity_x','f4'),
                    ('peak_velocity_y','f4'),
                    ('peak_velocity_xy','f4'),
                    ('status','u1')
                    ]

    EVENT_TYPE_ID=EventConstants.SACCADE_END
    EVENT_TYPE_STRING=EventConstants.getName(EVENT_TYPE_ID)
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING

    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self,*args,**kwargs):
        DeviceEvent.__init__(self,*args,**kwargs)


################### Blink Event Types ##########################
# 
class BlinkStartEvent(EyeTrackerEvent):
    _newDataTypes = [
                    ('eye', 'u1'),      # The eye type that the fixation is from. Valid values are:
                                        #   EyeTrackerConstants.LEFT_EYE
                                        #   EyeTrackerConstants.RIGHT_EYE
                                        #   EyeTrackerConstants.BINOCULAR_AVERAGED
                                        #   EyeTrackerConstants.SIMULATED_MONOCULAR


                    ('status', 'u1')    # An available status byte for the eye tracker blink start event.
                                        # Meaning is completely tracker dependent.
                    ]
    __slots__=[e[0] for e in _newDataTypes]

    EVENT_TYPE_ID=EventConstants.BLINK_START
    EVENT_TYPE_STRING=EventConstants.getName(EVENT_TYPE_ID)
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING

    def __init__(self,*args,**kwargs):
        DeviceEvent.__init__(self,*args,**kwargs)

class BlinkEndEvent(EyeTrackerEvent):
    _newDataTypes = [
                            ('eye', 'u1'),       # The eye type that the fixation is from. Valid values are:
                                                #   EyeTrackerConstants.LEFT_EYE
                                                #   EyeTrackerConstants.RIGHT_EYE
                                                #   EyeTrackerConstants.BINOCULAR_AVERAGED
                                                #   EyeTrackerConstants.SIMULATED_MONOCULAR


                        ('duration','f4'),  # The duration of the blink event.

                        ('status', 'u1')    # An available status byte for the eye tracker blink start event.
                                            # Meaning is completely tracker dependent.
                    ]

    EVENT_TYPE_ID=EventConstants.BLINK_END
    EVENT_TYPE_STRING=EventConstants.getName(EVENT_TYPE_ID)
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING

    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self,*args,**kwargs):
        DeviceEvent.__init__(self,*args,**kwargs)
