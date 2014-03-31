# -*- coding: utf-8 -*-
from __future__ import division
"""
ioHub
.. file: iohub/util/targetpositionsequence.py

Copyright (C) 2012-2014 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com>
.. fileauthor:: Sol Simpson <sol@isolver-software.com>

This module contains functionality useful for displaying an eye tracker
independent validation process that tests the accuracy of the eye tracker
being used. The functionality could also be used to drive calibration graphics
for eye tracker models that require psychopy to perform the stimulus
presentation during calibration.

To use this module, the following high level steps are generally preformed:
* Create an instance of TargetStim, specifying the fixation target appearance.
* Create an instance of PositionGrid, which defines target position information.
* Create a TargetPosSequenceStim instance, providing the TargetStim and
  PositionGrid objects created, as well as the Trigger's which should be used
  to transition from one target position to another during the sequence of
  target graphics presentation and the defined positions.
* Use TargetPosSequenceStim.display() to run the full presentation procedure.
* Use TargetPosSequenceStim.targetdata to access information about each target
  position displayed and the events collected during the display duration for
  each position.
"""
from ... import visual, core
from . import win32MessagePump, Trigger, TimeTrigger, DeviceEventTrigger, OrderedDict
from ..constants import EventConstants
from .. import ioHubConnection
from weakref import proxy
import numpy as np
from time import sleep
import os, sys
from PIL import Image
getTime = core.getTime

class TargetStim(object):
    """
    TargetStim creates a target graphic that can be used during a sequential
    fixation task. The stim consists of two psychopy circle stim, one is
    used to draw the outer edge of the target and the target body fill.
    The second is used to draw a dot in the center of the larger circle.
    """
    def __init__(self,
                 win,
                 radius=None,       # The outer radius of the target.
                 fillcolor=None,    # The color used to fill the target body.
                 edgecolor=None,    # The color for the edge around the target.
                 edgewidth=None,    # The thickness of the target outer edge.
                 dotcolor=None,     # The color of the central target dot.
                 dotradius=None,    # The radius to use for the target dot.
                 units=None,        # The psychopy unit type of any size values.
                 colorspace=None,   # The psychopy color space of any colors.
                 opacity=1.0,       # The transparency of the target (0.0 - 1.0)
                 contrast=1.0       # The contrast of the target stim.
                 ):
        self.win = proxy(win)
        self.stim = []
        self.radius=radius
        outer = visual.Circle(self.win,
                            radius=radius,
                            fillColor=fillcolor,
                            lineColor=edgecolor,
                            lineWidth=edgewidth,
                            edges=int(np.pi*radius),
                            units=units,
                            lineColorSpace=colorspace,
                            fillColorSpace=colorspace,
                            opacity=opacity,
                            contrast=contrast,
                            interpolate=True,
                            autoLog=False)
        self.stim.append(outer)

        if dotcolor and dotcolor != fillcolor:
            centerdot = visual.Circle(self.win,
                                radius=dotradius,
                                fillColor=dotcolor,
                                lineColor=dotcolor,
                                lineWidth=0.0,
                                edges=int(np.pi*dotradius),
                                interpolate=True,
                                units=units,
                                lineColorSpace=colorspace,
                                fillColorSpace=colorspace,
                                opacity=opacity,
                                contrast=contrast,
                                autoLog=False)
            self.stim.append(centerdot)

    def setRadius(self, r):
        """
        Update the radius of the target stim.
        """
        self.stim[0].setRadius(r)

    def setPos(self, pos):
        """
        Set the position of the target stim. The target center will be drawn at
        the position given.
        """
        for s in self.stim:
            s.setPos(pos)

    def draw(self):
        """
        Draw the Target stim. (this simply calls the draw method of the
        psychopy stim used, in the correct order).
        """
        for s in self.stim:
            s.draw()

