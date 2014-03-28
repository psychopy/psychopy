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
from . import win32MessagePump, Trigger, TimeTrigger, DeviceEventTrigger
from ..constants import EventConstants
from .. import ioHubConnection
from weakref import proxy
import numpy as np
from time import sleep

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
                w, h = winSize
                xmin = 0.0
                xmax = 1.0
                ymin = 0.0
                ymax = 1.0

                if leftMargin:
                    if leftMargin < w:
                        xmin = leftMargin/w
                    else:
                        raise ValueError('PositionGrid leftMargin kwarg must be'
                                     ' < winSize[0]')
                if rightMargin:
                    if rightMargin < w:
                        xmax = 1.0-rightMargin/w
                    else:
                        raise ValueError('PositionGrid rightMargin kwarg must be'
                                     ' < winSize[0]')
                if topMargin:
                    if topMargin < h:
                        ymax = 1.0-topMargin/h
                    else:
                        raise ValueError('PositionGrid topMargin kwarg must be'
                                     ' < winSize[1]')
                if bottomMargin:
                    if bottomMargin < h:
                        ymin = bottomMargin/h
                    else:
                        raise ValueError('PositionGrid bottomMargin kwarg must be'
                                     ' < winSize[1]')
                        ymin = bottomMargin/h

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
                    xps = np.random.uniform(xmin, xmax, colCount)*w-w/2.0
                    yps = np.random.uniform(ymin, ymax, rowCount)*h-h/2.0
                else:
                    xps = np.linspace(xmin, xmax, colCount)*w-w/2.0
                    yps = np.linspace(ymin, ymax, rowCount)*h-h/2.0

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
        w , h = self.winSize
        pl.clf()
        pl.scatter(x, y, **kwargs)
        pl.xlim(-w/2, w/2)
        pl.ylim(-h/2, h/2)
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
    def __init__(self,
                 target,            # The TargetStim instance to use.
                 positions,         # The PositionGrid instance to use.
                 background=None,   # Window background color to use (if any).
                 storeeventsfor=[], # List of iohub device objects to track
                                    # events for.
                 triggers=None,     # The triggers to use for controlling target
                                    # position progression.
                 msgcategory=""     # As the display() process is preformed,
                                    # iohub experiment messages are generated
                                    # providing information on the state of the
                                    # target and position. msgcategory can be
                                    # used to define the category string to
                                    # assign to each message.
                ):
        self.win = target.win
        self.target = target
        self.background = background
        self.positions = positions
        self.storeevents=storeeventsfor
        self.msgcategory=msgcategory

        # If storeevents is True, targetdata will be a list of dict's.
        # Each dict, among other things, contains all ioHub events that occurred
        # from when a target was first presented at a position, to when the
        # the wait period completed for that position.
        #
        self.targetdata=[]
        self.triggers = None
        io = self.getIO()

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
        return ioHubConnection.getActiveConnection()

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
                    io.sendMessageEvent("POS_UPDATE\t%.2f,%.2f\t%.3f\t%3f"%(
                                        tpos[0], tpos[1], starttime,
                                        arrivetime), self.msgcategory,
                                        sec_time=fliptime)
                    self._addDeviceEvents()

        self.target.setPos(topos)
        self._draw()
        fliptime = self.win.flip()
        io.sendMessageEvent("TARGET_POS\t%.2f,%.2f"%(topos[0], topos[1]),
                            self.msgcategory, sec_time=fliptime)
        self._addDeviceEvents()

        expandedscale=kwargs.get('expandedscale')
        expansionduration=kwargs.get('expansionduration')
        contractionduration=kwargs.get('contractionduration')

        if expandedscale:
            initialradius=self.target.radius
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
                    io.sendMessageEvent("EXPAND_SIZE\t%.2f\t%.2f\t"
                                        "%.3f"%(initialradius, cradius,
                                                starttime),
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
                    io.sendMessageEvent("CONTRACT_SIZE\t%.2f\t%.2f\t"
                                        "%.3f"%(cradius, initialradius,
                                                starttime),
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
        self._initTargetData(frompos, topos)

        io = self.getIO()
        io.clearEvents('all')
        io.sendMessageEvent("START_DRAW\t{0}\t{1}\t{2}".format(
            self.positions.posIndex, frompos, topos), self.msgcategory)

        fliptime=self._animateTarget(topos, frompos, **kwargs)

        io.sendMessageEvent("SYNCTIME\t{0}\t{1}\t{2}".format(
            self.positions.posIndex, frompos, topos), self.msgcategory,
            sec_time=fliptime)

        # wait for trigger to fire
        last_pump_time=fliptime
        while not self._hasTriggerFired(start_time=fliptime):
            if getTime() - last_pump_time >= 0.250:
                win32MessagePump()
                last_pump_time = getTime()
            sleep(0.005)

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
        io.sendMessageEvent("BEGIN_SEQUENCE\t{0}".format(len(self.positions.positions)),
                                self.msgcategory)

        for pos in self.positions:
            self.moveTo(pos, prevpos, **kwargs)
            prevpos = pos

        io.sendMessageEvent("DONE_SEQUENCE\t{0}".format(len(self.positions.positions)),
                            self.msgcategory)
