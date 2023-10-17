#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A class for getting numeric or categorical ratings, e.g., a 1-to-7 scale."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import sys
import numpy

from psychopy import core, logging, event
from psychopy.visual.circle import Circle
from psychopy.visual.patch import PatchStim
from psychopy.visual.shape import ShapeStim
from psychopy.visual.text import TextStim
from psychopy.visual.basevisual import MinimalStim
from psychopy.visual.helpers import pointInPolygon, groupFlipVert
from psychopy.tools.attributetools import logAttrib
from psychopy.constants import FINISHED, STARTED, NOT_STARTED


class RatingScale(MinimalStim):
    """A class for obtaining ratings, e.g., on a 1-to-7 or categorical scale.
    This is a lazy-imported class, therefore import using full path 
    `from psychopy.visual.ratingscale import RatingScale` when inheriting
    from it.

    A RatingScale instance is a re-usable visual object having a ``draw()``
    method, with customizable appearance and response options. ``draw()``
    displays the rating scale, handles the subject's mouse or key responses,
    and updates the display. When the subject accepts a selection,
    ``.noResponse`` goes ``False`` (i.e., there is a response).

    You can call the ``getRating()`` method anytime to get a rating,
    ``getRT()`` to get the decision time, or ``getHistory()`` to obtain
    the entire set of (rating, RT) pairs.

    There are five main elements of a rating scale: the `scale`
    (text above the line intended to be a reminder of how to use the scale),
    the `line` (with tick marks), the `marker` (a moveable visual indicator
    on the line), the `labels` (text below the line that label specific
    points), and the `accept` button. The appearance and function of
    elements can be customized by the experimenter; it is not possible
    to orient a rating scale to be vertical. Multiple scales can be
    displayed at the same time, and continuous real-time ratings can be
    obtained from the history.

    The Builder RatingScale component gives a restricted set of options,
    but also allows full control over a RatingScale via the
    'customize_everything' field.

    A RatingScale instance has no idea what else is on the screen.
    The experimenter has to draw the item to be rated, and handle `escape`
    to break or quit, if desired. The subject can use the mouse or keys to
    respond. Direction keys (left, right) will move the marker in the
    smallest available increment (e.g., 1/10th of a tick-mark if
    precision = 10).

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

        For fMRI, sometimes only a keyboard can be used. If your response
        box sends keys 1-4, you could specify left, right, and accept keys,
        and not need a mouse::

            ratingScale = visual.RatingScale(
                win, low=1, high=5, markerStart=4,
                leftKeys='1', rightKeys = '2', acceptKeys='4')

    **Example 3**:

        Categorical ratings can be obtained using choices::

            ratingScale = visual.RatingScale(
                win, choices=['agree', 'disagree'],
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
                 colorSpace='rgb',
                 skipKeys='tab',
                 mouseOnly=False,
                 noMouse=False,
                 size=1.0,
                 stretch=1.0,
                 pos=None,
                 minTime=0.4,
                 maxTime=0.0,
                 flipVert=False,
                 depth=0,
                 name=None,
                 autoLog=True,
                 **kwargs):  # catch obsolete args
        """
    :Parameters:

        win :
            A :class:`~psychopy.visual.Window` object (required).
        choices :
            A list of items which the subject can choose among.
            ``choices`` takes precedence over ``low``, ``high``,
            ``precision``, ``scale``, ``labels``, and ``tickMarks``.
        low :
            Lowest numeric rating (integer), default = 1.
        high :
            Highest numeric rating (integer), default = 7.
        precision :
            Portions of a tick to accept as input [1, 10, 60, 100];
            default = 1 (a whole tick).
            Pressing a key in `leftKeys` or `rightKeys` will move the
            marker by one portion of a tick. precision=60 is intended to
            support ratings of time-based quantities, with seconds being
            fractional minutes (or minutes being fractional hours).
            The display uses a colon (min:sec, or hours:min)
            to signal this to participants. The value returned by getRating()
            will be a proportion of a minute (e.g., 1:30 -> 1.5, or 59 seconds
            -> 59/60 = 0.98333). hours:min:sec is not supported.
        scale :
            Optional reminder message about how to respond or rate an item,
            displayed above the line; default =
            '<low>=not at all, <high>=extremely'.
            To suppress the scale, set ``scale=None``.
        labels :
            Text to be placed at specific tick marks to indicate their value.
            Can be just the ends (if given 2 labels), ends + middle
            (if given 3 labels),
            or all points (if given the same number of labels as points).
        tickMarks :
            List of positions at which tick marks should be placed from low
            to high.
            The default is to space tick marks equally, one per integer value.
        tickHeight :
            The vertical height of tick marks: 1.0 is the default height
            (above line), -1.0 is below the line, and 0.0 suppresses the
            display of tickmarks. ``tickHeight`` is purely cosmetic, and can
            be fractional, e.g., 1.2.
        marker :
            The moveable visual indicator of the current selection. The
            predefined styles are 'triangle', 'circle', 'glow', 'slider',
            and 'hover'. A slider moves smoothly when there are enough
            screen positions to move through, e.g., low=0, high=100.
            Hovering requires a set of choices, and allows clicking directly
            on individual choices; dwell-time is not recorded.
            Can also be set to a custom marker stimulus: any object with
            a .draw() method and .pos will work, e.g.,
            ``visual.TextStim(win, text='[]', units='norm')``.
        markerStart :
            The location or value to be pre-selected upon initial display,
            either numeric or one of the choices. Can be fractional,
            e.g., midway between two options.
        markerColor :
            Color to use for a predefined marker style, e.g., 'DarkRed'.
        markerExpansion :
            Only affects the `glow` marker: How much to expand or
            contract when moving rightward; 0=none, negative shrinks.
        singleClick :
            Enable a mouse click to both select and accept the rating,
            default = ``False``.
            A legal key press will also count as a singleClick.
            The 'accept' box is visible, but clicking it has no effect.
        pos : tuple (x, y)
            Position of the rating scale on the screen. The midpoint of
            the line will be positioned at ``(x, y)``;
            default = ``(0.0, -0.4)`` in norm units
        size :
            How much to expand or contract the overall rating scale display.
            Default size = 1.0. For larger than the default, set
            ``size`` > 1; for smaller, set < 1.
        stretch:
            Like ``size``, but only affects the horizontal direction.
        textSize :
            The size of text elements, relative to the default size
            (i.e., a scaling factor, not points).
        textColor :
            Color to use for labels and scale text; default = 'LightGray'.
        textFont :
            Name of the font to use; default = 'Helvetica Bold'.
        showValue :
            Show the subject their current selection default = ``True``.
            Ignored if singleClick is ``True``.
        showAccept :
            Show the button to click to accept the current value by using
            the mouse; default = ``True``.
        acceptPreText :
            The text to display before any value has been selected.
        acceptText :
            The text to display in the 'accept' button after a value has
            been selected.
        acceptSize :
            The width of the accept box relative to the default
            (e.g., 2 is twice as wide).
        acceptKeys :
            A list of keys that are used to accept the current response;
            default = 'return'.
        leftKeys :
            A list of keys that each mean "move leftwards";
            default = 'left'.
        rightKeys :
            A list of keys that each mean "move rightwards";
            default = 'right'.
        respKeys :
            A list of keys to use for selecting choices, in the desired order.
            The first item will be the left-most choice, the second
            item will be the next choice, and so on.
        skipKeys :
            List of keys the subject can use to skip a response,
            default = 'tab'.
            To require a response to every item, set ``skipKeys=None``.
        lineColor :
            The RGB color to use for the scale line, default = 'White'.
        mouseOnly :
            Require the subject to use the mouse (any keyboard input is
            ignored), default = ``False``. Can be used to avoid competing
            with other objects for keyboard input.
        noMouse:
            Require the subject to use keys to respond; disable and
            hide the mouse.
            `markerStart` will default to the left end.
        minTime :
            Seconds that must elapse before a response can be accepted,
            default = `0.4`.
        maxTime :
            Seconds after which a response cannot be accepted.
            If ``maxTime`` <= ``minTime``, there's no time limit.
            Default = `0.0` (no time limit).
        disappear :
            Whether the rating scale should vanish after a value is accepted.
            Can be useful when showing multiple scales.
        flipVert :
            Whether to mirror-reverse the rating scale in the vertical
            direction.
    """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        super(RatingScale, self).__init__(name=name, autoLog=False)

        # warn about obsolete arguments; Jan 2014, for v1.80:
        obsoleted = {'showScale', 'ticksAboveLine', 'displaySizeFactor',
                     'markerStyle', 'customMarker', 'allowSkip',
                     'stretchHoriz', 'escapeKeys', 'textSizeFactor',
                     'showScale', 'showAnchors',
                     'lowAnchorText', 'highAnchorText'}
        obsArgs = set(kwargs.keys()).intersection(obsoleted)
        if obsArgs:
            msg = ('RatingScale obsolete args: %s; see changelog v1.80.00'
                   ' for notes on how to migrate')
            logging.error(msg % list(obsArgs))
            core.quit()
        # kwargs will absorb everything, including typos, so warn about bad
        # args
        unknownArgs = set(kwargs.keys()).difference(obsoleted)
        if unknownArgs:
            msg = "RatingScale unknown kwargs: %s"
            logging.error(msg % list(unknownArgs))
            core.quit()

        self.autoLog = False  # needs to start off False
        self.win = win
        self.disappear = disappear

        # internally work in norm units, restore to orig units at the end of
        # __init__:
        self.savedWinUnits = self.win.units
        self.win.setUnits(u'norm', log=False)
        self.depth = depth

        # 'hover' style = like hyperlink with hover over choices:
        if marker == 'hover':
            showAccept = False
            singleClick = True
            textSize *= 1.5
            mouseOnly = True
            noMouse = False

        self.colorSpace = colorSpace

        # make things well-behaved if the requested value(s) would be trouble:
        self._initFirst(showAccept, mouseOnly, noMouse, singleClick,
                        acceptKeys, marker, markerStart, low, high, precision,
                        choices, scale, tickMarks, labels, tickHeight)
        self._initMisc(minTime, maxTime)

        # Set scale & position, key-bindings:
        self._initPosScale(pos, size, stretch)
        self._initKeys(self.acceptKeys, skipKeys,
                       leftKeys, rightKeys, respKeys)

        # Construct the visual elements:
        self._initLine(tickMarkValues=tickMarks,
                       lineColor=lineColor, marker=marker)
        self._initMarker(marker, markerColor, markerExpansion)
        self._initTextElements(win, self.scale, textColor, textFont, textSize,
                               showValue, tickMarks)
        self._initAcceptBox(self.showAccept, acceptPreText, acceptText,
                            acceptSize, self.markerColor, self.textSizeSmall,
                            textSize, self.textFont)

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
        self.win.setUnits(self.savedWinUnits, log=False)

        self.timedOut = False
        self.beyondMinTime = False

        # set autoLog (now that params have been initialised)
        self.autoLog = autoLog
        if autoLog:
            logging.exp("Created %s = %s" % (self.name, repr(self)))

    def __repr__(self, complete=False):
        return self.__str__(complete=complete)  # from MinimalStim

    def _initFirst(self, showAccept, mouseOnly, noMouse, singleClick,
                   acceptKeys, marker, markerStart, low, high, precision,
                   choices, scale, tickMarks, labels, tickHeight):
        """some sanity checking; various things are set, especially those
        that are used later; choices, anchors, markerStart settings are
        handled here
        """
        self.showAccept = bool(showAccept)
        self.mouseOnly = bool(mouseOnly)
        self.noMouse = bool(noMouse) and not self.mouseOnly  # mouseOnly wins
        self.singleClick = bool(singleClick)
        self.acceptKeys = acceptKeys
        self.precision = precision
        self.labelTexts = None
        self.tickHeight = tickHeight

        if not self.showAccept:
            # the accept button is the mouse-based way to accept the current
            # response
            if len(list(self.acceptKeys)) == 0:
                # make sure there is in fact a way to respond using a
                # key-press:
                self.acceptKeys = ['return']
            if self.mouseOnly and not self.singleClick:
                # then there's no way to respond, so deny mouseOnly / enable
                # using keys:
                self.mouseOnly = False
                msg = ("RatingScale %s: ignoring mouseOnly (because "
                       "showAccept and singleClick are False)")
                logging.warning(msg % self.name)

        # 'choices' is a list of non-numeric (unordered) alternatives:
        if choices and len(list(choices)) < 2:
            msg = "RatingScale %s: choices requires 2 or more items"
            logging.error(msg % self.name)
        if choices and len(list(choices)) >= 2:
            low = 0
            high = len(list(choices)) - 1
            self.precision = 1  # a fractional choice makes no sense
            self.choices = choices
            self.labelTexts = choices
        else:
            self.choices = False
        if marker == 'hover' and not self.choices:
            logging.error("RatingScale: marker='hover' requires "
                          "a set of choices.")
            core.quit()

        # Anchors need to be well-behaved [do after choices]:
        try:
            self.low = int(low)
        except Exception:
            self.low = 1
        try:
            self.high = int(high)
        except Exception:
            self.high = self.low + 1
        if self.high <= self.low:
            self.high = self.low + 1
            self.precision = 100

        if not self.choices:
            diff = self.high - self.low
            if labels and len(labels) == 2:
                # label the endpoints
                first, last = labels[0], labels[-1]
                self.labelTexts = [first] + [''] * (diff - 1) + [last]
            elif labels and len(labels) == 3 and diff > 1 and (1 + diff) % 2:
                # label endpoints and middle tick
                placeHolder = [''] * ((diff - 2) // 2)
                self.labelTexts = ([labels[0]] + placeHolder +
                                   [labels[1]] + placeHolder +
                                   [labels[2]])
            elif labels in [None, False]:
                self.labelTexts = []
            else:
                first, last = str(self.low), str(self.high)
                self.labelTexts = [first] + [''] * (diff - 1) + [last]

        self.scale = scale
        if tickMarks and not labels is False:
            if labels is None:
                self.labelTexts = tickMarks
            else:
                self.labelTexts = labels
            if len(self.labelTexts) != len(tickMarks):
                msg = "RatingScale %s: len(labels) not equal to len(tickMarks)"
                logging.warning(msg % self.name)
                self.labelTexts = tickMarks
            if self.scale == "<default>":
                self.scale = False

        # Marker pre-positioned? [do after anchors]
        try:
            self.markerStart = float(markerStart)
        except Exception:
            if (isinstance(markerStart, str) and
                    type(self.choices) == list and
                    markerStart in self.choices):
                self.markerStart = self.choices.index(markerStart)
                self.markerPlacedAt = self.markerStart
                self.markerPlaced = True
            else:
                self.markerStart = None
                self.markerPlaced = False
        else:  # float(markerStart) succeeded
            self.markerPlacedAt = self.markerStart
            self.markerPlaced = True
        # default markerStart = 0 if needed but otherwise unspecified:
        if self.noMouse and self.markerStart is None:
            self.markerPlacedAt = self.markerStart = 0
            self.markerPlaced = True

    def _initMisc(self, minTime, maxTime):
        # precision is the fractional parts of a tick mark to be sensitive to,
        # in [1,10,100]:
        if type(self.precision) != int or self.precision < 10:
            self.precision = 1
            self.fmtStr = "%.0f"  # decimal places, purely for display
        elif self.precision == 60:
            self.fmtStr = "%d:%s"  # minutes:seconds.zfill(2)
        elif self.precision < 100:
            self.precision = 10
            self.fmtStr = "%.1f"
        else:
            self.precision = 100
            self.fmtStr = "%.2f"

        self.clock = core.Clock()  # for decision time
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

        self.myMouse = event.Mouse(
            win=self.win, visible=bool(not self.noMouse))
        # Mouse-click-able 'accept' button pulsates (cycles its brightness
        # over frames):
        framesPerCycle = 100
        self.pulseColor = [0.6 + 0.22 * numpy.cos(i/15.65)
                           for i in range(framesPerCycle)]

    def _initPosScale(self, pos, size, stretch, log=True):
        """position (x,y) and size (magnification) of the rating scale
        """
        # Screen position (translation) of the rating scale as a whole:
        if pos:
            if len(list(pos)) == 2:
                offsetHoriz, offsetVert = pos
            elif log and self.autoLog:
                msg = "RatingScale %s: pos expects a tuple (x,y)"
                logging.warning(msg % self.name)
        try:
            self.offsetHoriz = float(offsetHoriz)
        except Exception:
            if self.savedWinUnits == 'pix':
                self.offsetHoriz = 0
            else:  # default x in norm units:
                self.offsetHoriz = 0.0
        try:
            self.offsetVert = float(offsetVert)
        except Exception:
            if self.savedWinUnits == 'pix':
                self.offsetVert = int(self.win.size[1]/-5.0)
            else:  # default y in norm units:
                self.offsetVert = -0.4
        # pos=(x,y) will consider x,y to be in win units, but want norm
        # internally
        if self.savedWinUnits == 'pix':
            self.offsetHoriz = float(self.offsetHoriz) / self.win.size[0] / 0.5
            self.offsetVert = float(self.offsetVert) / self.win.size[1] / 0.5
        # just expose; not used elsewhere yet
        self.pos = [self.offsetHoriz, self.offsetVert]

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
            self.acceptKeys = []  # no valid keys, so must use mouse
        else:
            if type(acceptKeys) not in [list, tuple, set]:
                acceptKeys = [acceptKeys]
            self.acceptKeys = acceptKeys
        self.skipKeys = []
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
        nonRespKeys = (self.leftKeys + self.rightKeys + self.acceptKeys +
                       self.skipKeys)
        if respKeys and hasattr(respKeys, '__iter__'):
            self.respKeys = respKeys
            self.enableRespKeys = True
            if set(self.respKeys).intersection(nonRespKeys):
                msg = 'RatingScale %s: respKeys may conflict with other keys'
                logging.warning(msg % self.name)
        else:
            # allow resp via numeric keys if the response range is in 0-9
            self.respKeys = []
            if not self.mouseOnly and self.low > -1 and self.high < 10:
                self.respKeys = [str(i)
                                 for i in range(self.low, self.high + 1)]
            # but if any digit is used as an action key, that should
            # take precedence so disable using numeric keys:
            if set(self.respKeys).intersection(nonRespKeys) == set([]):
                self.enableRespKeys = True
            else:
                self.enableRespKeys = False
        if self.enableRespKeys:
            self.tickFromKeyPress = {}
            for i, key in enumerate(self.respKeys):
                self.tickFromKeyPress[key] = i + self.low

        # if self.noMouse:
        #     could check that there are appropriate response keys

        self.allKeys = nonRespKeys + self.respKeys

    def _initLine(self, tickMarkValues=None, lineColor='White', marker=None):
        """define a ShapeStim to be a graphical line, with tick marks.

        ### Notes (JRG Aug 2010)
        Conceptually, the response line is always -0.5 to +0.5
        ("internal" units). This line, of unit length, is scaled and
        translated for display. The line is effectively "center justified",
        expanding both left and right with scaling, with pos[] specifying
        the screen coordinate (in window units, norm or pix) of the
        mid-point of the response line. Tick marks are in integer units,
        internally 0 to (high-low), with 0 being the left end and (high-low)
        being the right end. (Subjects see low to high on the screen.)
        Non-numeric (categorical) choices are selected using tick-marks
        interpreted as an index, choice[tick]. Tick units get mapped to
        "internal" units based on their proportion of the total ticks
        (--> 0. to 1.). The unit-length internal line is expanded or
        contracted by stretch and size, and then is translated to
        position pos (offsetHoriz=pos[0], offsetVert=pos[1]).
        pos is the name of the arg, and its values appear in the code as
        offsetHoriz and offsetVert only for historical reasons (could be
        refactored for clarity).

        Auto-rescaling reduces the number of tick marks shown on the
        screen by a factor of 10, just for nicer appearance, without
        affecting the internal representation.

        Thus, the horizontal screen position of the i-th tick mark,
        where i in [0,n], for n total ticks (n = high-low),
        in screen units ('norm') will be:
          tick-i             == offsetHoriz + (-0.5 + i/n ) * stretch * size
        So two special cases are:
          tick-0 (left end)  == offsetHoriz - 0.5 * stretch * size
          tick-n (right end) == offsetHoriz + 0.5 * stretch * size
        The vertical screen position is just offsetVert (in screen norm units).
        To elaborate: tick-0 is the left-most tick, or "low anchor";
        here 0 is internal, the subject sees <low>.
        tick-n is the right-most tick, or "high anchor", or
        internal-tick-(high-low), and the subject sees <high>.
        Intermediate ticks, i, are located proportionally
        between -0.5 to + 0.5, based on their proportion
        of the total number of ticks, float(i)/n.
        The "proportion of total" is used because it's a line of unit length,
        i.e., the same length as used to internally represent the
        scale (-0.5 to +0.5).
        If precision > 1, the user / experimenter is asking for
        fractional ticks. These map correctly
        onto [0, 1] as well without requiring special handling
        (just do ensure float() ).

        Another note: -0.5 to +0.5 looked too big to be the default
        size of the rating line in screen norm units,
        so I set the internal size = 0.6 to compensate (i.e., making
        everything smaller). The user can adjust the scaling around
        the default by setting size, stretch, or both.
        This means that the user / experimenter can just think of > 1
        being expansion (and < 1 == contraction) relative to the default
        (internal) scaling, and not worry about the internal scaling.

        ### Notes (HS November 2012)
        To allow for labels at the ticks, the positions of the tick marks
        are saved in self.tickPositions. If tickMarks, those positions
        are used instead of the automatic positions.
        """

        self.lineColor = lineColor
        # vertical height of each tick, norm units; used for markers too:
        self.baseSize = 0.04
        # num tick marks to display, can get autorescaled
        self.tickMarks = float(self.high - self.low)
        self.autoRescaleFactor = 1

        if tickMarkValues:
            tickTmp = numpy.asarray(tickMarkValues, dtype=numpy.float32)
            tickMarkPositions = (tickTmp - self.low)/self.tickMarks
        else:
            # visually remap 10 ticks onto 1 tick in some conditions (=
            # cosmetic):
            if (self.low == 0 and
                    self.tickMarks > 20 and
                    int(self.tickMarks) % 10 == 0):
                self.autoRescaleFactor = 10
                self.tickMarks /= self.autoRescaleFactor
            tickMarkPositions = numpy.linspace(0, 1, int(self.tickMarks) + 1)
        self.scaledPrecision = float(self.precision * self.autoRescaleFactor)

        # how far a left or right key will move the marker, in tick units:
        self.keyIncrement = 1. / self.autoRescaleFactor / self.precision
        self.hStretchTotal = self.stretch * self.size

        # ends of the rating line, in norm units:
        self.lineLeftEnd = self.offsetHoriz - 0.5 * self.hStretchTotal
        self.lineRightEnd = self.offsetHoriz + 0.5 * self.hStretchTotal

        # space around the line within which to accept mouse input:
        # not needed if self.noMouse, but not a problem either
        pad = 0.06 * self.size
        if marker == 'hover':
            padText = ((1.0/(3 * (self.high - self.low))) *
                       (self.lineRightEnd - self.lineLeftEnd))
        else:
            padText = 0
        self.nearLine = [
            [self.lineLeftEnd - pad - padText, -2 * pad + self.offsetVert],
            [self.lineLeftEnd - pad - padText, 2 * pad + self.offsetVert],
            [self.lineRightEnd + pad + padText, 2 * pad + self.offsetVert],
            [self.lineRightEnd + pad + padText, -2 * pad + self.offsetVert]]

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
                              lineWidth=4, lineColor=self.lineColor,
                              name=self.name + '.line', autoLog=False)

    def _initMarker(self, marker, markerColor, expansion):
        """define a visual Stim to be used as the indicator.

        marker can be either a string, or a visual object (custom marker).
        """
        # preparatory stuff:
        self.markerOffsetVert = 0.
        if isinstance(marker, str):
            self.markerStyle = marker
        elif not hasattr(marker, 'draw'):
            logging.error("RatingScale: custom marker has no draw() method")
            self.markerStyle = 'triangle'
        else:
            self.markerStyle = 'custom'
            if hasattr(marker, 'pos'):
                self.markerOffsetVert = marker.pos[1]
            else:
                logging.error(
                    "RatingScale: custom marker has no pos attribute")

        self.markerSize = 8. * self.size
        if isinstance(markerColor, str):
            markerColor = markerColor.replace(' ', '')

        # define or create self.marker:
        if self.markerStyle == 'hover':
            self.marker = TextStim(win=self.win, text=' ', units='norm',
                                   autoLog=False)  # placeholder
            self.markerOffsetVert = .02
            if not markerColor:
                markerColor = 'darkorange'
        elif self.markerStyle == 'triangle':
            scaledTickSize = self.baseSize * self.size
            vert = [[-1 * scaledTickSize * 1.8, scaledTickSize * 3],
                    [scaledTickSize * 1.8, scaledTickSize * 3], [0, -0.005]]
            if markerColor is None:
                markerColor = 'DarkBlue'
            self.marker = ShapeStim(win=self.win, units='norm', vertices=vert,
                                    lineWidth=0.1, lineColor=markerColor,
                                    fillColor=markerColor,
                                    name=self.name + '.markerTri',
                                    autoLog=False)
        elif self.markerStyle == 'slider':
            scaledTickSize = self.baseSize * self.size
            vert = [[-1 * scaledTickSize * 1.8, scaledTickSize],
                    [scaledTickSize * 1.8, scaledTickSize],
                    [scaledTickSize * 1.8, -1 * scaledTickSize],
                    [-1 * scaledTickSize * 1.8, -1 * scaledTickSize]]
            if markerColor is None:
                markerColor = 'black'
            self.marker = ShapeStim(win=self.win, units='norm', vertices=vert,
                                    lineWidth=0.1, lineColor=markerColor,
                                    fillColor=markerColor,
                                    name=self.name + '.markerSlider',
                                    opacity=0.7, autoLog=False)
        elif self.markerStyle == 'glow':
            if markerColor is None:
                markerColor = 'White'
            self.marker = PatchStim(win=self.win, units='norm',
                                    tex=None, mask='gauss',
                                    color=markerColor, opacity=0.85,
                                    autoLog=False,
                                    name=self.name + '.markerGlow')
            self.markerBaseSize = self.baseSize * self.markerSize
            self.markerOffsetVert = .02
            self.markerExpansion = float(expansion) * 0.6
            if self.markerExpansion == 0:
                self.markerBaseSize *= self.markerSize * 0.7
                if self.markerSize > 1.2:
                    self.markerBaseSize *= .7
                self.marker.setSize(self.markerBaseSize/2.0, log=False)
        elif self.markerStyle == 'custom':
            if markerColor is None:
                if hasattr(marker, 'color'):
                    try:
                        # marker.color 0 causes problems elsewhere too
                        if not marker.color:
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
            if markerColor is None:
                markerColor = 'DarkRed'
            x, y = self.win.size
            windowRatio = y/x
            self.markerSizeVert = 3.2 * self.baseSize * self.size
            circleSize = [self.markerSizeVert *
                          windowRatio, self.markerSizeVert]
            self.markerOffsetVert = self.markerSizeVert/2.0
            self.marker = Circle(self.win, size=circleSize, units='norm',
                                 lineColor=markerColor, fillColor=markerColor,
                                 name=self.name + '.markerCir', autoLog=False)
            self.markerBaseSize = self.baseSize
        self.markerColor = markerColor
        self.markerYpos = self.offsetVert + self.markerOffsetVert
        # save initial state, restore on reset
        self.markerColorOriginal = markerColor

    def _initTextElements(self, win, scale, textColor,
                          textFont, textSize, showValue, tickMarks):
        """creates TextStim for self.scaleDescription and self.labels
        """
        # text appearance (size, color, font, visibility):
        self.showValue = bool(showValue)  # hide if False
        self.textColor = textColor  # rgb
        self.textFont = textFont
        self.textSize = 0.2 * textSize * self.size
        self.textSizeSmall = self.textSize * 0.6

        # set the description text if not already set by user:
        if scale == '<default>':
            if self.choices:
                scale = ''
            else:
                msg = u' = not at all . . . extremely = '
                scale = str(self.low) + msg + str(self.high)

        # create the TextStim:
        self.scaleDescription = TextStim(
            win=self.win, height=self.textSizeSmall,
            pos=[self.offsetHoriz, 0.22 * self.size + self.offsetVert],
            color=self.textColor, wrapWidth=2 * self.hStretchTotal,
            font=textFont, autoLog=False)
        self.scaleDescription.font = textFont
        self.labels = []
        if self.labelTexts:
            if self.markerStyle == 'hover':
                vertPosTmp = self.offsetVert  # on the line = clickable labels
            else:
                vertPosTmp = -2 * self.textSizeSmall * self.size + self.offsetVert
            for i, label in enumerate(self.labelTexts):
                # need all labels for tick position, i
                if label or label is not None: # 'is not None' allows creation of '0' (zero or false) labels
                    txtStim = TextStim(
                        win=self.win, text=str(label), font=textFont,
                        pos=[self.tickPositions[i // self.autoRescaleFactor],
                             vertPosTmp],
                        height=self.textSizeSmall, color=self.textColor,
                        autoLog=False)
                    self.labels.append(txtStim)
        self.origScaleDescription = scale
        self.setDescription(scale)  # do last

    def _setMarkerColor(self, color):
        """Set the fill color or color of the marker"""
        try:
            self.marker.setFillColor(color, colorSpace=self.colorSpace, log=False)
        except AttributeError:
            try:
                self.marker.setColor(color, colorSpace=self.colorSpace, log=False)
            except Exception:
                pass

    def setDescription(self, scale=None, log=True):
        """Method to set the brief description (scale).

        Useful when using the same RatingScale object to rate several
        dimensions. `setDescription(None)` will reset the description
        to its initial state. Set to a space character (' ') to make
        the description invisible.
        """
        if scale is None:
            scale = self.origScaleDescription
        self.scaleDescription.setText(scale)
        self.showScale = bool(scale)  # not in [None, False, '']
        if log and self.autoLog:
            logging.exp('RatingScale %s: setDescription="%s"' %
                        (self.name, self.scaleDescription.text))

    def _initAcceptBox(self, showAccept, acceptPreText, acceptText,
                       acceptSize, markerColor,
                       textSizeSmall, textSize, textFont):
        """creates a ShapeStim for self.acceptBox (mouse-click-able
        'accept'  button) and a TextStim for self.accept (container for
        the text shown inside the box)
        """
        if not showAccept:  # no point creating things that won't be used
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
        acceptBoxtop = self.offsetVert - boxVert[0] * sizeFactor
        self.acceptBoxtop = acceptBoxtop
        acceptBoxbot = self.offsetVert - boxVert[1] * sizeFactor
        self.acceptBoxbot = acceptBoxbot
        acceptBoxleft = self.offsetHoriz - leftRightAdjust
        self.acceptBoxleft = acceptBoxleft
        acceptBoxright = self.offsetHoriz + leftRightAdjust
        self.acceptBoxright = acceptBoxright

        # define a rectangle with rounded corners; for square corners, set
        # delta2 to 0
        delta = 0.025 * self.size
        delta2 = delta/7
        acceptBoxVertices = [
            [acceptBoxleft, acceptBoxtop - delta],
            [acceptBoxleft + delta2, acceptBoxtop - 3 * delta2],
            [acceptBoxleft + 3 * delta2, acceptBoxtop - delta2],
            [acceptBoxleft + delta, acceptBoxtop],
            [acceptBoxright - delta, acceptBoxtop],
            [acceptBoxright - 3 * delta2, acceptBoxtop - delta2],
            [acceptBoxright - delta2, acceptBoxtop - 3 * delta2],
            [acceptBoxright, acceptBoxtop - delta],
            [acceptBoxright, acceptBoxbot + delta],
            [acceptBoxright - delta2, acceptBoxbot + 3 * delta2],
            [acceptBoxright - 3 * delta2, acceptBoxbot + delta2],
            [acceptBoxright - delta, acceptBoxbot],
            [acceptBoxleft + delta, acceptBoxbot],
            [acceptBoxleft + 3 * delta2, acceptBoxbot + delta2],
            [acceptBoxleft + delta2, acceptBoxbot + 3 * delta2],
            [acceptBoxleft, acceptBoxbot + delta]]
        # interpolation looks bad on linux, as of Aug 2010
        interpolate = bool(not sys.platform.startswith('linux'))
        self.acceptBox = ShapeStim(
            win=self.win, vertices=acceptBoxVertices,
            fillColor=self.acceptFillColor, lineColor=self.acceptLineColor,
            interpolate=interpolate, autoLog=False)

        # text to display inside accept button before a marker is placed:
        if self.low > 0 and self.high < 10 and not self.mouseOnly:
            self.keyClick = 'key, click'
        else:
            self.keyClick = 'click line'
        if acceptPreText != 'key, click':  # non-default
            self.keyClick = str(acceptPreText)
        self.acceptText = str(acceptText)

        # create the TextStim:
        self.accept = TextStim(
            win=self.win, text=self.keyClick, font=self.textFont,
            pos=[self.offsetHoriz, (acceptBoxtop + acceptBoxbot)/2.0],
            italic=True, height=textSizeSmall, color=self.textColor,
            autoLog=False)
        self.accept.font = textFont

        self.acceptTextColor = markerColor
        if isinstance(markerColor, str):
            # warning raised if color not specified as a string
            if markerColor in ['White']:
                self.acceptTextColor = 'Black'

    def _getMarkerFromPos(self, mouseX):
        """Convert mouseX into units of tick marks, 0 .. high-low.

        Will be fractional if precision > 1
        """
        value = min(max(mouseX, self.lineLeftEnd), self.lineRightEnd)
        # map mouseX==0 -> mid-point of tick scale:
        _tickStretch = self.tickMarks/self.hStretchTotal
        adjValue = value - self.offsetHoriz
        markerPos = adjValue * _tickStretch + self.tickMarks/2.0
        # We need float value in getRating(), but round() returns
        # numpy.float64 if argument is numpy.float64 in Python3.
        # So we have to convert return value of round() to float.
        rounded = float(round(markerPos * self.scaledPrecision))
        return rounded/self.scaledPrecision

    def _getMarkerFromTick(self, tick):
        """Convert a requested tick value into a position on internal scale.

        Accounts for non-zero low end, autoRescale, and precision.
        """
        # ensure its on the line:
        value = max(min(self.high, tick), self.low)
        # set requested precision:
        value = round(value * self.scaledPrecision)//self.scaledPrecision
        return (value - self.low) * self.autoRescaleFactor

    def setMarkerPos(self, tick):
        """Method to allow the experimenter to set the marker's position
        on the scale (in units of tick marks). This method can also set
        the index within a list of choices (which start at 0).
        No range checking is done.

        Assuming you have defined rs = RatingScale(...), you can specify
        a tick position directly::

            rs.setMarkerPos(2)

        or do range checking, precision management, and auto-rescaling::

            rs.setMarkerPos(rs._getMarkerFromTick(2))

        To work from a screen coordinate, such as the X position of a
        mouse click::

            rs.setMarkerPos(rs._getMarkerFromPos(mouseX))

        """
        self.markerPlacedAt = tick
        self.markerPlaced = True  # only needed first time

    def setFlipVert(self, newVal=True, log=True):
        """Sets current vertical mirroring to ``newVal``.
        """
        if self.flipVert != newVal:
            self.flipVert = not self.flipVert
            self.markerYpos *= -1
            groupFlipVert([self.nearLine, self.marker] +
                          self.visualDisplayElements)
        logAttrib(self, log, 'flipVert')

    # autoDraw and setAutoDraw are inherited from basevisual.MinimalStim

    def acceptResponse(self, triggeringAction, log=True):
        """Commit and optionally log a response and the action.
        """
        self.noResponse = False
        self.history.append((self.getRating(), self.getRT()))
        if log and self.autoLog:
            vals = (self.name, triggeringAction, str(self.getRating()))
            logging.data('RatingScale %s: (%s) rating=%s' % vals)

    def setYPos(self, newPos = None):
        """
        This function can be called by the user to change the Y-positioning of the rating scale.
        X location remains unchanged.
        """
        oldXPos, oldYPos = self.offsetHoriz, self.offsetVert
        if not newPos is None:
            if len(list(newPos)) == 2:
                offsetHoriz, offsetVert = newPos
        self.offsetHoriz = float(offsetHoriz)
        self.offsetVert = float(offsetVert)
        for positions in self.visualDisplayElements: # change location of elements based on position arg
            if not positions.pos is None:
                if 'ShapeStim' in str(type(positions)):
                    offsetY = abs(oldYPos - positions.pos[1])
                    positions.setPos([positions.pos[0], self.offsetVert + offsetY])
                    if '.line' in positions.name:# then change Y location of marker and mouse click box
                        self.markerYpos = self.offsetVert
                        self.nearLine[0][1],self.nearLine[3][1] = offsetVert-.072, offsetVert-.072
                        self.nearLine[1][1], self.nearLine[2][1] = offsetVert +.072, offsetVert + .072
                if 'TextStim' in str(type(positions)):
                    offsetY = abs(oldYPos-positions.pos[1])
                    positions.setPos([positions.pos[0], self.offsetVert - offsetY])


    def draw(self, log=True):
        """Update the visual display, check for response (key, mouse, skip).

        Sets response flags: `self.noResponse`, `self.timedOut`.
        `draw()` only draws the rating scale, not the item to be rated.
        """
        self.win.setUnits(u'norm', log=False)  # get restored
        if self.firstDraw:
            self.firstDraw = False
            self.clock.reset()
            self.status = STARTED
            if self.markerStart:
                # has been converted in index if given as str
                if (self.markerStart % 1 or self.markerStart < 0 or
                        self.markerStart > self.high or
                        self.choices is False):
                    first = self.markerStart
                else:
                    # back to str for history
                    first = self.choices[int(self.markerStart)]
            else:
                first = None
            self.history = [(first, 0.0)]  # this will grow
            self.beyondMinTime = False  # has minTime elapsed?
            self.timedOut = False

        if not self.beyondMinTime:
            self.beyondMinTime = bool(self.clock.getTime() > self.minTime)
        # beyond maxTime = timed out? max < min means never allow time-out
        if (self.allowTimeOut and
                not self.timedOut and
                self.maxTime < self.clock.getTime()):
            # only do this stuff once
            self.timedOut = True
            self.acceptResponse('timed out: %.3fs' % self.maxTime, log=log)

        # 'disappear' == draw nothing if subj is done:
        if self.noResponse == False and self.disappear:
            self.win.setUnits(self.savedWinUnits, log=False)
            return

        # draw everything except the marker:
        for visualElement in self.visualDisplayElements:
            visualElement.draw()

        # draw a fixed marker if the scale is being drawn after a response:
        if self.noResponse == False:
            # fix the marker position on the line
            if not self.markerPosFixed:
                self._setMarkerColor('DarkGray')

                # drop it onto the line
                self.marker.setPos((0, -.012), ('+', '-')[self.flipVert],
                                   log=False)
                self.markerPosFixed = True  # flag to park it there
            self.marker.draw()
            if self.showAccept:
                self.acceptBox.draw()  # hides the text
            self.win.setUnits(self.savedWinUnits, log=False)
            return  # makes the marker unresponsive

        if self.noMouse:
            mouseNearLine = False
        else:
            mouseX, mouseY = self.myMouse.getPos()  # norm units
            mouseNearLine = pointInPolygon(mouseX, mouseY, self.nearLine)

        # draw a dynamic marker:
        if self.markerPlaced or self.singleClick:
            # update position:
            if self.singleClick and mouseNearLine:
                self.setMarkerPos(self._getMarkerFromPos(mouseX))
            proportion = self.markerPlacedAt/self.tickMarks
            # expansion for 'glow', based on proportion of total line
            if self.markerStyle == 'glow' and self.markerExpansion != 0:
                if self.markerExpansion > 0:
                    newSize = 0.1 * self.markerExpansion * proportion
                    newOpacity = 0.2 + proportion
                else:  # self.markerExpansion < 0:
                    newSize = - 0.1 * self.markerExpansion * (1 - proportion)
                    newOpacity = 1.2 - proportion
                self.marker.setSize(self.markerBaseSize + newSize, log=False)
                self.marker.setOpacity(min(1, max(0, newOpacity)), log=False)
            # set the marker's screen position based on tick (==
            # markerPlacedAt)
            if self.markerPlacedAt is not False:
                x = self.offsetHoriz + self.hStretchTotal * (-0.5 + proportion)
                self.marker.setPos((x, self.markerYpos), log=False)
                self.marker.draw()
            if self.showAccept and self.markerPlacedBySubject:
                self.frame = (self.frame + 1) % 100
                self.acceptBox.setFillColor(
                    self.pulseColor[self.frame], colorSpace=self.colorSpace, log=False)
                self.acceptBox.setLineColor(
                    self.pulseColor[self.frame], colorSpace=self.colorSpace, log=False)
                self.accept.setColor(self.acceptTextColor, colorSpace=self.colorSpace, log=False)
                if self.showValue and self.markerPlacedAt is not False:
                    if self.choices:
                        val = str(self.choices[int(self.markerPlacedAt)])
                    elif self.precision == 60:
                        valTmp = self.markerPlacedAt + self.low
                        minutes = int(valTmp)  # also works for hours:minutes
                        seconds = int(60. * (valTmp - minutes))
                        val = self.fmtStr % (minutes, str(seconds).zfill(2))
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
                    proportion = self.markerPlacedAt/self.tickMarks
                    self.marker.setPos(
                        [self.size * (-0.5 + proportion), 0], log=False)
                if self.markerPlaced and self.beyondMinTime:
                    # placed by experimenter (as markerStart) or by subject
                    if (self.markerPlacedBySubject or
                            self.markerStart is None or
                            not self.markerStart % self.keyIncrement):
                        # inefficient to do every frame...
                        leftIncr = rightIncr = self.keyIncrement
                    else:
                        # markerStart is fractional; arrow keys move to next
                        # location
                        leftIncr = self.markerStart % self.keyIncrement
                        rightIncr = self.keyIncrement - leftIncr
                    if key in self.leftKeys:
                        self.markerPlacedAt = self.markerPlacedAt - leftIncr
                        self.markerPlacedBySubject = True
                    elif key in self.rightKeys:
                        self.markerPlacedAt = self.markerPlacedAt + rightIncr
                        self.markerPlacedBySubject = True
                    elif key in self.acceptKeys:
                        self.acceptResponse('key response', log=log)
                    # off the end?
                    self.markerPlacedAt = max(0, self.markerPlacedAt)
                    self.markerPlacedAt = min(
                        self.tickMarks, self.markerPlacedAt)

                if (self.markerPlacedBySubject and self.singleClick
                        and self.beyondMinTime):
                    self.marker.setPos((0, self.offsetVert), '+', log=False)
                    self.acceptResponse('key single-click', log=log)

        # handle mouse left-click:
        if not self.noMouse and self.myMouse.getPressed()[0]:
            # mouseX, mouseY = self.myMouse.getPos() # done above
            # if click near the line, place the marker there:
            if mouseNearLine:
                self.markerPlaced = True
                self.markerPlacedBySubject = True
                self.markerPlacedAt = self._getMarkerFromPos(mouseX)
                if self.singleClick and self.beyondMinTime:
                    self.acceptResponse('mouse single-click', log=log)
            # if click in accept box and conditions are met, accept the
            # response:
            elif (self.showAccept and
                    self.markerPlaced and
                    self.beyondMinTime and
                    self.acceptBox.contains(mouseX, mouseY)):
                self.acceptResponse('mouse response', log=log)

        if self.markerStyle == 'hover' and self.markerPlaced:
            # 'hover' --> noMouse = False during init
            if (mouseNearLine or
                    self.markerPlacedAt != self.markerPlacedAtLast):
                if hasattr(self, 'targetWord'):
                    self.targetWord.setColor(self.textColor, colorSpace=self.colorSpace, log=False)
                    # self.targetWord.setHeight(self.textSizeSmall, log=False)
                    # # avoid TextStim memory leak
                self.targetWord = self.labels[int(self.markerPlacedAt)]
                self.targetWord.setColor(self.markerColor, colorSpace=self.colorSpace, log=False)
                # skip size change to reduce mem leakage from pyglet text
                # self.targetWord.setHeight(1.05*self.textSizeSmall,log=False)
                self.markerPlacedAtLast = self.markerPlacedAt
            elif not mouseNearLine and self.wasNearLine:
                self.targetWord.setColor(self.textColor, colorSpace=self.colorSpace, log=False)
                # self.targetWord.setHeight(self.textSizeSmall, log=False)
            self.wasNearLine = mouseNearLine

        # decision time = sec from first .draw() to when first 'accept' value:
        if not self.noResponse and self.decisionTime == 0:
            self.decisionTime = self.clock.getTime()
            if log and self.autoLog:
                logging.data('RatingScale %s: rating RT=%.3f' %
                             (self.name, self.decisionTime))
                logging.data('RatingScale %s: history=%s' %
                             (self.name, self.getHistory()))
            # minimum time is enforced during key and mouse handling
            self.status = FINISHED
            if self.showAccept:
                self.acceptBox.setFillColor(self.acceptFillColor, colorSpace=self.colorSpace, log=False)
                self.acceptBox.setLineColor(self.acceptLineColor, colorSpace=self.colorSpace, log=False)
        else:
            # build up response history if no decision or skip yet:
            tmpRating = self.getRating()
            if (self.history[-1][0] != tmpRating and
                    self.markerPlacedBySubject):
                self.history.append((tmpRating, self.getRT()))  # tuple

        # restore user's units:
        self.win.setUnits(self.savedWinUnits, log=False)

    def reset(self, log=True):
        """Restores the rating-scale to its post-creation state.

        The history is cleared, and the status is set to NOT_STARTED. Does
        not restore the scale text description (such reset is needed between
        items when rating multiple items)
        """
        # only resets things that are likely to have changed when the
        # ratingScale instance is used by a subject
        # reset label color if using hover
        if self.markerStyle == 'hover':
            for labels in self.labels:
                labels.setColor(self.textColor, colorSpace=self.colorSpace, log=False)
        self.noResponse = True
        # restore in case it turned gray, etc
        self.markerColor = self.markerColorOriginal
        self._setMarkerColor(self.markerColor)
        # placed by subject or markerStart: show on screen
        self.markerPlaced = False
        # placed by subject is actionable: show value, singleClick
        self.markerPlacedBySubject = False
        self.markerPlacedAt = False
        # NB markerStart could be 0; during __init__, its forced to be numeric
        # and valid, or None (not boolean)
        if self.markerStart != None:
            self.markerPlaced = True
            # __init__ assures this is valid:
            self.markerPlacedAt = self.markerStart - self.low
        self.markerPlacedAtLast = -1  # unplaced
        self.wasNearLine = False
        self.firstDraw = True  # -> self.clock.reset() at start of draw()
        self.decisionTime = 0
        self.markerPosFixed = False
        self.frame = 0  # a counter used only to 'pulse' the 'accept' box

        if self.showAccept:
            self.acceptBox.setFillColor(self.acceptFillColor, colorSpace=self.colorSpace, log=False)
            self.acceptBox.setLineColor(self.acceptLineColor, colorSpace=self.colorSpace, log=False)
            self.accept.setColor('#444444', colorSpace='hex', log=False)  # greyed out
            self.accept.setText(self.keyClick, log=False)
        if log and self.autoLog:
            logging.exp('RatingScale %s: reset()' % self.name)
        self.status = NOT_STARTED
        self.history = None

    def getRating(self):
        """Returns the final, accepted rating, or the current value.

        The rating is None if the subject skipped this item, took longer
        than ``maxTime``, or no rating is
        available yet. Returns the currently indicated rating even if it has
        not been accepted yet (and so might change until accept is pressed).
        The first rating in the list will have the value of
        markerStart (whether None, a numeric value, or a choice value).
        """
        if self.noResponse and self.status == FINISHED:
            return None
        if not type(self.markerPlacedAt) in [float, int]:
            return None  # eg, if skipped a response

        # set type for the response, based on what was wanted
        val = self.markerPlacedAt * self.autoRescaleFactor
        if self.precision == 1:
            response = int(val) + self.low
        else:
            response = float(val) + self.low
        if self.choices:
            try:
                response = self.choices[response]
            except Exception:
                pass
                # == we have a numeric fractional choice from markerStart and
                # want to save the numeric value as first item in the history
        return response

    def getRT(self):
        """Returns the seconds taken to make the rating (or to indicate skip).

        Returns None if no rating available, or maxTime if the response
        timed out. Returns the time elapsed so far if no rating has been
        accepted yet (e.g., for continuous usage).
        """
        if self.status != FINISHED:
            return round(self.clock.getTime(), 3)
        if self.noResponse:
            if self.timedOut:
                return round(self.maxTime, 3)
            return None
        return round(self.decisionTime, 3)

    def getHistory(self):
        """Return a list of the subject's history as (rating, time) tuples.

        The history can be retrieved at any time, allowing for continuous
        ratings to be obtained in real-time. Both numerical and categorical
        choices are stored automatically in the history.
        """
        return self.history