class PositionGrid(object):
    """
    PositionGrid provides a flexible way to generate a set of x,y position
    values within the boundaries of the psychopy window object provided.

    The class provides a set of arguments that represent commonly needed
    constrains when creating a position list for a sequential fixation type
    task. This allows for a wide variety of position lists to be generated.

    PositionGrid supports the len() function, and returns the number of
    positions generated based on the supplied parameters. If repeatfirstpos
    is true, len(posgrid) == number of unique positions + 1 (a repeat of the
    first position value).

    PositionGrid is a generator, so the normal way to access the positions from
    the class is to use a for loop or with statement:

    posgrid = PositionGrid(....)
    for pos in posgrid:
        # do something cool with the pos

    """
    def __init__(self,
                winSize=None,       # Window width,height bounds.
                shape=None,         # Defines the number of columns and rows of
                                    # positions needed. If shape is an array of
                                    # two elements, it defines the col,row shape
                                    # for position layout. Position count will
                                    # equal rows*cols. If shape is a single
                                    # int, the position grid col,row shape will
                                    # be shape x shape.
                posCount=None,      # Defines the number of positions to
                                    # without any col,row position constraint.
                leftMargin=None,    # Specify the minimum valid horz position.
                rightMargin=None,   # Limit horz positions to be < max horz
                                    # position minus rightMargin.
                topMargin=None,     # Limit vert positions to be < max vert
                                    # position minus topMargin.
                bottomMargin=None,  # Specify the minimum valid vert position.
                scale=1.0,          # Scale can be one or two numbers, each
                                    # between 0.0 and 1.0. If a tuple is
                                    # provided, it represents the horz, vert
                                    # scale to be applied to window width,
                                    # height. If a single number is
                                    # given, the same scale will be applied to
                                    # both window width and height. The scaled
                                    # window size is centered on the original
                                    # window size to define valid position area.
                posList=None,       # Provide an existing list of (x,y)
                                    # positions. If posList is provided, the
                                    # shape, posCount, margin and scale arg's
                                    # are ignored.
                noiseStd=None,      # Add a random shift to each position based
                                    # on a normal distribution with mean = 0.0
                                    # and sigma equal to noiseStd. Specify
                                    # value based on units being used.
                firstposindex=0,    # Specify which position in the position
                                    # list should be displayed first. This
                                    # position is not effected by randomization.
                repeatfirstpos=True # If the first position in the list should
                                    # be provided as the last position as well,
                                    # set to True. In this case, the number of
                                    # positions returned will be position
                                    # count + 1. False indicated the first
                                    # position should not be repeated.
                ):

        self.posIndex = 0
        self.positions = None
        self.posOffsets=None

        self.winSize=winSize
        self.firstposindex=firstposindex

        self.repeatfirstpos=repeatfirstpos

        self.horzStd, self.vertStd = None, None
        if noiseStd:
            if hasattr(noiseStd, '__len__'):
                self.horzStd, self.vertStd = noiseStd
            else:
                self.horzStd, self.vertStd = noiseStd, noiseStd

        horzScale, vertScale = None, None
        if scale:
            if hasattr(scale, '__len__'):
                horzScale, vertScale = scale
            else:
                horzScale, vertScale = scale, scale

        rowCount, colCount = None, None
        if shape:
            if hasattr(shape, '__len__'):
                colCount, rowCount = shape
            else:
                rowCount, colCount = shape, shape

        if posList:
            if (len(posList) == 2 and
            len(posList[0]) != 2 and
            len(posList[0]) == len(posList[1]) ):
                #positions were provided in ((x1,x2,..,xn),(y1,y2,..,yn)) format
                self.positions = np.column_stack((posList[0],
                                                posList[1]))
            elif len(posList[0]) == 2:
                self.positions = np.asarray(posList)
            else:
                raise ValueError('PositionGrid posList kwarg must be in'
                                 ' ((x1,y1),(x2,y2),..,(xn,yn))'
                                 ' or ((x1,x2,..,xn),(y1,y2,..,yn)) format')

        if self.positions is None and (posCount or (rowCount and colCount)):
            # create posCount random grid positions within winSize
            if winSize is not None:
                pixw, pixh = winSize
                xmin = 0.0
                xmax = 1.0
                ymin = 0.0
                ymax = 1.0

                if leftMargin:
                    if leftMargin < pixw:
                        xmin = leftMargin/pixw
                    else:
                        raise ValueError('PositionGrid leftMargin kwarg must be'
                                     ' < winSize[0]')
                if rightMargin:
                    if rightMargin < pixw:
                        xmax = 1.0-rightMargin/pixw
                    else:
                        raise ValueError('PositionGrid rightMargin kwarg must be'
                                     ' < winSize[0]')
                if topMargin:
                    if topMargin < pixh:
                        ymax = 1.0-topMargin/pixh
                    else:
                        raise ValueError('PositionGrid topMargin kwarg must be'
                                     ' < winSize[1]')
                if bottomMargin:
                    if bottomMargin < pixh:
                        ymin = bottomMargin/pixh
                    else:
                        raise ValueError('PositionGrid bottomMargin kwarg must be'
                                     ' < winSize[1]')
                        ymin = bottomMargin/pixh

                if horzScale:
                    if 0.0 < horzScale <= 1.0:
                        xmin += (1.0-horzScale)/2.0
                        xmax -= (1.0-horzScale)/2.0
                else:
                    raise ValueError('PositionGrid horzScale kwarg must be'
                                     ' 0.0 > horzScale <= 1.0')

                if vertScale:
                    if 0.0 < vertScale <= 1.0:
                        ymin += (1.0-vertScale)/2.0
                        ymax -= (1.0-vertScale)/2.0
                else:
                    raise ValueError('PositionGrid vertScale kwarg must be'
                                     ' 0.0 > vertScale <= 1.0')
                if posCount:
                    colCount=int(np.sqrt(posCount))
                    rowCount=colCount
                    xps = np.random.uniform(xmin, xmax, colCount)*pixw-pixw/2.0
                    yps = np.random.uniform(ymin, ymax, rowCount)*pixh-pixh/2.0
                else:
                    xps = np.linspace(xmin, xmax, colCount)*pixw-pixw/2.0
                    yps = np.linspace(ymin, ymax, rowCount)*pixh-pixh/2.0

                xps, yps = np.meshgrid(xps, yps)
                self.positions = np.column_stack((xps.flatten(), yps.flatten()))

            else:
                raise ValueError('PositionGrid posCount kwarg also requires'
                                 'winSize to be provided.')

        if self.positions is None:
            raise AttributeError('PositionGrid is unable to generate positions'
                                 'based on the provided kwargs.')

        if self.firstposindex:
            fpos = self.positions[self.firstposindex]
            self.positions = np.delete(self.positions, self.firstposindex, 0)
            self.positions = np.insert(self.positions, 0, fpos, 0)

        self._generatePosOffsets()

    def __len__(self):
        if self.repeatfirstpos:
            return len(self.positions)+1
        else:
            return len(self.positions)

    def plot(self, **kwargs):
        """
        Uses Matplotlib to create a figure illustrating the screen positions,
        and presentation order, for the PositionGrid's current state.

        **kwargs will be directly passed to pyplot.scatter() as kwargs.
        """
        from matplotlib import pyplot as pl
        x = [p[0] for p in self]
        y = [p[1] for p in self]
        pixw , pixh = self.winSize
        pl.clf()
        pl.scatter(x, y, **kwargs)
        pl.xlim(-pixw/2, pixw/2)
        pl.ylim(-pixh/2, pixh/2)
        for i in range(len(x)):
            pl.text(x[i], y[i], str(i), size=11, horizontalalignment='center',
                    verticalalignment='center')
        pl.xlabel("Horizontal Target Position")
        pl.ylabel("Vertical Target Position")
        pl.title("PositionGrid Generated Screen Locations\n(Point Number is List Index)")
        pl.show()

    def randomize(self):
        """
        Randomize the positions within the position list. If a first position
        index was been provided, randomization only occurs for positions[1:].

        This can be called multiple times if the same position list is being used
        repeatedly and a random presentation order is needed.

        Each time randomize() is called, if noiseStd is != 0, a new set of
        normally distributed offsets are created for the target positions.
        """
        if not self.firstposindex:
            np.random.shuffle(self.positions)
        else:
            firstpos = self.positions[0]
            self.positions = np.delete(self.positions, 0, 0)
            np.random.shuffle(self.positions)
            self.positions = np.insert(self.positions, 0, firstpos, 0)
        self._generatePosOffsets()

    def _generatePosOffsets(self):
        """
        Create a new set of position displayment 'noise' based on the noiseStd
        value given when the object was initialized.
        """
        horzPosOffsetList = np.zeros((len(self), 1))
        if self.horzStd:
            horzPosOffsetList = np.random.normal(0.0, self.horzStd,
                                                 len(self))
        vertPosOffsetList = np.zeros((len(self), 1))
        if self.vertStd:
            vertPosOffsetList = np.random.normal(0.0, self.vertStd,
                                                 len(self))
        self.posOffsets = np.column_stack((vertPosOffsetList, horzPosOffsetList))

    def __iter__(self):
        return self

    # Python 3 compatibility
    def __next__(self):
        return self.next()

    def next(self):
        """
        Returns the next position in the list. Usually this method is not
        called directly. Instead, positions are accessed by iterating over
        the PositionGrid object.

        pos = PositionGrid(....)

        for p in pos:
            # do something cool with it
            pass
        """
        if self.posIndex < len(self.positions):
            pos = self.positions[self.posIndex]+self.posOffsets[self.posIndex]
            self.posIndex = self.posIndex+1
            return pos
        elif self.repeatfirstpos and self.posIndex == len(self.positions):
            pos = self.positions[0]+self.posOffsets[0]
            self.posIndex = self.posIndex+1
            return pos
        else:
            self.posIndex = 0
            raise StopIteration()


