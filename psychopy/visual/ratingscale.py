#!/usr/bin/env python2

'''A class for getting numeric or categorical ratings, e.g., a 1-to-7 scale.'''

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys
import numpy

from psychopy import core, logging, event
from psychopy.colors import isValidColor
from psychopy.visual.circle import Circle
from psychopy.visual.patch import PatchStim
from psychopy.visual.shape import ShapeStim
from psychopy.visual.text import TextStim
from psychopy.visual.basevisual import MinimalStim
from psychopy.visual.helpers import pointInPolygon, groupFlipVert
from psychopy.tools.attributetools import attributeSetter, setWithOperation, logAttrib
from psychopy.constants import FINISHED, STARTED, NOT_STARTED


class RatingScale(MinimalStim):
    """A class for obtaining ratings, e.g., on a 1-to-7 or categorical scale.

    A RatingScale instance is a re-usable visual object having a ``draw()``
    method, with customizable appearance and response options. ``draw()``
    displays the rating scale, handles the subject's mouse or key responses,
    and updates the display. When the subject accepts a selection, ``.noResponse``
    goes ``False`` (i.e., there is a response). You can call the ``getRating()``
    method anytime to get a rating, ``getRT()`` to get the decision time, or
    ``getHistory()`` to obtain the entire set of (rating, RT) pairs.

    There are five main elements of a rating scale: the `scale` (text above the
    line intended to be a reminder of how to use the scale), the `line` (with
    tick marks), the `marker` (a moveable visual indicator on the line), the
    `labels` (text below the line that label specific points), and the `accept` button.
    The appearance and function of elements can be customized by the experimenter; it is not possible
    to orient a rating scale to be vertical. Multiple scales can be displayed at
    the same time, and continuous real-time ratings can be obtained from the history.

    The Builder RatingScale component gives a restricted set of options, but also
    allows full control over a RatingScale via the 'customize_everything' field.

    A RatingScale instance has no idea what else is on the screen. The experimenter
    has to draw the item to be rated, and handle `escape` to break or quit, if desired.
    The subject can use the mouse or keys to respond. Direction keys (left, right)
    will move the marker in the smallest available increment (e.g., 1/10th of a
    tick-mark if precision = 10).

    **Example 1**:

        A basic 7-point scale::

            ratingScale = visual.RatingScale(win)
            item = <statement, question, image, movie, ...>
            while ratingScale.noResponse:
                item.draw()
                ratingScale.draw()
                win.flip()
            rating = ratingScale.getRating()
            decisionTime = ratingScale.getRT()
            choiceHistory = ratingScale.getHistory()

    **Example 2**:

        For fMRI, sometimes only a keyboard can be used. If your response box sends
        keys 1-4, you could specify left, right, and accept keys, and not need a mouse::

            ratingScale = visual.RatingScale(win, low=1, high=5, markerStart=4,
                leftKeys='1', rightKeys = '2', acceptKeys='4')

    **Example 3**:

        Categorical ratings can be obtained using choices::

            ratingScale = visual.RatingScale(win, choices=['agree', 'disagree'],
                markerStart=0.5, singleClick=True)

    For other examples see Coder Demos -> stimuli -> ratingScale.py.

    :Authors:
        - 2010 Jeremy Gray: original code and on-going updates
        - 2012 Henrik Singmann: tickMarks, labels, ticksAboveLine
        - 2014 Jeremy Gray: multiple API changes (v1.80.00)
    """
    def __init__(self,
                win,
                scale='<default>',
                choices=None,
                low=1,
                high=7,
                precision=1,
                labels=(),
                tickMarks=None,
                tickHeight=1.0,
                marker='triangle',
                markerStart=None,
                markerColor=None,
                markerExpansion=1,
                singleClick=False,
                disappear=False,
                textSize=1.0,
                textColor='LightGray',
                textFont='Helvetica Bold',
                showValue=True,
                showAccept=True,
                acceptKeys='return',
                acceptPreText='key, click',
                acceptText='accept?',
                acceptSize=1.0,
                leftKeys='left',
                rightKeys='right',
                respKeys=(),
                lineColor='White',
                skipKeys='tab',
                mouseOnly=False,
                size=1.0,
                stretch=1.0,
                pos=None,
                minTime=0.4,
                maxTime=0.0,
                flipVert=False,
                depth=0,
                name='',
                autoLog=True,
                **kwargs  # catch obsolete args
                ):
        """
    :Parameters:

        win :
            A :class:`~psychopy.visual.Window` object (required).
        choices :
            A list of items which the subject can choose among. ``choices`` takes
            precedence over ``low``, ``high``, ``precision``, ``scale``, ``labels``,
            and ``tickMarks``.
        low :
            Lowest numeric rating (integer), default = 1.
        high :
            Highest numeric rating (integer), default = 7.
        precision :
            Portions of a tick to accept as input [1, 10, 100]; default = 1 (a whole tick).
            Pressing a key in `leftKeys` or `rightKeys` will move the marker by
            one portion of a tick.
        scale :
            Optional reminder message about how to respond or rate an item,
            displayed above the line; default = '<low>=not at all, <high>=extremely'.
            To suppress the scale, set ``scale=None``.
        labels :
            Text to be placed at specific tick marks to indicate their value. Can
            be just the ends (if given 2 labels), ends + middle (if given 3 labels),
            or all points (if given the same number of labels as points).
        tickMarks :
            List of positions at which tick marks should be placed from low to high.
            The default is to space tick marks equally, one per integer value.
        tickHeight :
            The vertical height of tick marks: 1.0 is the default height (above line),
            -1.0 is below the line, and 0.0 suppresses the display of tickmarks.
            ``tickHeight`` is purely cosmetic, and can be fractional, e.g., 1.2.
        marker :
            The moveable visual indicator of the current selection. The predefined styles are
            'triangle', 'circle', 'glow', 'slider', or 'hover'. A slider moves smoothly when
            there are enough screen positions to move through, e.g., low=0, high=100.
            Hovering requires a set of choices, and allows clicking directly on individual
            choices; dwell-time is not recorded.
            Can also be set to a custom marker stimulus: any object with a .draw() method and .pos will work, e.g.,
            ``visual.TextStim(win, text='[]', units='norm')``.
        markerStart :
            The location or value to be pre-selected upon initial display, either numeric or
            one of the choices. Can be fractional, e.g., midway between two options.
        markerColor :
            Color to use for a predefined marker style, e.g., 'DarkRed', '#123456'.
        markerExpansion :
            Only affects the `glow` marker: How much to expand or contract when
            moving rightward; 0=none, negative shrinks.
        singleClick :
            Enable a mouse click to both select and accept the rating, default = ``False``.
            A legal key press will also count as a singleClick.
            The 'accept' box is visible, but clicking it has no effect.
        pos : tuple (x, y)
            Position of the rating scale on the screen. The midpoint of the line will
            be positioned at ``(x, y)``; default = ``(0.0, -0.4)`` in norm units
        size :
            How much to expand or contract the overall rating scale display. Default
            size = 1.0. For larger than the default, set ``size`` > 1; for smaller, set < 1.
        stretch:
            Like ``size``, but only affects the horizontal direction.
        textSize :
            The size of text elements, relative to the default size (i.e., a scaling factor, not points).
        textColor :
            Color to use for labels and scale text; default = 'LightGray'.
        textFont :
            Name of the font to use; default = 'Helvetica Bold'.
        showValue :
            Show the subject their current selection default = ``True``. Ignored
            if singleClick is ``True``.
        showAccept :
            Show the button to click to accept the current value by using the mouse; default = ``True``.
        acceptPreText :
            The text to display before any value has been selected.
        acceptText :
            The text to display in the 'accept' button after a value has been selected.
        acceptSize :
            The width of the accept box relative to the default (e.g., 2 is twice as wide).
        acceptKeys :
            A list of keys that are used to accept the current response; default = 'return'.
        leftKeys :
            A list of keys that each mean "move leftwards"; default = 'left'.
        rightKeys :
            A list of keys that each mean "move rightwards"; default = 'right'.
        respKeys :
            A list of keys to use for selecting choices, in the desired order.
            The first item will be the left-most choice, the second item will be the
            next choice, and so on.
        skipKeys :
            List of keys the subject can use to skip a response, default = 'tab'.
            To require a response to every item, set ``skipKeys=None``.
        lineColor :
            The RGB color to use for the scale line, default = 'White'.
        mouseOnly :
            Require the subject to use the mouse (any keyboard input is ignored), default = ``False``.
            Can be used to avoid competing with other objects for keyboard input.
        minTime :
            Seconds that must elapse before a reponse can be accepted,
            default = `0.4`.
        maxTime :
            Seconds after which a response cannot be accepted.
            If ``maxTime`` <= ``minTime``, there's no time limit.
            Default = `0.0` (no time limit).
        disappear :
            Whether the rating scale should vanish after a value is accepted.
            Can be useful when showing multiple scales.
        flipVert :
            Whether to mirror-reverse the rating scale in the vertical direction.
        name : string
            The name of the object to be using during logged messages about
            this stim.
        autolog :
            Whether logging should be done automatically.
    """
        # what local vars are defined (these are the init params) for use by __repr__
        self._initParams = dir()
        super(RatingScale, self).__init__(name=name, autoLog=False)

        # warn about obsolete arguments; Jan 2014, for v1.80:
        obsoleted = set(['showScale', 'ticksAboveLine', 'displaySizeFactor', 'markerStyle',
                'customMarker', 'allowSkip', 'stretchHoriz', 'escapeKeys', 'textSizeFactor',
                'showScale', 'showAnchors', 'lowAnchorText', 'highAnchorText'])
        obsArgs = set(kwargs.keys()).intersection(obsoleted)
        if obsArgs:
            logging.error('RatingScale obsolete args: %s; see changelog v1.80.00 for notes on how to migrate' % list(obsArgs))
            core.quit()
        # kwargs will absorb everything, including typos, so warn about bad args
        unknownArgs = set(kwargs.keys()).difference(obsoleted)
        if unknownArgs:
            logging.error("RatingScale unknown kwargs: %s" % list(unknownArgs))
            core.quit()

        self.autoLog = False # needs to start off False
        self.win = win
        self.name = name
        self.disappear = disappear

        # internally work in norm units, restore to orig units at the end of __init__:
        self.savedWinUnits = self.win.units
        self.win.units = 'norm'
        self.depth = depth

        # 'hover' style = like hyperlink with hover over choices:
        if marker == 'hover':
            showAccept = False
            singleClick = True
            textSize *= 1.5
            mouseOnly = True

        # make things well-behaved if the requested value(s) would be trouble:
        self._initFirst(showAccept, mouseOnly, singleClick, acceptKeys,
                        marker, markerStart, low, high, precision, choices,
                        scale, tickMarks, labels, tickHeight)
        self._initMisc(minTime, maxTime)

        # Set scale & position, key-bindings:
        self._initPosScale(pos, size, stretch)
        self._initKeys(self.acceptKeys, skipKeys, leftKeys, rightKeys, respKeys)

        # Construct the visual elements:
        self._initLine(tickMarkValues=tickMarks, lineColor=lineColor, marker=marker)
        self._initMarker(marker, markerColor, markerExpansion)
        self._initTextElements(win,
            self.scale, textColor, textFont, textSize, showValue, tickMarks)
        self._initAcceptBox(self.showAccept, acceptPreText, acceptText, acceptSize,
            self.markerColor, self.textSizeSmall, textSize, self.textFont)

        # List-ify the visual elements; self.marker is handled separately
        self.visualDisplayElements = []
        if self.showScale:
            self.visualDisplayElements += [self.scaleDescription]
        if self.showAccept:
            self.visualDisplayElements += [self.acceptBox, self.accept]
        if self.labels:
            for item in self.labels:
                if not item.text == '':  # skip any empty placeholders
                    self.visualDisplayElements.append(item)
        if marker != 'hover':
            self.visualDisplayElements += [self.line]

        # Mirror (flip) vertically if requested
        self.flipVert = False
        self.setFlipVert(flipVert)

        # Final touches:
        self.origScaleDescription = self.scaleDescription.text
        self.reset()  # sets .status, among other things
        self.win.units = self.savedWinUnits

        #set autoLog (now that params have been initialised)
        self.autoLog = autoLog
        if autoLog:
            logging.exp("Created %s = %s" %(self.name, repr(self)))

    def __repr__(self, complete=False):
        return self.__str__(complete=complete)  # from MinimalStim

    def _initFirst(self, showAccept, mouseOnly, singleClick, acceptKeys,
                   marker, markerStart, low, high, precision, choices,
                   scale, tickMarks, labels, tickHeight):
        """some sanity checking; various things are set, especially those that are
        used later; choices, anchors, markerStart settings are handled here
        """
        self.showAccept = bool(showAccept)
        self.mouseOnly = bool(mouseOnly)
        self.singleClick = bool(singleClick)
        self.acceptKeys = acceptKeys
        self.precision = precision
        self.labelTexts = None
        self.tickHeight = tickHeight

        if not self.showAccept:
            # the accept button is the mouse-based way to accept the current response
            if len(list(self.acceptKeys)) == 0:
                # make sure there is in fact a way to respond using a key-press:
                self.acceptKeys = ['return']
            if self.mouseOnly and not self.singleClick:
                # then there's no way to respond, so deny mouseOnly / enable using keys:
                self.mouseOnly = False
                logging.warning("RatingScale %s: ignoring mouseOnly (because showAccept and singleClick are False)" % self.name)

        self.scale = scale
        self.showScale = (scale is not None)

        # 'choices' is a list of non-numeric (unordered) alternatives:
        if choices and len(list(choices)) < 2:
            logging.error("RatingScale %s: choices requires 2 or more items" % self.name)
        if choices and len(list(choices)) >= 2:
            low = 0
            high = len(list(choices)) - 1
            self.precision = 1  # a fractional choice makes no sense
            self.choices = choices
            self.labelTexts = choices
        else:
            self.choices = False
        if marker == 'hover' and not self.choices:
            logging.error("RatingScale: marker='hover' requires a set of choices.")
            core.quit()

        # Anchors need to be well-behaved [do after choices]:
        try:
            self.low = int(low)
        except:
            self.low = 1
        try:
            self.high = int(high)
        except:
            self.high = self.low + 1
        if self.high <= self.low:
            self.high = self.low + 1
            self.precision = 100

        if not self.choices:
            if labels and len(labels) == 2:
                # label the endpoints
                self.labelTexts = [labels[0]] + [''] * (self.high-self.low - 1) + [labels[-1]]
            elif labels and len(labels) == 3 and (self.high-self.low) > 1 and (1+self.high-self.low) % 2:
                # label endpoints and middle tick
                placeHolder = [''] * ((self.high-self.low-2)//2)
                self.labelTexts = [labels[0]] + placeHolder + [labels[1]] + placeHolder + [labels[2]]
            else:
                self.labelTexts = [unicode(self.low)] + [''] * (self.high-self.low - 1) + [unicode(self.high)]

        if tickMarks and not(labels is False):
            if labels is None:
                self.labelTexts = tickMarks
            else:
                self.labelTexts = labels
            if len(self.labelTexts) != len(tickMarks):
                logging.warning("RatingScale %s: len(labels) not equal to len(tickMarks)" % self.name)
                self.labelTexts = tickMarks
            if self.scale == "<default>":
                self.scale = False

        # Marker pre-positioned? [do after anchors]
        try:
            self.markerStart = float(markerStart)
        except:
            if isinstance(markerStart, basestring) and type(self.choices) == list and markerStart in self.choices:
                self.markerStart = self.choices.index(markerStart)
                self.markerPlacedAt = self.markerStart
                self.markerPlaced = True
            else:
                self.markerStart = None
                self.markerPlaced = False
        else:  # float(markerStart) suceeded
            self.markerPlacedAt = self.markerStart
            self.markerPlaced = True

    def _initMisc(self, minTime, maxTime):
        # precision is the fractional parts of a tick mark to be sensitive to, in [1,10,100]:
        if type(self.precision) != int or self.precision < 10:
            self.precision = 1
            self.fmtStr = "%.0f" # decimal places, purely for display
        elif self.precision < 100:
            self.precision = 10
            self.fmtStr = "%.1f"
        else:
            self.precision = 100
            self.fmtStr = "%.2f"

        self.clock = core.Clock() # for decision time
        try:
            self.minTime = float(minTime)
        except ValueError:
            self.minTime = 1.0
        self.minTime = max(self.minTime, 0.)
        try:
            self.maxTime = float(maxTime)
        except ValueError:
            self.maxTime = 0.0
        self.allowTimeOut = bool(self.minTime < self.maxTime)

        self.myMouse = event.Mouse(win=self.win, visible=True)
        # Mouse-click-able 'accept' button pulsates (cycles its brightness over frames):
        frames_per_cycle = 100
        self.pulseColor = [0.6 + 0.22 * float(numpy.cos(i/15.65)) for i in range(frames_per_cycle)]

    def _initPosScale(self, pos, size, stretch, log=True):
        """position (x,y) and size (magnification) of the rating scale
        """
        # Screen position (translation) of the rating scale as a whole:
        if pos:
            if len(list(pos)) == 2:
                offsetHoriz, offsetVert = pos
            elif log and self.autoLog:
                logging.warning("RatingScale %s: pos expects a tuple (x,y)" % self.name)
        try:
            self.offsetHoriz = float(offsetHoriz)
        except:
            if self.savedWinUnits == 'pix':
                self.offsetHoriz = 0
            else: # default x in norm units:
                self.offsetHoriz = 0.0
        try:
            self.offsetVert = float(offsetVert)
        except:
            if self.savedWinUnits == 'pix':
                self.offsetVert = int(self.win.size[1] / -5.0)
            else: # default y in norm units:
                self.offsetVert = -0.4
        # pos=(x,y) will consider x,y to be in win units, but want norm internally
        if self.savedWinUnits == 'pix':
            self.offsetHoriz = float(self.offsetHoriz) / self.win.size[0] / 0.5
            self.offsetVert = float(self.offsetVert) / self.win.size[1] / 0.5
        self.pos = [self.offsetHoriz, self.offsetVert] # just expose; not used elsewhere yet

        # Scale size (magnification) of the rating scale as a whole:
        try:
            self.stretch = float(stretch)
        except ValueError:
            self.stretch = 1.
        try:
            self.size = float(size) * 0.6
        except ValueError:
            self.size = 0.6

    def _initKeys(self, acceptKeys, skipKeys, leftKeys, rightKeys, respKeys):
        # keys for accepting the currently selected response:
        if self.mouseOnly:
            self.acceptKeys = [ ] # no valid keys, so must use mouse
        else:
            if type(acceptKeys) not in [list, tuple, set]:
                acceptKeys = [acceptKeys]
            self.acceptKeys = acceptKeys
        self.skipKeys = [ ]
        if skipKeys and not self.mouseOnly:
            if type(skipKeys) not in [list, tuple, set]:
                skipKeys = [skipKeys]
            self.skipKeys = list(skipKeys)
        if type(leftKeys) not in [list, tuple, set]:
            leftKeys = [leftKeys]
        self.leftKeys = leftKeys
        if type(rightKeys) not in [list, tuple, set]:
            rightKeys = [rightKeys]
        self.rightKeys = rightKeys

        # allow responding via arbitrary keys if given as a param:
        if respKeys and hasattr(respKeys, '__iter__'):
            self.respKeys = respKeys
            self.enableRespKeys = True
            if (set(self.respKeys).intersection(self.leftKeys + self.rightKeys +
                        self.acceptKeys + self.skipKeys)):
                logging.warning('RatingScale %s: respKeys may conflict with other keys' % self.name)
        else:
            # allow resp via numeric keys if the response range is in 0-9
            self.respKeys = [ ]
            if (not self.mouseOnly and self.low > -1 and self.high < 10):
                self.respKeys = [str(i) for i in range(self.low, self.high + 1)]
            # but if any digit is used as an action key, that should take precedence
            # so disable using numeric keys:
            if (set(self.respKeys).intersection(self.leftKeys + self.rightKeys +
                                    self.acceptKeys + self.skipKeys) == set([]) ):
                self.enableRespKeys = True
            else:
                self.enableRespKeys = False
        if self.enableRespKeys:
            self.tickFromKeyPress = {}
            for i, key in enumerate(self.respKeys):
                self.tickFromKeyPress[key] = i + self.low

        self.allKeys = (self.rightKeys + self.leftKeys + self.acceptKeys +
                        self.skipKeys + self.respKeys)

    def _initLine(self, tickMarkValues=None, lineColor='White', marker=None):
        """define a ShapeStim to be a graphical line, with tick marks.

        ### Notes (JRG Aug 2010)
        Conceptually, the response line is always -0.5 to +0.5 ("internal" units). This line, of unit length,
        is scaled and translated for display. The line is effectively "center justified", expanding both left
        and right with scaling, with pos[] specifiying the screen coordinate (in window units, norm or pix)
        of the mid-point of the response line. Tick marks are in integer units, internally 0 to (high-low),
        with 0 being the left end and (high-low) being the right end. (Subjects see low to high on the screen.)
        Non-numeric (categorical) choices are selected using tick-marks interpreted as an index, choice[tick].
        Tick units get mapped to "internal" units based on their proportion of the total ticks (--> 0. to 1.).
        The unit-length internal line is expanded / contracted by stretch and size, and then
        is translated to position pos (offsetHoriz=pos[0], offsetVert=pos[1]). pos is the name of the arg, and
        its values appear in the code as offsetHoriz and offsetVert only for historical reasons (could be
        refactored for clarity).

        Auto-rescaling reduces the number of tick marks shown on the
        screen by a factor of 10, just for nicer appearance, without affecting the internal representation.

        Thus, the horizontal screen position of the i-th tick mark, where i in [0,n], for n total ticks (n = high-low),
        in screen units ('norm') will be:
          tick-i             == offsetHoriz + (-0.5 + i/n ) * stretch * size
        So two special cases are:
          tick-0 (left end)  == offsetHoriz - 0.5 * stretch * size
          tick-n (right end) == offsetHoriz + 0.5 * stretch * size
        The vertical screen position is just offsetVert (in screen norm units).
        To elaborate: tick-0 is the left-most tick, or "low anchor"; here 0 is internal, the subject sees <low>.
        tick-n is the right-most tick, or "high anchor", or internal-tick-(high-low), and the subject sees <high>.
        Intermediate ticks, i, are located proportionally between -0.5 to + 0.5, based on their proportion
        of the total number of ticks, float(i)/n. The "proportion of total" is used because its a line of unit length,
        i.e., the same length as used to internally represent the scale (-0.5 to +0.5).
        If precision > 1, the user / experimenter is asking for fractional ticks. These map correctly
        onto [0, 1] as well without requiring special handling (just do ensure float() ).

        Another note: -0.5 to +0.5 looked too big to be the default size of the rating line in screen norm units,
        so I set the internal size = 0.6 to compensate (i.e., making everything smaller). The user can
        adjust the scaling around the default by setting size, stretch, or both.
        This means that the user / experimenter can just think of > 1 being expansion (and < 1 == contraction)
        relative to the default (internal) scaling, and not worry about the internal scaling.

        ### Notes (HS November 2012)
        To allow for labels at the ticks, the positions of the tick marks are saved in self.tickPositions.
        If tickMarks, those positions are used instead of the automatic positions.
        """

        self.lineColor = lineColor
        self.baseSize = 0.04 # vertical height of each tick, norm units; used for markers too
        self.tickMarks = float(self.high - self.low)  # num tick marks to display, can get autorescaled
        self.autoRescaleFactor = 1

        if tickMarkValues:
            tickTmp = numpy.asarray(tickMarkValues, dtype=numpy.float32)
            tickMarkPositions = (tickTmp - self.low) / self.tickMarks
        else:
            # visually remap 10 ticks onto 1 tick in some conditions (= cosmetic):
            if (self.low == 0 and self.tickMarks > 20 and int(self.tickMarks) % 10 == 0):
                self.autoRescaleFactor = 10
                self.tickMarks /= self.autoRescaleFactor
            tickMarkPositions = numpy.linspace(0, 1, self.tickMarks + 1)
        self.scaledPrecision = float(self.precision * self.autoRescaleFactor)

        # how far a left or right key will move the marker, in tick units:
        self.keyIncrement = 1. / self.autoRescaleFactor / self.precision
        self.hStretchTotal = self.stretch * self.size

        # ends of the rating line, in norm units:
        self.lineLeftEnd  = self.offsetHoriz - 0.5 * self.hStretchTotal
        self.lineRightEnd = self.offsetHoriz + 0.5 * self.hStretchTotal

        # space around the line within which to accept mouse input:
        pad = 0.06 * self.size
        if marker == 'hover':
            padText = (1./(3*(self.high-self.low))) * (self.lineRightEnd - self.lineLeftEnd)
        else:
            padText = 0
        self.nearLine = [
            [self.lineLeftEnd - pad - padText, -2 * pad + self.offsetVert],
            [self.lineLeftEnd - pad - padText, 2 * pad + self.offsetVert],
            [self.lineRightEnd + pad + padText, 2 * pad + self.offsetVert],
            [self.lineRightEnd + pad + padText, -2 * pad + self.offsetVert] ]

        # vertices for ShapeStim:
        self.tickPositions = []  # list to hold horizontal positions
        vertices = [[self.lineLeftEnd, self.offsetVert]]  # first vertex
        # vertical height of ticks (purely cosmetic):
        if self.tickHeight is False:
            self.tickHeight = -1.  # backwards compatibility for boolean
        # numeric -> scale tick height;  float(True) == 1.
        tickSize = self.baseSize * self.size * float(self.tickHeight)
        lineLength = self.lineRightEnd - self.lineLeftEnd
        for count, tick in enumerate(tickMarkPositions):
            horizTmp = self.lineLeftEnd + lineLength * tick
            vertices += [[horizTmp, self.offsetVert + tickSize],
                         [horizTmp, self.offsetVert]]
            if count < len(tickMarkPositions) - 1:
                tickRelPos = lineLength * tickMarkPositions[count + 1]
                nextHorizTmp = self.lineLeftEnd + tickRelPos
                vertices.append([nextHorizTmp, self.offsetVert])
            self.tickPositions.append(horizTmp)
        vertices += [[self.lineRightEnd, self.offsetVert],
                     [self.lineLeftEnd, self.offsetVert]]

        # create the line:
        self.line = ShapeStim(win=self.win, units='norm', vertices=vertices,
            lineWidth=4, lineColor=self.lineColor, name=self.name+'.line', autoLog=False)

    def _initMarker(self, marker, markerColor, expansion):
        """define a visual Stim to be used as the indicator.

        marker can be either a string, or a visual object (custom marker).
        """
        # preparatory stuff:
        self.markerOffsetVert = 0.
        if isinstance(marker, basestring):
            self.markerStyle = marker
        elif not hasattr(marker, 'draw'):
            logging.error("RatingScale: custom marker has no draw() method")
            self.markerStyle = 'triangle'
        else:
            self.markerStyle = 'custom'
            if hasattr(marker, 'pos'):
                self.markerOffsetVert = marker.pos[1]
            else:
                logging.error("RatingScale: custom marker has no pos attribute")

        self.markerSize = 8. * self.size
        if isinstance(markerColor, basestring):
            markerColor = markerColor.replace(' ', '')

        # define or create self.marker:
        if self.markerStyle == 'hover':
            self.marker = TextStim(win=self.win, text=' ', units='norm', autoLog=False)  # placeholder
            self.markerOffsetVert = .02
            if not markerColor:
                markerColor = 'darkorange'
        elif self.markerStyle == 'triangle':
            scaledTickSize = self.baseSize * self.size
            vert = [[-1 * scaledTickSize * 1.8, scaledTickSize * 3],
                    [ scaledTickSize * 1.8, scaledTickSize * 3], [0, -0.005]]
            if markerColor == None or not isValidColor(markerColor):
                markerColor = 'DarkBlue'
            self.marker = ShapeStim(win=self.win, units='norm', vertices=vert,
                lineWidth=0.1, lineColor=markerColor, fillColor=markerColor,
                name=self.name+'.markerTri', autoLog=False)
        elif self.markerStyle == 'slider':
            scaledTickSize = self.baseSize * self.size
            vert = [[-1 * scaledTickSize * 1.8, scaledTickSize],
                    [ scaledTickSize * 1.8, scaledTickSize],
                    [ scaledTickSize * 1.8, -1 * scaledTickSize],
                    [-1 * scaledTickSize * 1.8, -1 * scaledTickSize]]
            if markerColor == None or not isValidColor(markerColor):
                markerColor = 'black'
            self.marker = ShapeStim(win=self.win, units='norm', vertices=vert,
                lineWidth=0.1, lineColor=markerColor, fillColor=markerColor,
                name=self.name+'.markerSlider', opacity=0.7, autoLog=False)
        elif self.markerStyle == 'glow':
            if markerColor == None or not isValidColor(markerColor):
                markerColor = 'White'
            self.marker = PatchStim(win=self.win, units='norm',
                tex='sin', mask='gauss', color=markerColor, opacity = 0.85,
                autoLog=False, name=self.name+'.markerGlow')
            self.markerBaseSize = self.baseSize * self.markerSize
            self.markerOffsetVert = .02
            self.markerExpansion = float(expansion)  * 0.6
            if self.markerExpansion == 0:
                self.markerBaseSize *= self.markerSize * 0.7
                if self.markerSize > 1.2:
                    self.markerBaseSize *= .7
                self.marker.setSize(self.markerBaseSize/2., log=False)
        elif self.markerStyle == 'custom':
            if markerColor == None:
                if hasattr(marker, 'color'):
                    try:
                        if not marker.color: # 0 causes other problems, so ignore it here
                            marker.color = 'DarkBlue'
                    except ValueError:  # testing truth value of list
                        marker.color = 'DarkBlue'
                elif hasattr(marker, 'fillColor'):
                    marker.color = marker.fillColor
                else:
                    marker.color = 'DarkBlue'
                markerColor = marker.color
            if not hasattr(marker, 'name') or not marker.name:
                marker.name = 'customMarker'
            self.marker = marker
        else:  # 'circle':
            if markerColor == None or not isValidColor(markerColor):
                markerColor = 'DarkRed'
            x,y = self.win.size
            windowRatio = float(y)/x
            self.markerSizeVert = 3.2 * self.baseSize * self.size
            circleSize = [self.markerSizeVert * windowRatio, self.markerSizeVert]
            self.markerOffsetVert = self.markerSizeVert / 2.
            self.marker = Circle(self.win, size=circleSize, units='norm',
                lineColor=markerColor, fillColor=markerColor,
                name=self.name+'.markerCir', autoLog=False)
            self.markerBaseSize = self.baseSize
        self.markerColor = markerColor
        self.markerYpos = self.offsetVert + self.markerOffsetVert

    def _initTextElements(self, win, scale, textColor,
                          textFont, textSize, showValue, tickMarks):
        """creates TextStim for self.scaleDescription and self.labels
        """
        # text appearance (size, color, font, visibility):
        self.showValue = bool(showValue) # hide if False
        self.textColor = textColor  # rgb
        self.textFont = textFont
        self.textSize = 0.2 * textSize * self.size
        self.textSizeSmall = self.textSize * 0.6

        if self.choices or not scale:
            scale = ''
        elif scale == '<default>':
            scale = unicode(self.low) + u' = not at all . . . extremely = ' + unicode(self.high)

        # create the TextStim:
        self.scaleDescription = TextStim(win=self.win, height=self.textSizeSmall,
            pos=[self.offsetHoriz, 0.22 * self.size + self.offsetVert],
            color=self.textColor, wrapWidth=2 * self.hStretchTotal,
            font=textFont, autoLog=False)
        self.scaleDescription.setFont(textFont)
        self.labels = []
        if self.labelTexts:
            if self.markerStyle == 'hover':
                vertPosTmp = self.offsetVert  # on the line = clickable labels
            else:
                vertPosTmp = -2 * self.textSizeSmall * self.size + self.offsetVert
            for i, label in enumerate(self.labelTexts):
                # need all labels for tick position, i
                if label:  # skip '' placeholders, no need to create them
                    self.labels.append(TextStim(win=self.win, text=unicode(label), font=textFont,
                        pos=[self.tickPositions[i//self.autoRescaleFactor], vertPosTmp],
                        height=self.textSizeSmall, color=self.textColor, autoLog=False))
        self.setDescription(scale) # do after having set the relevant things

    def setDescription(self, scale=None, log=True):
        """Method to set the brief description (scale) that appears above the line.

        Useful when using the same RatingScale object to rate several dimensions.
        `setDescription(None)` will reset the description to its initial state.
        Set to a space character (' ') to make the description invisible.
        """
        if scale is None:
            scale = self.origScaleDescription
        self.scaleDescription.setText(scale)
        if log and self.autoLog:
            logging.exp('RatingScale %s: setDescription="%s"' % (self.name, self.scaleDescription.text))

    def _initAcceptBox(self, showAccept, acceptPreText, acceptText, acceptSize,
                       markerColor, textSizeSmall, textSize, textFont):
        """creates a ShapeStim for self.acceptBox (mouse-click-able 'accept'  button)
        and a TextStim for self.accept (container for the text shown inside the box)
        """
        if not showAccept: # then no point creating things that won't be used
            return

        self.acceptLineColor = [-.2, -.2, -.2]
        self.acceptFillColor = [.2, .2, .2]

        if self.labelTexts:
            boxVert = [0.3, 0.47]
        else:
            boxVert = [0.2, 0.37]

        # define self.acceptBox:
        sizeFactor = self.size * textSize
        leftRightAdjust = 0.04 + 0.2 * max(0.1, acceptSize) * sizeFactor
        self.acceptBoxtop = acceptBoxtop = self.offsetVert - boxVert[0] * sizeFactor
        self.acceptBoxbot = acceptBoxbot = self.offsetVert - boxVert[1] * sizeFactor
        self.acceptBoxleft = acceptBoxleft = self.offsetHoriz - leftRightAdjust
        self.acceptBoxright = acceptBoxright = self.offsetHoriz + leftRightAdjust

        # define a rectangle with rounded corners; for square corners, set delta2 to 0
        delta = 0.025 * self.size
        delta2 = delta / 7
        acceptBoxVertices = [
            [acceptBoxleft,acceptBoxtop-delta], [acceptBoxleft+delta2,acceptBoxtop-3*delta2],
            [acceptBoxleft+3*delta2,acceptBoxtop-delta2], [acceptBoxleft+delta,acceptBoxtop],
            [acceptBoxright-delta,acceptBoxtop], [acceptBoxright-3*delta2,acceptBoxtop-delta2],
            [acceptBoxright-delta2,acceptBoxtop-3*delta2], [acceptBoxright,acceptBoxtop-delta],
            [acceptBoxright,acceptBoxbot+delta],[acceptBoxright-delta2,acceptBoxbot+3*delta2],
            [acceptBoxright-3*delta2,acceptBoxbot+delta2], [acceptBoxright-delta,acceptBoxbot],
            [acceptBoxleft+delta,acceptBoxbot], [acceptBoxleft+3*delta2,acceptBoxbot+delta2],
            [acceptBoxleft+delta2,acceptBoxbot+3*delta2], [acceptBoxleft,acceptBoxbot+delta] ]
        # interpolation looks bad on linux, as of Aug 2010
        interpolate = bool(not sys.platform.startswith('linux'))
        self.acceptBox = ShapeStim(win=self.win, vertices=acceptBoxVertices,
            fillColor=self.acceptFillColor, lineColor=self.acceptLineColor,
            interpolate=interpolate, autoLog=False)

        # text to display inside accept button before a marker has been placed:
        if self.low > 0 and self.high < 10 and not self.mouseOnly:
            self.keyClick = 'key, click'
        else:
            self.keyClick = 'click line'
        if acceptPreText != 'key, click': # non-default
            self.keyClick = unicode(acceptPreText)
        self.acceptText = unicode(acceptText)

        # create the TextStim:
        self.accept = TextStim(win=self.win, text=self.keyClick, font=self.textFont,
            pos=[self.offsetHoriz, (acceptBoxtop + acceptBoxbot) / 2.],
            italic=True, height=textSizeSmall, color=self.textColor, autoLog=False)
        self.accept.setFont(textFont)

        self.acceptTextColor = markerColor
        if markerColor in ['White']:
            self.acceptTextColor = 'Black'

    def _getMarkerFromPos(self, mouseX):
        """Convert mouseX into units of tick marks, 0 .. high-low, fractional if precision > 1
        """
        value = min(max(mouseX, self.lineLeftEnd), self.lineRightEnd)
        # map mouseX==0 -> mid-point of tick scale:
        _tickStretch = self.tickMarks / self.hStretchTotal
        markerPos = (value - self.offsetHoriz) * _tickStretch + self.tickMarks/2.
        return round(markerPos * self.scaledPrecision) / self.scaledPrecision

    def _getMarkerFromTick(self, tick):
        """Convert a requested tick value into a position on the internal scale.
        Accounts for non-zero low end, autoRescale, and precision.
        """
        # ensure its on the line:
        value = max(min(self.high, tick), self.low)
        # set requested precision:
        value = round(value * self.scaledPrecision) / self.scaledPrecision
        return (value - self.low) * self.autoRescaleFactor

    def setMarkerPos(self, tick):
        """Method to allow the experimenter to set the marker's position on the
        scale (in units of tick marks). This method can also set the index within
        a list of choices (which start at 0). No range checking is done.

        Assuming you have defined rs = RatingScale(...), you can specify a tick
        position directly::

            rs.setMarkerPos(2)

        or do range checking, precision management, and auto-rescaling::

            rs.setMarkerPos(rs._getMarkerFromTick(2))

        To work from a screen coordinate, such as the X position of a mouse click::

            rs.setMarkerPos(rs._getMarkerFromPos(mouseX))

        """
        self.markerPlacedAt = tick
        self.markerPlaced = True # only needed first time, which this ensures

    def setFlipVert(self, newVal=True, log=True):
        """Sets current vertical mirroring to ``newVal``.
        """
        if self.flipVert != newVal:
            self.flipVert = not self.flipVert
            self.markerYpos *= -1
            groupFlipVert([self.nearLine, self.marker] + self.visualDisplayElements)
        logAttrib(self, log, 'flipVert')

    # autoDraw and setAutoDraw are inherited from basevisual.MinimalStim

    def draw(self, log=True):
        """Update the visual display, check for response (key, mouse, skip).

        Sets response flags: `self.noResponse`, `self.timedOut`.
        `draw()` only draws the rating scale, not the item to be rated.
        """
        self.win.units = 'norm'  # original units do get restored
        if self.firstDraw:
            self.firstDraw = False
            self.clock.reset()
            self.status = STARTED
            if self.markerStart:  # has been converted in index if given as str
                if (self.markerStart % 1 or self.markerStart < 0
                    or self.markerStart > self.high or self.choices is False):
                    first = self.markerStart
                else:
                    first = self.choices[int(self.markerStart)]  # back to str for history
            else:
                first = None
            self.history = [(first, 0.0)]  # this will grow
            self.beyondMinTime = False  # has minTime elapsed?
            self.timedOut = False

        if not self.beyondMinTime:
            self.beyondMinTime = bool(self.clock.getTime() > self.minTime)
        # beyond maxTime = timed out? max < min means never allow time-out
        if self.allowTimeOut and not self.timedOut and self.maxTime < self.clock.getTime():
            # only do this stuff once
            self.timedOut = True
            self.noResponse = False
            # getRT() returns a value because noResponse==False
            self.history.append((self.getRating(), self.getRT()))
            if log and self.autoLog:
                logging.data('RatingScale %s: rating=%s (no response, timed out after %.3fs)' %
                         (self.name, unicode(self.getRating()), self.maxTime) )
                logging.data('RatingScale %s: rating RT=%.3fs' % (self.name, self.getRT()) )

        # 'disappear' == draw nothing if subj is done:
        if self.noResponse == False and self.disappear:
            self.win.units = self.savedWinUnits
            return

        # draw everything except the marker:
        for visualElement in self.visualDisplayElements:
            visualElement.draw()

        # draw a fixed marker if the scale is being drawn after a response:
        if self.noResponse == False:
            # fix the marker position on the line
            if not self.markerPosFixed:
                try:
                    self.marker.setFillColor('DarkGray', log=False)
                except AttributeError:
                    try:
                        self.marker.setColor('DarkGray', log=False)
                    except:
                        pass
                self.marker.setPos((0, -.012), ('+', '-')[self.flipVert], log=False)  # drop it onto the line
                self.markerPosFixed = True  # flag to park it there
            self.marker.draw()
            if self.showAccept:
                self.acceptBox.draw()  # hides the text
            self.win.units = self.savedWinUnits
            return  # makes the marker unresponsive

        mouseX, mouseY = self.myMouse.getPos() # norm units
        mouseNearLine = pointInPolygon(mouseX, mouseY, self.nearLine)

        # draw a dynamic marker:
        if self.markerPlaced or self.singleClick:
            # expansion for 'glow', based on proportion of total line
            proportion = self.markerPlacedAt / self.tickMarks
            if self.markerStyle == 'glow' and self.markerExpansion != 0:
                if self.markerExpansion > 0:
                    newSize = 0.1 * self.markerExpansion * proportion
                    newOpacity = 0.2 + proportion
                else:  # self.markerExpansion < 0:
                    newSize = - 0.1 * self.markerExpansion * (1 - proportion)
                    newOpacity = 1.2 - proportion
                self.marker.setSize(self.markerBaseSize + newSize, log=False)
                self.marker.setOpacity(min(1, max(0, newOpacity)), log=False)
            # update position:
            if self.singleClick and mouseNearLine:
                self.setMarkerPos(self._getMarkerFromPos(mouseX))
            elif not hasattr(self, 'markerPlacedAt'):
                self.markerPlacedAt = False
            # set the marker's screen position based on tick (== markerPlacedAt)
            if self.markerPlacedAt is not False:
                x = self.offsetHoriz + self.hStretchTotal * (-0.5 + proportion)
                self.marker.setPos((x, self.markerYpos), log=False)
                self.marker.draw()
            if self.showAccept and self.markerPlacedBySubject:
                self.frame = (self.frame + 1) % 100
                self.acceptBox.setFillColor(self.pulseColor[self.frame], log=False)
                self.acceptBox.setLineColor(self.pulseColor[self.frame], log=False)
                self.accept.setColor(self.acceptTextColor, log=False)
                if self.showValue and self.markerPlacedAt is not False:
                    if self.choices:
                        val = unicode(self.choices[int(self.markerPlacedAt)])
                    else:
                        valTmp = self.markerPlacedAt + self.low
                        val = self.fmtStr % (valTmp * self.autoRescaleFactor)
                    self.accept.setText(val)
                elif self.markerPlacedAt is not False:
                    self.accept.setText(self.acceptText)

        # handle key responses:
        if not self.mouseOnly:
            for key in event.getKeys(self.allKeys):
                if key in self.skipKeys:
                    self.markerPlacedAt = None
                    self.noResponse = False
                    self.history.append((None, self.getRT()))
                elif key in self.respKeys and self.enableRespKeys:
                    # place the marker at the corresponding tick (from key)
                    self.markerPlaced = True
                    self.markerPlacedBySubject = True
                    resp = self.tickFromKeyPress[key]
                    self.markerPlacedAt = self._getMarkerFromTick(resp)
                    proportion = self.markerPlacedAt / self.tickMarks
                    self.marker.setPos([self.size * (-0.5 + proportion), 0], log=False)
                if self.markerPlaced and self.beyondMinTime:
                    # can be placed by experimenter (markerStart) or by subject
                    if (self.markerPlacedBySubject or self.markerStart is None or
                        not self.markerStart % self.keyIncrement):
                        # inefficient to do every frame...
                        leftIncrement = rightIncrement = self.keyIncrement
                    else:
                        # markerStart is fractional; arrow keys move to next location
                        leftIncrement = self.markerStart % self.keyIncrement
                        rightIncrement = self.keyIncrement - leftIncrement
                    if key in self.leftKeys:
                        self.markerPlacedAt = self.markerPlacedAt - leftIncrement
                        self.markerPlacedBySubject = True
                    elif key in self.rightKeys:
                        self.markerPlacedAt = self.markerPlacedAt + rightIncrement
                        self.markerPlacedBySubject = True
                    elif key in self.acceptKeys:
                        self.noResponse = False
                        self.history.append((self.getRating(), self.getRT()))  # RT when accept pressed
                        logging.data('RatingScale %s: (key response) rating=%s' %
                                         (self.name, unicode(self.getRating())) )
                    # off the end?
                    self.markerPlacedAt = max(0, self.markerPlacedAt)
                    self.markerPlacedAt = min(self.tickMarks, self.markerPlacedAt)

                if (self.markerPlacedBySubject and self.singleClick
                        and self.beyondMinTime):
                    self.noResponse = False
                    self.marker.setPos((0, self.offsetVert), '+', log=False)
                    if log and self.autoLog:
                        logging.data('RatingScale %s: (key single-click) rating=%s' %
                                 (self.name, unicode(self.getRating())) )

        # handle mouse left-click:
        if self.myMouse.getPressed()[0]:
            #mouseX, mouseY = self.myMouse.getPos() # done above
            # if click near the line, place the marker there:
            if mouseNearLine:
                self.markerPlaced = True
                self.markerPlacedBySubject = True
                self.markerPlacedAt = self._getMarkerFromPos(mouseX)
                if self.singleClick and self.beyondMinTime:
                    self.noResponse = False
                    if log and self.autoLog:
                        logging.data('RatingScale %s: (mouse single-click) rating=%s' %
                                 (self.name, unicode(self.getRating())) )
            # if click in accept box and conditions are met, accept the response:
            elif (self.showAccept and self.markerPlaced and self.beyondMinTime and
                    self.acceptBox.contains(mouseX, mouseY)):
                self.noResponse = False  # accept the currently marked value
                self.history.append((self.getRating(), self.getRT()))
                if log and self.autoLog:
                    logging.data('RatingScale %s: (mouse response) rating=%s' %
                            (self.name, unicode(self.getRating())) )

        if self.markerStyle == 'hover' and self.markerPlaced:
            if mouseNearLine or self.markerPlacedAt != self.markerPlacedAtLast:
                if hasattr(self, 'targetWord'):
                    self.targetWord.setColor(self.textColor, log=False)
                    self.targetWord.setHeight(self.textSizeSmall, log=False)
                self.targetWord = self.labels[int(self.markerPlacedAt)]
                self.targetWord.setColor(self.markerColor, log=False)
                self.targetWord.setHeight(1.05 * self.textSizeSmall, log=False)
                self.markerPlacedAtLast = self.markerPlacedAt
            elif not mouseNearLine and self.wasNearLine:
                self.targetWord.setColor(self.textColor, log=False)
                self.targetWord.setHeight(self.textSizeSmall, log=False)
            self.wasNearLine = mouseNearLine

        # decision time = secs from first .draw() to when first 'accept' value:
        if not self.noResponse and self.decisionTime == 0:
            self.decisionTime = self.clock.getTime()
            if log and self.autoLog:
                logging.data('RatingScale %s: rating RT=%.3f' % (self.name, self.decisionTime))
                logging.data('RatingScale %s: history=%s' % (self.name, self.getHistory()))
            # minimum time is enforced during key and mouse handling
            self.status = FINISHED
            if self.showAccept:
                self.acceptBox.setFillColor(self.acceptFillColor, log=False)
                self.acceptBox.setLineColor(self.acceptLineColor, log=False)

        # build up response history:
        tmpRating = self.getRating()
        if self.history[-1][0] != tmpRating and self.markerPlacedBySubject:
            self.history.append((tmpRating, self.getRT()))  # tuple

        # restore user's units:
        self.win.units = self.savedWinUnits

    def reset(self, log=True):
        """Restores the rating-scale to its post-creation state.

        The history is cleared, and the status is set to NOT_STARTED. Does not
        restore the scale text description (such reset is needed between
        items when rating multiple items)
        """
        # only resets things that are likely to have changed when the ratingScale instance is used by a subject
        self.noResponse = True
        self.markerPlaced = False  # placed by subject or markerStart: show on screen
        self.markerPlacedBySubject = False  # placed by subject is actionable: show value, singleClick
        self.markerPlacedAt = False
        #NB markerStart could be 0; during __init__, its forced to be numeric and valid, or None (not boolean)
        if self.markerStart != None:
            self.markerPlaced = True
            self.markerPlacedAt = self.markerStart - self.low # __init__ assures this is valid
        self.markerPlacedAtLast = -1  # unplaced
        self.wasNearLine = False
        self.firstDraw = True # triggers self.clock.reset() at start of draw()
        self.decisionTime = 0
        self.markerPosFixed = False
        self.frame = 0 # a counter used only to 'pulse' the 'accept' box

        if self.showAccept:
            self.acceptBox.setFillColor(self.acceptFillColor, log=False)
            self.acceptBox.setLineColor(self.acceptLineColor, log=False)
            self.accept.setColor('#444444', log=False)  # greyed out
            self.accept.setText(self.keyClick, log=False)
        if log and self.autoLog:
            logging.exp('RatingScale %s: reset()' % self.name)
        self.status = NOT_STARTED
        self.history = None

    def getRating(self):
        """Returns the final, accepted rating, or the current (non-accepted) value.

        The rating is None if the subject skipped this item, took longer than ``maxTime``, or no rating is
        available yet. Returns the currently indicated rating even if it has
        not been accepted yet (and so might change until accept is pressed). The
        first rating in the list will have the value of
        markerStart (whether None, a numeric value, or a choice value).
        """
        if self.noResponse and self.status == FINISHED:
            return None
        if not type(self.markerPlacedAt) in [float, int]:
            return None # eg, if skipped a response

        if self.precision == 1: # set type for the response, based on what was wanted
            response = int(self.markerPlacedAt * self.autoRescaleFactor) + self.low
        else:
            response = float(self.markerPlacedAt) * self.autoRescaleFactor + self.low
        if self.choices:
            try:
                response = self.choices[response]
            except:
                pass
                # == we have a numeric fractional choice from markerStart and
                # want to save the numeric value as first item in the history
        return response

    def getRT(self):
        """Returns the seconds taken to make the rating (or to indicate skip).

        Returns None if no rating available, or maxTime if the response timed out.
        Returns the time elapsed so far if no rating has been accepted yet (e.g.,
        for continuous usage).
        """
        if self.status != FINISHED:
            return round(self.clock.getTime(), 3)
        if self.noResponse:
            if self.timedOut:
                return round(self.maxTime, 3)
            return None
        return round(self.decisionTime, 3)

    def getHistory(self):
        """Return a list of the subject's selection history as (rating, time) tuples.

        The history can be retrieved at any time, allowing for continuous ratings to be
        obtained in real-time. Both numerical and categorical choices are stored
        automatically in the history.
        """
        return self.history