class TargetPosSequenceStim(object):
    """
    TargetPosSequenceStim combines an instance of a Target stim and an instance
    of a PositionGrid to create everything needed to present the target at
    each position returned by the PositionGrid instance within the psychopy
    window used to create the Target stim. The target is presented at each
    position sequentially.

    By providing keyword arguments to the TargetPosSequenceStim.display(...)
    method, position animation between target positions, and target stim
    expansion and / or contraction transitions are possible.

    psychopy.iohub.Trigger based classes are used to define the criteria used to
    start displaying the next target position graphics. By providing a list
    of a TimerTrigger and a set of DeviceEventTriggers, complex criteria
    for target position pacing can be easily defined for use during the display
    period.

    iohub devices can be provided in the storeeventsfor keyword argument.
    Events which occur during each target position presentation period are
    stored and are available at the end of the display() period, grouped by
    position index and device event types.
    """
    TARGET_STATIONARY=1
    TARGET_MOVING=2
    TARGET_EXPANDING=4
    TARGET_CONTRACTING=8

    # Experiment Message text field types and tokens
    #
    message_types=dict(
        # position_count
        BEGIN_SEQUENCE = ("BEGIN_SEQUENCE", '', int),        
        # position_count
        DONE_SEQUENCE = ("DONE_SEQUENCE", '', int),        
        # event_type_id event_time
        NEXT_POS_TRIG = ("NEXT_POS_TRIG", '', int,float),
        # position_count from_x,from_y to_x,to_y         
        START_DRAW = ("START_DRAW", ',', int, float, float, float, float),
        # position_count from_x,from_y to_x,to_y         
        SYNCTIME = ("SYNCTIME", ',', int, float, float, float, float),        
        # current_radius original_radius         
        EXPAND_SIZE = ("EXPAND_SIZE", '', float, float),
        # current_radius original_radius         
        CONTRACT_SIZE = ("CONTRACT_SIZE", '', float, float),
        # current_x,current_y         
        POS_UPDATE = ("POS_UPDATE", ',', float, float),
        # final_x,final_y         
        TARGET_POS = ("TARGET_POS", ',', float, float)
        )    
    max_msg_type_length=max([len(s) for s in message_types.keys()])

    binocular_sample_message_element=[
                    ('targ_pos_ix',np.int),
                    ('last_msg_time',np.float32),
                    ('last_msg_type',np.str, max_msg_type_length),
                    ('next_msg_time',np.float32),
                    ('next_msg_type',np.str, max_msg_type_length),
                    ('targ_pos_x',np.float32),
                    ('targ_pos_y',np.float32),
                    ('targ_state',np.int),
                    ('eye_time',np.float32),
                    ('eye_status',np.int),
                    ('left_eye_x',np.float32),
                    ('left_eye_y',np.float32),
                    ('left_pupil_size',np.float32),
                    ('right_eye_x',np.float32),
                    ('right_eye_y',np.float32),
                    ('right_pupil_size',np.float32)
                   ]
                   
    monocular_sample_message_element=[
                    ('targ_pos_ix',np.int),
                    ('last_msg_time',np.float32),
                    ('last_msg_type',np.str, max_msg_type_length),
                    ('next_msg_time',np.float32),
                    ('next_msg_type',np.str, max_msg_type_length),
                    ('targ_pos_x',np.float32),
                    ('targ_pos_y',np.float32),
                    ('targ_state',np.int),
                    ('eye_time',np.float32),
                    ('eye_status',np.int),
                    ('eye_x',np.float32),
                    ('eye_y',np.float32),
                    ('pupil_size',np.float32)
                   ]
                           
    def __init__(self,
                 target,            # The TargetStim instance to use.
                 positions,         # The PositionGrid instance to use.
                 background=None,   # Window background color to use (if any).
                 storeeventsfor=[], # List of iohub device objects to track
                                    # events for.
                 triggers=None,     # The triggers to use for controlling target
                                    # position progression.
                 msgcategory="",     # As the display() process is preformed,
                                    # iohub experiment messages are generated
                                    # providing information on the state of the
                                    # target and position. msgcategory can be
                                    # used to define the category string to
                                    # assign to each message.
                 io=None            # The ioHubConnection instance to use.
                ):
        self.win = target.win
        self.target = target
        self.background = background
        self.positions = positions
        self.storeevents=storeeventsfor
        self.msgcategory=msgcategory
        
        if io is None:
            io=ioHubConnection.getActiveConnection()
        self.io=io

        # If storeevents is True, targetdata will be a list of dict's.
        # Each dict, among other things, contains all ioHub events that occurred
        # from when a target was first presented at a position, to when the
        # the wait period completed for that position.
        #
        self.targetdata=[]
        self.triggers = None

        # Handle different valid trigger object types
        if isinstance(triggers, (list, tuple)):
            # Support is provided for a list of Trigger objects or a list of
            # strings.
            t1 = triggers[0]
            if isinstance(t1, basestring):
                # triggers is a list of strings, so try and create a list of
                # DeviceEventTrigger's using keyboard device, KEYBOARD_CHAR
                # event type, and the triggers list elements each as the
                # event.key.
                kbtriggers=[]
                kbdevice = io.getDevice('keyboard')
                KEYBOARD_CHAR = EventConstants.KEYBOARD_CHAR
                for c in triggers:
                    kbtriggers.append(DeviceEventTrigger(kbdevice,
                                      event_type=KEYBOARD_CHAR,
                                      event_attribute_conditions={'key':
                                                                  c}
                                                         )
                                      )
                    self.triggers = kbtriggers
            else:
                # Assume triggers is a list of Trigger objects
                self.triggers = triggers
        elif isinstance(triggers, (int, float, long)):
            # triggers is a number, so assume a TimeTrigger is wanted where
            # the delay == triggers. start time will be the fliptime of the
            # last update for drawing to the new target position.
            self.triggers = (TimeTrigger(start_time=None, delay=triggers),)
        elif isinstance(triggers, basestring):
            # triggers is a string, so try and create a
            # DeviceEventTrigger using keyboard device, KEYBOARD_CHAR
            # event type, and triggers as the event.key.
            self.triggers = (DeviceEventTrigger(io.getDevice('keyboard'),
                                event_type=EventConstants.KEYBOARD_CHAR,
                                event_attribute_conditions={'key':
                                                                triggers}),)
        elif isinstance(triggers, Trigger):
            # A single Trigger object was provided
            self.triggers = (triggers,)
        else:
            raise ValueError("The triggers kwarg could not be understood as a "
                             "valid triggers input value.")

    def getIO(self):
        """
        Get the active ioHubConnection instance.
        """
        return self.io

    def _draw(self):
        """
        Fill the window with the specified background color and draw the target
        stim.
        """
        if self.background:
            self.background.draw()
        self.target.draw()

    def _animateTarget(self, topos, frompos, **kwargs):
        """
        Internal method.

        Any logic related to drawing the target at the new screen position,
        including any intermediate animation effects, is done here.

        Return the flip time when the target was first drawn at the newpos
        location.
        """
        io = self.getIO()
        if frompos is not None:
            velocity = kwargs.get('velocity')
            if velocity:
                starttime = getTime()
                a, b = np.abs(topos-frompos)**2
                duration = np.sqrt(a+b)/velocity
                arrivetime = duration+starttime
                fliptime = starttime
                while fliptime < arrivetime:
                    mu = (fliptime-starttime)/duration
                    tpos=frompos*(1.0-mu)+topos*mu
                    self.target.setPos(frompos*(1.0-mu)+topos*mu)
                    self._draw()
                    fliptime = self.win.flip()
                    io.sendMessageEvent("POS_UPDATE %.2f,%.2f"%(
                                        tpos[0], tpos[1]), self.msgcategory,
                                        sec_time=fliptime)
                    self._addDeviceEvents()

        self.target.setPos(topos)
        self._draw()
        fliptime = self.win.flip()
        io.sendMessageEvent("TARGET_POS %.2f,%.2f"%(topos[0], topos[1]),
                            self.msgcategory, sec_time=fliptime)
        self._addDeviceEvents()

        expandedscale=kwargs.get('expandedscale')
        expansionduration=kwargs.get('expansionduration')
        contractionduration=kwargs.get('contractionduration')

        initialradius=self.target.radius
        if expandedscale:
            expandedradius=self.target.radius*expandedscale

            if expansionduration:
                starttime = fliptime
                expandedtime = fliptime+expansionduration
                while fliptime < expandedtime:
                    mu = (fliptime-starttime)/expansionduration
                    cradius=initialradius*(1.0-mu)+expandedradius*mu
                    self.target.setRadius(cradius)
                    self._draw()
                    fliptime = self.win.flip()
                    io.sendMessageEvent("EXPAND_SIZE %.2f %.2f"%(
                                        cradius, initialradius),
                                        self.msgcategory, sec_time=fliptime)
                    self._addDeviceEvents()

            if contractionduration:
                starttime = fliptime
                contractedtime = fliptime+contractionduration
                while fliptime < contractedtime:
                    mu = (fliptime-starttime)/contractionduration
                    cradius=expandedradius*(1.0-mu)+initialradius*mu
                    self.target.setRadius(cradius)
                    self._draw()
                    fliptime = self.win.flip()
                    io.sendMessageEvent("CONTRACT_SIZE %.2f %.2f"%(
                                        cradius, initialradius),
                                        self.msgcategory, sec_time=fliptime)
                    self._addDeviceEvents()

        self.target.setRadius(initialradius)
        return fliptime

    def moveTo(self, topos, frompos, **kwargs):
        """
        Indicates that the target should be moved frompos to topos.
        If a PositionGrid has been provided, moveTo should not be called
        directly. Instead, use the display() method to start the full target
        position presentation sequence.
        """
        io = self.getIO()
        fpx, fpy = -1, -1
        if frompos is not None:
            fpx, fpy = frompos[0], frompos[1]
        io.sendMessageEvent("START_DRAW %d %.2f,%.2f %.2f,%.2f"%(
            self.positions.posIndex, fpx, fpy, 
            topos[0], topos[1]), self.msgcategory)

        fliptime=self._animateTarget(topos, frompos, **kwargs)

        io.sendMessageEvent("SYNCTIME %d %.2f,%.2f %.2f,%.2f"%(
            self.positions.posIndex, fpx, fpy, 
            topos[0], topos[1]), self.msgcategory, sec_time=fliptime)

        # wait for trigger to fire
        last_pump_time=fliptime
        while not self._hasTriggerFired(start_time=fliptime):
            if getTime() - last_pump_time >= 0.250:
                win32MessagePump()
                last_pump_time = getTime()
            sleep(0.001)
            
    def _hasTriggerFired(self, **kwargs):
        """
        Used internally to know when one of the triggers has occurred and the
        target should move to the next target position.
        """
        # wait for trigger to fire
        triggered = None
        for trig in self.triggers:
            if trig.triggered(**kwargs):
                triggered = trig
                break
        self._addDeviceEvents(trig.clearEventHistory(True))
        if triggered:
            # assume it was a timer trigger,so use 255 as 'event type'
            event_type_id=255
            trig_evt=triggered.getTriggeringEvent()
            if hasattr(trig_evt,'type'):
                # actually it was a device event trigger
                event_type_id=trig_evt.type
            # get time trigger of trigger event
            event_time = triggered.getTriggeringTime()
            self.getIO().sendMessageEvent("NEXT_POS_TRIG %d %.3f"%(
                            event_type_id, event_time), self.msgcategory)
            for trig in self.triggers:
                trig.resetTrigger()
        return triggered

    def _initTargetData(self, frompos, topos):
        """
        Internally used to create the data structure used to store position
        information and events which occurred during each target position
        period.
        """
        if self.storeevents:
            deviceevents={}
            for device in self.storeevents:
                deviceevents[device] = []
        self.targetdata.append(dict(frompos=frompos,
                                      topos=topos,
                                      events=deviceevents
                                    )
                               )


    def _addDeviceEvents(self, device_event_dict={}):
        dev_event_buffer = self.targetdata[-1]['events']
        for dev, dev_events in dev_event_buffer.iteritems():
            if dev in device_event_dict:
                dev_events.extend(device_event_dict[dev])
            else:
                dev_events.extend(dev.getEvents())


    def display(self, **kwargs):
        """
        Display the target at each point in the position grid, performing
        target animation if requested. The target then holds position until
        one of the specified triggers occurs, resulting in the target moving
        to the next position in the positiongrid.

        To setup target animation between grid positions, the following keyword
        arguments are supported. If an option is not specified, the animation
        related to it is not preformed.

        velocity: The rate (units / second) at which the target should move
                  from a current target position to the next target position.
                  The value should be in the unit type the target stimulus
                  is using.

        expandedscale: When a target stimulus is at the current grid position,
                       the target graphic can expand to a size equal to the
                       original target radius * expandedscale.

        expansionduration: If expandedscale has been specified, this option is
                           used to set how long it should take for the target to
                           reach the full expanded target size. Time is in sec.

        contractionduration: If a target has been expanded, this option is used
                             to specify how many seconds it should take for the
                             target to contract back to the original target
                             radius.

        Note that target expansion and contraction change the target stimulus
        outer diameter only. The edge thickness and central dot radius do not
        change.

        All movement and size changes are linear in fashion.

        For example, to display a static target at each grid position::

        targetsequence.display()

        To have the target stim move between each grid position
        at 400 pixels / sec and not expand or contract::

        targetsequence.display(velocity=400.0)

        If the target should jump from one grid position to the next, and then
        expand to twice the radius over a 0.5 second period::

        targetsequence.display(
                                expandedscale=2.0,
                                expansionduration=0.50
                              )

        To do a similar animation as the pervious example, but also have the
        target contract back to it's original size over 0.75 seconds::

        targetsequence.display(
                                expandedscale=2.0,
                                expansionduration=0.50,
                                contractionduration=0.75
                              )

        When this method returns, the target has been displayed at all
        positions. Data collected for each position period can be accessed via
        the targetdata attribute.
        """
        del self.targetdata[:]
        prevpos = None
        
        io = self.getIO()
        io.clearEvents('all')
        io.sendMessageEvent("BEGIN_SEQUENCE {0}".format(len(self.positions.positions)),
                                self.msgcategory)
        turn_rec_off=[]
        for d in self.storeevents:
            if not d.isReportingEvents():
                d.enableEventReporting(True)
                turn_rec_off.append(d)

        sleep(0.025)                
        for pos in self.positions:
            self._initTargetData(prevpos,pos)        
            self._addDeviceEvents()
            self.moveTo(pos, prevpos, **kwargs)
            prevpos = pos
            self._addDeviceEvents()

        for d in turn_rec_off:
            d.enableEventReporting(False)

        io.sendMessageEvent("DONE_SEQUENCE {0}".format(len(self.positions.positions)),
                            self.msgcategory)
        sleep(0.025)        
        self._addDeviceEvents()
        io.clearEvents('all')        

    def _processMessageEvents(self):
        self.target_pos_msgs=[]   
        self.saved_pos_samples=[]
        for pd in self.targetdata:
            frompos=pd.get('frompos')
            topos=pd.get('topos')
            events=pd.get('events')
            
            # create a dict of device labels as keys, device events as value
            devlabel_events={}
            for k,v in events.iteritems():
                devlabel_events[k.getName()]=v
            
            samples = devlabel_events.get('tracker',[])
            # remove any eyetracker events that are not samples
            samples = [s for s in samples if s.type in (EventConstants.BINOCULAR_EYE_SAMPLE,EventConstants.MONOCULAR_EYE_SAMPLE)]
            self.saved_pos_samples.append(samples)

            self.sample_type= self.saved_pos_samples[0][0].type  
            if  self.sample_type == EventConstants.BINOCULAR_EYE_SAMPLE:
                self.sample_msg_dtype=self.binocular_sample_message_element
            else:
                self.sample_msg_dtype=self.monocular_sample_message_element
 
            messages = devlabel_events.get('experiment',[])
            msg_lists=[]
            for m in messages:
                temp = m.text.strip().split()
                msg_type= self.message_types.get(temp[0])
                if msg_type:
                    current_msg = [m.time,m.category]
                    if msg_type[1]==',':                                                
                        for t in temp:
                            current_msg.extend(t.split(',')) 
                    else:
                        current_msg.extend(temp)

                    for mi,dtype in enumerate(msg_type[2:]):
                        current_msg[mi+3]=dtype(current_msg[mi+3])
                        
                    msg_lists.append(current_msg)
            
            if msg_lists[0][2] == 'NEXT_POS_TRIG':
                # handle case where the trigger msg from the previous target
                # message was not read until the start of the next pos.
                # In which case, move msg to end of previous targ pos msgs
                npm=msg_lists.pop(0)
                self.target_pos_msgs[-1].append(npm)
               
            self.target_pos_msgs.append(msg_lists)
        
        for i in range(len( self.target_pos_msgs)):        
            self.target_pos_msgs[i]=np.asarray(self.target_pos_msgs[i])
  
        return self.target_pos_msgs  
        
    def getSampleMessageData(self):
        """
        Return a list of numpy ndarrays, each containing joined eye sample
        and previous / next experiment message data for the sample's time.
        """
        
        #preprocess message events
        self._processMessageEvents()
        
        # inline func to return sample field array based on sample namedtup                       
        def getSampleData(s):
            sampledata=[s.time,s.status]
            if self.sample_type == EventConstants.BINOCULAR_EYE_SAMPLE:                
                sampledata.extend((s.left_gaze_x,
                                   s.left_gaze_y,
                                   s.left_pupil_measure1,
                                   s.right_gaze_x,
                                   s.right_gaze_y,
                                   s.right_pupil_measure1))
                return sampledata

            sampledata.extend((s.gaze_x,
                               s.gaze_y,
                               s.pupil_measure1))                   
            return sampledata  
            
        ######

        #
        ## Process Samples
        #
        
        current_target_pos=-1.0,-1.0
        current_targ_state=0        
        target_pos_samples=[]
        for pindex,samples in enumerate(self.saved_pos_samples):       
            last_msg,messages= self.target_pos_msgs[pindex][0], self.target_pos_msgs[pindex][1:]
            samplesforposition=[]
            pos_sample_count=len(samples)
            si=0
            for current_msg in messages:
                last_msg_time=last_msg[0]
                last_msg_type=last_msg[2]
                if last_msg_type == 'START_DRAW':
                    if not current_targ_state& self.TARGET_STATIONARY:
                        current_targ_state+= self.TARGET_STATIONARY
                    current_targ_state-=current_targ_state& self.TARGET_MOVING
                    current_targ_state-=current_targ_state& self.TARGET_EXPANDING
                    current_targ_state-=current_targ_state& self.TARGET_CONTRACTING                    
                elif last_msg_type == 'EXPAND_SIZE':
                    if not current_targ_state& self.TARGET_EXPANDING:
                        current_targ_state+= self.TARGET_EXPANDING
                    current_targ_state-=current_targ_state& self.TARGET_CONTRACTING                                        
                elif last_msg_type == 'CONTRACT_SIZE':
                    if not current_targ_state& self.TARGET_CONTRACTING:
                        current_targ_state+= self.TARGET_CONTRACTING                                        
                    current_targ_state-=current_targ_state& self.TARGET_EXPANDING
                elif last_msg_type == 'TARGET_POS':
                    current_target_pos=float(last_msg[3]),float(last_msg[4])
                    current_targ_state-=current_targ_state& self.TARGET_MOVING
                    if not current_targ_state& self.TARGET_STATIONARY:
                        current_targ_state+= self.TARGET_STATIONARY
                elif last_msg_type == 'POS_UPDATE':
                    current_target_pos=float(last_msg[3]),float(last_msg[4])
                    if not current_targ_state& self.TARGET_MOVING:
                        current_targ_state+= self.TARGET_MOVING
                    current_targ_state-=current_targ_state& self.TARGET_STATIONARY
                elif last_msg_type == 'SYNCTIME':
                    if not current_targ_state& self.TARGET_STATIONARY:
                        current_targ_state+= self.TARGET_STATIONARY
                    current_targ_state-=current_targ_state& self.TARGET_MOVING
                    current_targ_state-=current_targ_state& self.TARGET_EXPANDING
                    current_targ_state-=current_targ_state& self.TARGET_CONTRACTING
                    current_target_pos=float(last_msg[6]),float(last_msg[7])
                
                while si < pos_sample_count:
                    sample=samples[si]               
                    if sample.time >= last_msg_time and sample.time < current_msg[0]:
                        sarray=[pindex, last_msg_time, last_msg_type,
                                current_msg[0], current_msg[2],
                                current_target_pos[0], current_target_pos[1],
                                current_targ_state]
                        sarray.extend(getSampleData(sample))
                        sndarray=np.asarray(tuple(sarray),dtype= self.sample_msg_dtype)
                        samplesforposition.append(sndarray)
                        si+=1
                    elif sample.time >= current_msg[0]:
                        break
                    else:
                        si+=1
                last_msg=current_msg
            
            # convert any position fields to degrees if needed
            possamples=np.asanyarray(samplesforposition)
            target_pos_samples.append(possamples)
            
        # So we now have a list len == number target positions. Each element 
        # of the list is a list of all eye sample / message data for a
        # target position. Each element of the data list for a single target 
        # position is itself a list that that contains combined info about
        # an eye sample and message info valid for when the sample time was.
        
        return np.asanyarray(target_pos_samples)

################ Validation #######################

class ValidationProcedure(object):
    """
    ValidationProcedure can be used to check the accuracy of a calibrated eye 
    tracking system.
    
    One a ValidationProcedure class instance has been created, the 
    display(**kwargs) method can be called to run the full validation process.
    
    The validation process consists of the following stages:
    
    1) Display an Introduction / Instruction screen. A key press is used to
       move to the next stage.
    2) The validation target presentation sequence. Based on the Target and 
       PositionGrid objects provided when the ValidationProcedure was created,
       a series of target positions are displayed. The progression from one
       target position to the next is controlled by the triggers specified.
       The target can simply jump from one position to the next, or optional
       linear motion settings can be used to have the target move across the
       screen from one point to the next. The Target graphic itself can also 
       be configured to expand or contract once it has reached a location
       defined in the position grid.
    3) During stage 2), data is collected from the devices being monitored by
       iohub. Specifically eye tracker samples and experiment messages are 
       collected.
    4) The data collected during the validation target sequence is used to 
       calculate accuracy information for each target position presented.
       The raw data as well as the computed accuracy data is available via the
       ValidationProcedure class. Calculated measures are provided seperately
       for each target position and include:
       
           a) An array of the samples used for the accuracy calculation. The
              samples used are selected using the following criteria:
                   i) Only samples where the target was stationary and 
                      not expanding or contracting are selected.
                   
                   ii) Samples are selected that fall between:
                   
                          start_time_filter = last_sample_time - accuracy_period_start
                          
                       and
                       
                          end_time_filter = last_sample_time - accuracy_period_end
                       
                       Therefore, the duration of the selected sample period is:
                       
                          selection_period_dur = end_time_filter - start_time_filter
                          
                   iii) Sample that contain missing / invalid position data
                        are then removed, providing the final set of samples
                        used for accuracy calculations. The min, max, and mean
                        values from each set of selected samples is calculated.
                        
           b) The x and y error of each samples gaze position relative to the
              current target position. This data is in the same units as is 
              used by the Target instance. Computations are done for each eye
              being recorded. The values are signed floats.
              
           c) The xy distance error from the from each eye's gaze position to
              the target position. This is also calculated as an average of 
              both eyes when binocular data is available. The data is unsigned,
              providing the absolute distance from gaze to target positions
    
    5) A 2D plot is created displaying each target position and the position of
       each sample used for the accuracy calculation. The minimum, maximum, and
       average error is displayed for all target positions. A key press is used
       to remove the validation results plot, and control is returned to the 
       script that started the validation display. Note that the plot is also 
       saved as a png file in the same directory as the calling stript.
    
    See the validation.py demo in demos.coder.iohub.eyetracker for example usage.
    """
    def __init__(self,
                 target,
                 positions,
                 target_animation_params={},
                 background=None,
                 triggers=2.0,
                 storeeventsfor=None,
                 accuracy_period_start=0.350,
                 accuracy_period_stop=.050,
                 show_intro_screen=True,
                 intro_text="Validation procedure is now going to be performed.",
                 show_results_screen=True,
                 results_in_degrees=False
                 ):
        self.io=ioHubConnection.getActiveConnection()
        self.win=target.win
        self.display_size=target.win.size
        if target_animation_params is None:
            target_animation_params={}
        self.animation_params=target_animation_params
        self.accuracy_period_start=accuracy_period_start
        self.accuracy_period_stop=accuracy_period_stop
        self.show_intro_screen=show_intro_screen
        self.intro_text=intro_text
        self.show_results_screen=show_results_screen
        self.results_in_degrees=results_in_degrees
        self.pix2deg=None        
        if self.results_in_degrees:
            display=self.io.devices.display
            ddim=display.getPhysicalDimensions()
            dhorz,dvert=ddim['width'],ddim['height']
            self.pix2deg = VisualAngleCalc((dhorz,dvert),
                                           self.display_size,
                                           display.getDefaultEyeDistance()
                                           ).pix2deg
        
        self.validation_results=None
        if storeeventsfor is None:
            storeeventsfor=[self.io.devices.keyboard, 
                            self.io.devices.mouse, 
                            self.io.devices.tracker,
                            self.io.devices.experiment
                            ]            

        # Create the TargetPosSequenceStim instance; used to control the sequential
        # presentation of the target at each of the grid positions.
        self.targetsequence = TargetPosSequenceStim(target=target,
                                               positions=positions,
                                               background=background,
                                               triggers=triggers,
                                               storeeventsfor=storeeventsfor
                                               )
        
        # Stim for results screen
        self.imagestim=None
        self.textstim=None
        
        self.use_dpi=80

    def _waitForTrigger(self, trigger_key):
        # TODO: should process a Trigger object. Right now only kb 
        # event supported.
        self.io.clearEvents('all')        
        show_screen=True
        while show_screen:
            kb_events=self.io.devices.keyboard.getEvents()
            for kbe in kb_events:
                if kbe.key==trigger_key:
                    show_screen=False
                    break
            core.wait(0.2,0.025)
        self.io.clearEvents('all')
        
    def display(self,**kwargs):
        """
        Begin the validation procedure. The method returns after the full 
        validation process is complete, including:
            a) display of an instruction screen
            b) display of the target position sequence used for validation
               data collection.
            c) display of a validation accuracy results plot.
        """
        
        if self.show_intro_screen:
            # Display Validation Intro Screen
            #
            self.showIntroScreen()
            self._waitForTrigger(' ')

        # Perform Validation.....
        self.targetsequence.display(**self.animation_params)
        self.io.clearEvents('all')

        if self.show_results_screen:
            # Display Accuracy Results Plot
            self.showResultsScreen()
            self._waitForTrigger(' ')

        
        return self.validation_results
        
    def _generateImageName(self):
        from psychopy.iohub.util import getCurrentDateTimeString, normjoin
        rootScriptPath = os.path.dirname(sys.argv[0])
        file_name='fig_'+getCurrentDateTimeString().replace(' ','_').replace(':','_')+'.png'
        return normjoin(rootScriptPath,file_name)
    
    def _createPlot(self):
        try:
            sample_array=self.targetsequence.getSampleMessageData()
            if self.results_in_degrees:
                for postdat in sample_array:
                    postdat['targ_pos_x'], postdat['targ_pos_y']=self.pix2deg(
                    postdat['targ_pos_x'],postdat['targ_pos_y'])

                    postdat['left_eye_x'], postdat['left_eye_y']=self.pix2deg(
                    postdat['left_eye_x'],postdat['left_eye_y'])

                    postdat['right_eye_x'], postdat['right_eye_y']=self.pix2deg(
                    postdat['right_eye_x'],postdat['right_eye_y'])
                
                
            pixw,pixh=self.display_size
            # Validation Accuracy Analysis
            
            from matplotlib import pyplot as pl
            pl.clf()
            fig=pl.gcf()  
            fig.set_size_inches((pixw*.9)/self.use_dpi,(pixh*.8)/self.use_dpi)

            cm = pl.cm.get_cmap('RdYlBu')
    
            min_error=100000.0
            max_error=0.0
            summed_error=0.0
            point_count=0
            
            results=dict(display_size=self.display_size,
                         position_count=len(sample_array),
                         positions_failed_processing=0,
                         target_positions=[p for p in self.targetsequence.positions],
                         position_results=[])
            for pindex,samplesforpos in enumerate(sample_array):
                
                stationary_samples=samplesforpos[samplesforpos['targ_state'] == 
                                            self.targetsequence.TARGET_STATIONARY]
            
                last_stime=stationary_samples[-1]['eye_time']
                first_stime=stationary_samples[0]['eye_time']

                filter_stime=last_stime- self.accuracy_period_start
                filter_etime=last_stime- self.accuracy_period_stop
            
                all_samples_for_accuracy_calc=stationary_samples[
                                    stationary_samples['eye_time']>=filter_stime]    
                all_samples_for_accuracy_calc=all_samples_for_accuracy_calc[
                            all_samples_for_accuracy_calc['eye_time']<filter_etime]    
                
                good_samples_for_accuracy_calc=all_samples_for_accuracy_calc[
                                    all_samples_for_accuracy_calc['eye_status']<=1]
            
                all_samples_for_accuracy_count=all_samples_for_accuracy_calc.shape[0]
                good_accuracy_sample_count= good_samples_for_accuracy_calc.shape[0]            
                accuracy_calc_good_sample_perc=good_accuracy_sample_count/float(
                                                    all_samples_for_accuracy_count)
            
                # stationary_period_sample_count=stationary_samples.shape[0]
                # target_period_sample_count=samplesforpos.shape[0]
                # print 'target_period_sample_count:',target_period_sample_count
                # print 'stationary_period_sample_count:',stationary_period_sample_count
                # print 'all_samples_for_accuracy_count:',all_samples_for_accuracy_count
                # print 'good_accuracy_sample_count:',good_accuracy_sample_count
                # print 'accuracy_calc_good_sample_perc:',accuracy_calc_good_sample_perc
                
                # Ordered dictionary of the different levels of samples 
                # selected during filtering for valid samples to use in 
                # accuracy calculations.
                sample_msg_data_filtering=OrderedDict(
                                      # All samples from target period.
                                      all_samples=samplesforpos, 
                                      # Sample during stationary period at 
                                      # end of target presentation display.
                                      stationary_samples=stationary_samples,
                                      # Samples that occurred within the 
                                      # defined time selection period. 
                                      time_filtered_samples=all_samples_for_accuracy_calc,
                                      # Samples from the selection period that 
                                      # do not have missing data
                                      used_samples=good_samples_for_accuracy_calc
                                      )
                                      
                position_results=dict(pos_index=pindex,
                                      sample_time_range=[first_stime,last_stime],
                                      filter_samples_time_range=[filter_stime,filter_etime],
                                      sample_from_filter_stages=sample_msg_data_filtering,
                                      valid_filtered_sample_perc=accuracy_calc_good_sample_perc
                                      )
                
                if accuracy_calc_good_sample_perc == 0.0:
                    position_results['calculation_status']='FAILED'
                    results['positions_failed_processing']+=1
                else:
                    time=good_samples_for_accuracy_calc[:]['eye_time']
                
                    target_x=good_samples_for_accuracy_calc[:]['targ_pos_x']
                    target_y=good_samples_for_accuracy_calc[:]['targ_pos_y']
                
                    left_x=good_samples_for_accuracy_calc[:]['left_eye_x']
                    left_y=good_samples_for_accuracy_calc[:]['left_eye_y']
                    left_pupil=good_samples_for_accuracy_calc[:]['left_pupil_size']
                    left_error_x=target_x-left_x
                    left_error_y=target_y-left_y
                    left_error_xy=np.hypot(left_error_x,left_error_y)
                
                    right_x=good_samples_for_accuracy_calc[:]['right_eye_x']
                    right_y=good_samples_for_accuracy_calc[:]['right_eye_y']
                    right_pupil=good_samples_for_accuracy_calc[:]['right_pupil_size']    
                    right_error_x=target_x-right_x
                    right_error_y=target_y-right_y    
                    right_error_xy=np.hypot(right_error_x,right_error_y)
                    
                    lr_x=(left_x+right_x)/2.0
                    lr_y=(left_y+right_y)/2.0
                    lr_error=(right_error_xy+left_error_xy)/2.0
                    lr_error_max=lr_error.max()
                    lr_error_min=lr_error.min()
                    lr_error_mean=lr_error.mean()
                    lr_error_std=np.std(lr_error)
                    
                    min_error=min(min_error,lr_error_min)
                    max_error=max(max_error,lr_error_max)
                    summed_error+=lr_error_mean
                    point_count+=1.0
                    
                    position_results['calculation_status']='PASSED'
                    position_results['target_position']=(target_x[0],target_y[0])
                    position_results['min_error']=lr_error_min
                    position_results['max_error']=lr_error_max
                    position_results['mean_error']=lr_error_mean
                    position_results['stdev_error']=lr_error_std
                    
                    normed_error=lr_error/lr_error_max
                    normed_time=(time-time.min())/(time.max()-time.min())
                    
                    pl.scatter(target_x[0], 
                               target_y[0], 
                               s=400, 
                               c=[0.75,0.75,0.75], 
                               alpha=0.5)
    
                    pl.text(target_x[0], target_y[0], 
                            str(pindex), 
                            size=11, 
                            horizontalalignment='center',
                            verticalalignment='center')
            
                    pl.scatter(lr_x, lr_y, 
                               s=40, c=normed_time, 
                               cmap=cm,alpha=0.75)
           
                    results['position_results'].append(position_results)
            
            unit_type='pixels'
            if self.results_in_degrees:            
                ldeg,bdeg=self.pix2deg(-pixw/2,-pixh/2)
                rdeg,tdeg=self.pix2deg(pixw/2,pixh/2)
                pl.xlim(ldeg, rdeg)
                pl.ylim(bdeg, tdeg)
                unit_type='degrees'
            else:
                pl.xlim(-pixw/2, pixw/2)
                pl.ylim(-pixh/2, pixh/2)                
            pl.xlabel("Horizontal Position (%s)"%(unit_type))
            pl.ylabel("Vertical Position (%s)"%(unit_type))
            
            mean_error=summed_error/point_count
            pl.title("Validation Accuracy (%s)\nMin: %.2f, Max: %.2f, Mean %.2f"%(
                                    unit_type,min_error,max_error,mean_error))
                                    
            results['min_error']=min_error
            results['max_error']=max_error
            results['mean_error']=mean_error
            
            self.validation_results=results
            
            #pl.colorbar()
            fig.tight_layout()
            return fig 
        except:
            print "\nError While Calculating Accuracy Stats:"
            import traceback
            traceback.print_exc()
            print
    
    def getValidationResults(self):
        """
        Returns the last calulationed validation accuracy results, including
        event data used in calculations.
        
        Validation results dict structure:
        
        {
        # Resolution of the display during validation.
        'display_size': array([1280, 1024]),
        # Minimum error for all target positions. In display coord units.
        'min_error': 4.880888,
        # Maximum error for all target positions. In display coord units.
        'max_error': 43.408658,
        # Mean error for all target positions. In display coord units.
        'mean_error': 28.65743,
        # Number of validation Target Positions displayed.
        'position_count': 10,
        # Number of validation Target Positions for which not valid samples could
        # be found following sample selection process. 
        'positions_failed_processing': 0,
        # List of x,y target positions, in the order presented. Units in display
        # unit space (PsychoPy 'pix' in this example).
        'target_positions': [array([ 0.,  0.]),
                              array([-544. ,  435.2]),
                              array([-544.,    0.]),
                              array([-544. , -435.2]),
                              array([ 544. ,  435.2]),
                              array([   0. ,  435.2]),
                              array([ 544. , -435.2]),
                              array([ 544.,    0.]),
                              array([   0. , -435.2]),
                              array([ 0.,  0.])]     
         # Error calculations and raw sample-message evements used in those
         # calculations for one of the target positions presented during the 
         # validation process. The position_results list will have a  length
         # = position_count - 
         'position_results': [{
                           # Index of the current target position in the position
                           # display order
                           'pos_index': 0,
    
                           # Window final position of the current target.
                           'target_position': (0.0, 0.0),
    
                           # The proportion of samples that were selected for use
                           # in the accuracy calculations that were valid.
                           # Invalid samples were not included in accuracy 
                           # calculations.
                           'valid_filtered_sample_perc': 0.9583333333333334},
    
                           # Did the current validation target position
                           # have data points for use in the accuracy calcs.
                           # If valid_filtered_sample_perc == 0, this == FAILED
                           'calculation_status': 'PASSED',
    
                           # Minimum error (in display units) for this position. 
                           'min_error': 35.235695,
    
                           # maximum error (in display units) for this position. 
                           'max_error': 126.20883,
    
                           # Mean error (in display units) for this position. 
                           'mean_error': 49.254543,
    
                           # Stdev of error calculated for the current target pos. 
                           'stdev_error': 17.085871,
    
                           # Time of first and last eye sample collected for 
                           # current target position. 
                           'sample_time_range': [62.145691, 63.626179],
    
                            # Time period used to filter sample-message data points
                           'filter_samples_time_range': [63.076178741455081,
                                                         63.47617874145508],
    
                           # Data collected from current target position period.
                           'sample_from_filter_stages':
                               # Each key provides sample-message data points
                               # for a given stage of sample selection filtering.
                               OrderedDict{
                                   # All sample-message data points during the
                                   # target point display. 
                                   'all_samples': array([ 
                                           # Each sample-message 
                                           # data point combines data from an eye 
                                           # sample with data about the experiment
                                           # message prior to, and following, the 
                                           # eye sample time.
                                           (
                                            0,                  # targ_pos_ix 
                                            62.15571594238281,  # last_msg_time
                                            'SYNCTIME',         # last_msg_type
                                            63.66259002685547,  # next_msg_time
                                            'NEXT_POS_TRIG',    # next_msg_type
                                            0.0,                # targ_pos_x
                                            0.0,                # targ_pos_y
                                            1,                  # targ_state
                                            63.07658386230469,  # eye_time
                                            0,                  # eye_status
                                            7.505566120147705,  # left_eye_x
                                            -60.00013732910156, # left_eye_y
                                            2.901397705078125,  # left_pupil_size
                                            -20.609329223632812,# right_eye_x
                                            -21.901472091674805,# right_eye_y
                                            2.976409912109375   # right_pupil_size
                                            ),
                                            # ......
                                            # for all samples in the current 
                                            # selection level.
                                            ]),
                                   # Sample-Message elements that occurred when 
                                   # target was stationary at end data of any 
                                   # animation graphics. 
                                   'stationary_samples': array([
                                            # Array of Sample-message data elements.
                                            # for current selection level.
                                            # ......
                                            ]),
                                   # Sample-Message elements that occurred within 
                                   # the specified time period prior to target 
                                   # graphics removal.
                                   'time_filtered_samples': array([
                                            # Array of Sample-message data elements.
                                            # for current selection level.
                                            # ......
                                            ]),
                                   # Final set of data used in accuracy calculation. 
                                   'used_samples': array([
                                            # Array of Sample-message data elements.
                                            # for current selection level.
                                            # ......
                                            ]),
                                    }, # Completed sample_from_filter_stages dict
                         }, #End of one entry in the position_results list.
                         {
                         # Next position_results list enty, ....
                         },
            ] # End of the position_results list.
        } # End of validation results dict        
        """
        return self.validation_results
        
    def _buildResultScreen(self,replot=False):
        if replot or self.imagestim is None:        
            fig=self._createPlot()
            text_pos=(0,0)
            text='Accuracy calculation not Possible. Press SPACE to continue.'
            
            if fig:
                fig_name=self._generateImageName()
                fig.savefig(fig_name,dpi=self.use_dpi)
                
                fig_image = Image.open(fig_name)
        
                if self.imagestim:
                    self.imagestim.setImage(fig_image)
                else:
                    self.imagestim = visual.ImageStim(self.win, 
                                                      image=fig_image, 
                                                      units='pix', 
                                                      pos=(0.0, 0.0))
                    
                text='Press SPACE to continue.'
                text_pos=(0.0, -(self.display_size[1]/2.0)*.9)
                       
            if self.textstim is None:
                self.textstim=visual.TextStim(self.win,
                    text=text, pos=text_pos, 
                    color=(0, 0, 0), colorSpace='rgb255', 
                    opacity=1.0, contrast=1.0, units='pix', 
                    ori=0.0, height=None, antialias=True, 
                    bold=False, italic=False, alignHoriz='center', 
                    alignVert='center', wrapWidth=self.display_size[0]*.8)        
            else:
                self.textstim.setText(text)
                self.textstim.setPos(text_pos)
                
            return True
        elif self.imagestim:
                return True
        return False        

    def showResultsScreen(self):
        self._buildResultScreen()
        self.imagestim.draw()
        self.textstim.draw()
        return self.win.flip()

    def showIntroScreen(self):
        text = self.intro_text+"\nPress SPACE to Start...."
        textpos=(0,0)
        if self.textstim:
            self.textstim.setText(text)
            self.textstim.setPos(textpos)
        else:
            self.textstim=visual.TextStim(self.win,
                text=text, pos=textpos, height = 30,
                color=(0, 0, 0), colorSpace='rgb255', 
                opacity=1.0, contrast=1.0, units='pix', 
                ori=0.0, antialias=True, 
                bold=False, italic=False, alignHoriz='center', 
                alignVert='center', wrapWidth=self.display_size[0]*.8)        

        self.textstim.draw()
        return self.win.flip()

from visualangle import VisualAngleCalc
         