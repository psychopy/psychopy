#!/usr/bin/env python2

'''A class for getting numeric or categorical ratings, e.g., a 1-to-7 scale.'''

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import print_function

import copy
import sys
import numpy as np
import pandas as pd

from psychopy import core, logging, event
from psychopy.colors import isValidColor
from psychopy.visual.circle import Circle
from psychopy.visual.line import Line
from psychopy.visual.patch import PatchStim
from psychopy.visual.shape import ShapeStim
from psychopy.visual.text import TextStim
from psychopy.visual.basevisual import MinimalStim
from psychopy.visual.helpers import pointInPolygon, groupFlipVert
from psychopy.tools.attributetools import logAttrib
from psychopy.tools.monitorunittools import convertToPix, pix2cm, pix2deg
from psychopy.constants import FINISHED, STARTED, NOT_STARTED
from psychopy.tools.attributetools import attributeSetter


class RatingScale(MinimalStim):
    """A class for obtaining ratings, e.g., on a 1-to-7 or categorical scale.

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
                first, last = unicode(self.low), unicode(self.high)
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
            if (isinstance(markerStart, basestring) and
                    type(self.choices) == list and
                    markerStart in self.choices):
                self.markerStart = self.choices.index(markerStart)
                self.markerPlacedAt = self.markerStart
                self.markerPlaced = True
            else:
                self.markerStart = None
                self.markerPlaced = False
        else:  # float(markerStart) suceeded
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
        self.pulseColor = [0.6 + 0.22 * float(np.cos(i / 15.65))
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
                self.offsetVert = int(self.win.size[1] / -5.0)
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
            tickTmp = np.asarray(tickMarkValues, dtype=np.float32)
            tickMarkPositions = (tickTmp - self.low) / self.tickMarks
        else:
            # visually remap 10 ticks onto 1 tick in some conditions (=
            # cosmetic):
            if (self.low == 0 and
                    self.tickMarks > 20 and
                    int(self.tickMarks) % 10 == 0):
                self.autoRescaleFactor = 10
                self.tickMarks /= self.autoRescaleFactor
            tickMarkPositions = np.linspace(0, 1, self.tickMarks + 1)
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
            padText = ((1. / (3 * (self.high - self.low))) *
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
                logging.error(
                    "RatingScale: custom marker has no pos attribute")

        self.markerSize = 8. * self.size
        if isinstance(markerColor, basestring):
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
            if markerColor is None or not isValidColor(markerColor):
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
            if markerColor is None or not isValidColor(markerColor):
                markerColor = 'black'
            self.marker = ShapeStim(win=self.win, units='norm', vertices=vert,
                                    lineWidth=0.1, lineColor=markerColor,
                                    fillColor=markerColor,
                                    name=self.name + '.markerSlider',
                                    opacity=0.7, autoLog=False)
        elif self.markerStyle == 'glow':
            if markerColor is None or not isValidColor(markerColor):
                markerColor = 'White'
            self.marker = PatchStim(win=self.win, units='norm',
                                    tex='sin', mask='gauss',
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
                self.marker.setSize(self.markerBaseSize / 2., log=False)
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
            if markerColor is None or not isValidColor(markerColor):
                markerColor = 'DarkRed'
            x, y = self.win.size
            windowRatio = float(y) / x
            self.markerSizeVert = 3.2 * self.baseSize * self.size
            circleSize = [self.markerSizeVert *
                          windowRatio, self.markerSizeVert]
            self.markerOffsetVert = self.markerSizeVert / 2.
            self.marker = Circle(self.win, size=circleSize, units='norm',
                                 lineColor=markerColor, fillColor=markerColor,
                                 name=self.name + '.markerCir', autoLog=False)
            self.markerBaseSize = self.baseSize
        self.markerColor = markerColor
        self.markerYpos = self.offsetVert + self.markerOffsetVert
        # save initial state, restore on reset
        self.markerOrig = copy.copy(self.marker)

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
                scale = unicode(self.low) + msg + unicode(self.high)

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
                if label:  # skip '' placeholders, no need to create them
                    txtStim = TextStim(
                        win=self.win, text=unicode(label), font=textFont,
                        pos=[self.tickPositions[i // self.autoRescaleFactor],
                             vertPosTmp],
                        height=self.textSizeSmall, color=self.textColor,
                        autoLog=False)
                    self.labels.append(txtStim)
        self.origScaleDescription = scale
        self.setDescription(scale)  # do last

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
        delta2 = delta / 7
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
            self.keyClick = unicode(acceptPreText)
        self.acceptText = unicode(acceptText)

        # create the TextStim:
        self.accept = TextStim(
            win=self.win, text=self.keyClick, font=self.textFont,
            pos=[self.offsetHoriz, (acceptBoxtop + acceptBoxbot) / 2.],
            italic=True, height=textSizeSmall, color=self.textColor,
            autoLog=False)
        self.accept.font = textFont

        self.acceptTextColor = markerColor
        if markerColor in ['White']:
            self.acceptTextColor = 'Black'

    def _getMarkerFromPos(self, mouseX):
        """Convert mouseX into units of tick marks, 0 .. high-low.

        Will be fractional if precision > 1
        """
        value = min(max(mouseX, self.lineLeftEnd), self.lineRightEnd)
        # map mouseX==0 -> mid-point of tick scale:
        _tickStretch = self.tickMarks / self.hStretchTotal
        adjValue = value - self.offsetHoriz
        markerPos = adjValue * _tickStretch + self.tickMarks / 2.
        rounded = round(markerPos * self.scaledPrecision)
        return rounded / self.scaledPrecision

    def _getMarkerFromTick(self, tick):
        """Convert a requested tick value into a position on internal scale.

        Accounts for non-zero low end, autoRescale, and precision.
        """
        # ensure its on the line:
        value = max(min(self.high, tick), self.low)
        # set requested precision:
        value = round(value * self.scaledPrecision) / self.scaledPrecision
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
            vals = (self.name, triggeringAction, unicode(self.getRating()))
            logging.data('RatingScale %s: (%s) rating=%s' % vals)

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
                try:
                    self.marker.setFillColor('DarkGray', log=False)
                except AttributeError:
                    try:
                        self.marker.setColor('DarkGray', log=False)
                    except Exception:
                        pass
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
            proportion = self.markerPlacedAt / self.tickMarks
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
                    self.pulseColor[self.frame], log=False)
                self.acceptBox.setLineColor(
                    self.pulseColor[self.frame], log=False)
                self.accept.setColor(self.acceptTextColor, log=False)
                if self.showValue and self.markerPlacedAt is not False:
                    if self.choices:
                        val = unicode(self.choices[int(self.markerPlacedAt)])
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
                    proportion = self.markerPlacedAt / self.tickMarks
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
                    self.targetWord.setColor(self.textColor, log=False)
                    # self.targetWord.setHeight(self.textSizeSmall, log=False)
                    # # avoid TextStim memory leak
                self.targetWord = self.labels[int(self.markerPlacedAt)]
                self.targetWord.setColor(self.markerColor, log=False)
                # skip size change to reduce mem leakage from pyglet text
                # self.targetWord.setHeight(1.05*self.textSizeSmall,log=False)
                self.markerPlacedAtLast = self.markerPlacedAt
            elif not mouseNearLine and self.wasNearLine:
                self.targetWord.setColor(self.textColor, log=False)
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
                self.acceptBox.setFillColor(self.acceptFillColor, log=False)
                self.acceptBox.setLineColor(self.acceptLineColor, log=False)
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
        self.noResponse = True
        # restore in case it turned gray, etc
        self.marker = copy.copy(self.markerOrig)
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
            self.acceptBox.setFillColor(self.acceptFillColor, log=False)
            self.acceptBox.setLineColor(self.acceptLineColor, log=False)
            self.accept.setColor('#444444', log=False)  # greyed out
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


class SimpleRatingScale(MinimalStim):
    def __init__(self, win, ori='horiz', limits=(0, 100), precision=None,
                 ticks=None, tickLabels=None, tickLoc='both',
                 labelLoc=None, color='black', markerColor='red',
                 colorSpace=None, pos=(0, 0), size=1, tickSize=None,
                 mousePos=None, units=None, lineWidth=3, labelPadding=None,
                 maxTime=10, finishOnResponse=True, resetOnFirstFlip=True,
                 iohub=False, name=None, autoLog=True):
        """
        A simple and minimalistic, yet flexible continuous rating scale that
        supports both horizontal and vertical alignment.

        Parameters
        ----------
        win : :class:`visual.Window`
            The window the rating scale should be attached to.

        ori : {'horiz', 'horizontal', 'vert', 'vertical'}
            The orientation of the scale.

        limits : array-like of length 2
            An iterable of length 2 containing the minimum and maximum
            values of the rating scale.

        precision : float, or `None
            The granularity, or step width between values the scale can
            differentiate. The scale will be internally divided into
            1/precision sections of equal length (e.g., 100 sections for
            `precision=100). The value range
            (`max - min`) of the scale must be divisable
            by `precision` (i.e., `(max - min) % precision == 0`).

            If `None`, will automatidally divide the scale into 100 sections
            of equal length.

        ticks : array-like, or `None`
            The positions (in scale values) of the tick marks on the scale.

        tickLabels : array-like, or `None`
            The labels corresponding to the tick marks specified as `ticks`.

        tickLoc : {'left', 'right', 'top', 'bottom', 'both'}
            The direction in which the tick labels expand. Please note that for
            a horizontal orientation of the scale, only the values `top`,
            `bottom`, and `both` are accepted; for a vertical scale, `left`,
            `right`, and `both` are valued options. The labels are
            automatically placed bases on this parameter. This can be
            overridden by specifying `labelLoc`.

        labelLoc : {'left', 'right', 'top', 'bottom', 'both'}
            The location of the tick labels, relative to the scale. The
            same restrictions as with `tickLoc` apply.

        color : string, or array-like
            The color of the scale. The color space can be specified using the
            `colorSpace` parameter.

        markerColor : string, or array-like
            The color of the marker, which appears when clicking on the scale.
            The color space can be specified using the `colorSpace` parameter.

        colorSpace : string, or None
            The color space used to interpret color specifications. If `None`
            specified, the default color space of the window is used.

        pos : array-like
            The center position of the scale on the screen. The units can be
            specified via the `units` parameter; otherwise, the window's
            default units are used.

        size : float
            The size of the scale on the screen. The units can be
            specified via the `units` parameter; otherwise, the window's
            default units are used.

        tickSize : float, or `None`
            The size (width or height, respectively) of the tick marks.
            The units can be specified via the `units` parameter; otherwise,
            the window's default units are used. If `None`, a sane default
            value is chosen.

        mousePos : array-like, or `None`
            An iterable of length 2 containing `x` and `y` coordinates.
            This parameter can be used to set the mouse cursor to a specific
            position when the scale is first displayed. The units can be
            specified via the `units` parameter; otherwise, the window's
            default units are used. If `None`, the mouse cursor position
            is not changed when the scale appears.

        units : {'norm', 'height', 'pix', 'pixels', 'deg', 'degs', 'degFlat',
                 'degFlatPos'}, or `None`
            The units in which all size- and position-related parameters are
            specified. If `None, the window's default units are used.

        lineWidth : float
            The width of the lines used to draw the scale, tick marks, and
            marker. The parameter is passed to :class:`visual.line.Line`.

        labelPadding : float, or None
            The padding between the scale and the tick labels.
            The units can be specified via the `units` parameter; otherwise,
            the window's default units are used. If `None`, a sane default
            value is chosen.

        maxTime : float
            The maximum time the participant is allowed to make a response.

        finishOnResponse : bool
            If `True`, :class:`visual.ratingscale.SimpleRatingScale`'s `status`
            is set to `FINISHED` once a response is collected. If `False`, will
            always wait until `maxTime` before finishing, even if a response
            was collected earlier alreay.

        resetOnFirstFlip : bool
            Whether to reset the scale, including the response timer, the
            first time the window is flipped after calling
            :fuc:~`visual.ratingscale.SimpleRatingScale.draw`.

        iohub : bool
            Whether to acquire respone times via the ioHub mouse device. Will
            try to automatically connect to a running ioHub server process.

        name : string, or `None`
            The name to associate with this stimulus. Will appear in the log
            files.

        autoLog : bool
            Whether or not to enable automatic logging of noteworthy events.

        Attributes
        ----------
        All properties set via keyword parameters are available as attributes
        with the names. Additionally, the following attributes are exposed to
        allow access to the recorded response:

        rt : float
            The measured response time, im seconds.

        response : float
            The acquired rating.

        The following attributes can be changed after instantiation:

            - `mousePos`
            - `maxTime`
            - `finishOnResponse`
            - `resetOnFirstFlip`
            - `autoLog`

        Raises
        ------
        ValueError
            When incompatible parameter combinations are supplied

        ImportError
            If usage of ioHub is requested, but the ioHub package cannot be
            imported.

        RuntimeError
            When something unexpected happens (i.e., a bug).

        Notes
        -----
        We maintain a complete lookup table of the positions of all visual
        elements and their corresponding values on the rating scale in
        `self._coords`. All coordinate unites correspond to the units specified
        via the `units` keyword argument, or to the window's units if
        `units=None`.

        When setting `iohub=True`, iohub will be used for determination of the
        response time only, immediately after
        :fuc:~`event.Mouse.isPressedIn` notifies us of a click inside the
        ratingscale's bounding box. We will then query the latest button press
        event (and corresponding event time) from ioHub's event buffer.

        Examples
        --------
        See the code examples folder for demonstrations how to use the
        `SimpleRatingScale`.

        """
        self._initParams = dir()

        self._check_args(ticks, tickLabels, tickLoc, labelLoc, limits,
                         precision, ori, units)

        super(SimpleRatingScale, self).__init__(name=name, autoLog=False)

        self._win = win
        self._ori = ori
        self._limits = limits
        self._min = np.float(limits[0])
        self._max = np.float(limits[1])

        if precision is not None:
            self._precision = np.float(precision)
        else:
            self._precision = (self._max - self._min) / 100

        self._pos = pos
        self._size = np.float(size)
        self._units = units if units is not None else win.units
        self._color = color
        self._marker_color = markerColor
        self._color_space = (colorSpace if colorSpace is not None
                             else win.colorSpace)
        self._line_width = lineWidth

        if self._ori in ['horiz', 'horizontal']:
            self._scale_dim = 0  # Scale expands horizontally.
            self._tick_dim = 1   # Ticks expand vertically.
        else:
            self._scale_dim = 1  # Scale expands vertically.
            self._tick_dim = 0   # Ticks expand horizontally.

        self._tick_size = (tickSize if tickSize is not None
                           else self._gen_default_size(0.05, self._tick_dim))

        if ticks is not None:
            self._ticks = np.array(ticks)
        else:
            self._ticks = np.array([self._min, self._max])

        if tickLabels is not None:
            self._tick_labels = tickLabels
        else:
            self._tick_labels = ['low', 'high']

        self._label_padding = (labelPadding if labelPadding is not None
                               else self._gen_default_size(0.07,
                                                           self._tick_dim))

        self._tick_loc = tickLoc

        self._label_loc = (labelLoc if labelLoc is not None
                           else self._gen_default_label_loc())

        (self._tick_label_halign,
         self._tick_label_valign) = self._gen_default_tick_label_alignments()

        self._iohub = iohub
        self._mouse, self._io, self._io_mouse = self._init_mouse()

        self._coords = self._gen_coords()
        self._visual_elements = self._gen_visual_elements()
        self._bounding_box = self._gen_bounding_box()
        self._timer = core.CountdownTimer()
        self._response = None
        self._rt = None
        self._time_start = None
        self._orig_units = win.units
        self._status = NOT_STARTED
        self._first_flip = True

        # User-settable attributes.
        self.__dict__['mousePos'] = mousePos
        self.__dict__['maxTime'] = maxTime
        self.__dict__['finishOnResponse'] = finishOnResponse
        self.__dict__['resetOnFirstFlip'] = resetOnFirstFlip

        self.autoLog = autoLog
        if self.autoLog:
            logging.exp('Created %s = %s' % (self.name, repr(self)))

    def __repr__(self, complete=False):
        return self.__str__(complete=complete)

    # User-settable attributes.
    # NB: self.autoLog not listed here, inherited from base class.
    @attributeSetter
    def mousePos(self, pos):
        self.__dict__['mousePos'] = pos

    @attributeSetter
    def maxTime(self, t):
        self.__dict__['maxTime'] = t

    @attributeSetter
    def finishOnResponse(self, finish_on_response):
        self.__dict__['finishOnResponse'] = finish_on_response

    @attributeSetter
    def resetOnFirstFlip(self, reset_on_first_flip):
        self.__dict__['resetOnFirstFlip'] = reset_on_first_flip

    # Read-only attributes.
    @property
    def win(self):
        return self._win

    @property
    def ori(self):
        return self._ori

    @property
    def limits(self):
        return self._limits

    @property
    def precision(self):
        return self._precision

    @property
    def pos(self):
        return self._pos

    @property
    def size(self):
        return self._size

    @property
    def units(self):
        return self._units

    @property
    def color(self):
        return self._color

    @property
    def markerColor(self):
        return self._marker_color

    @property
    def colorSpace(self):
        return self._color_space

    @property
    def lineWidth(self):
        return self._line_width

    @property
    def tickSize(self):
        return self._tick_size

    @property
    def ticks(self):
        return self._ticks

    @property
    def tickLabels(self):
        return self._tick_labels

    @property
    def tickLoc(self):
        return self._tick_loc

    @property
    def labelLoc(self):
        return self._label_loc

    @property
    def labelPadding(self):
        return self._label_padding

    @property
    def iohub(self):
        return self._iohub

    @property
    def rt(self):
        return self._rt

    @property
    def response(self):
        return self._response

    @staticmethod
    def _check_args(ticks, tickLabels, tickLoc, labelLoc, limits,
                    precision, ori, units):
        if (ticks is not None) and (tickLabels is None):
            msg = 'You specified `ticks`, but no corresponding `tickLabels`.'
            raise ValueError(msg)
        elif (ticks is None) and (tickLabels is not None):
            msg = 'You specified `tickLabels`, but no corresponding `ticks`.'
            raise ValueError(msg)
        elif (ticks is not None) and (tickLabels is not None):
            if len(ticks) != len(tickLabels):
                msg = ('`ticks` and `tickLabels` must contain the same number '
                       'of elements!')
                raise ValueError(msg)

            if (any(np.array(ticks) < limits[0]) or
                    any(np.array(ticks) > limits[1])):
                msg = 'Tick values must lie in the interval [minVal, maxVal].'
                raise ValueError(msg)

        if tickLoc not in [None, 'top', 'bottom', 'left', 'right', 'both']:
            msg = '`tickLoc` must be one of: top, bottom, left, right, both'
            raise ValueError(msg)

        if labelLoc not in [None, 'top', 'bottom', 'left', 'right']:
            msg = '`labelLoc` must be one of: top, bottom, left, right'
            raise ValueError(msg)

        if ori not in [None, 'horiz', 'horizontal', 'vert', 'vertical']:
            msg = '`ori` must be one of: horiz, horizontal, vert, vertical'
            raise ValueError(msg)

        if (ori in ['horiz', 'horizontal'] and
                    tickLoc not in ['top', 'bottom', 'both']):
            msg = ('Invalid combination of `ori` and `tickLoc`: %s, %s' %
                   (ori, tickLoc))
            raise ValueError(msg)

        if (ori in ['vert', 'vertical'] and
                    tickLoc not in ['left', 'right', 'both']):
            msg = ('Invalid combination of `ori` and `tickLoc`: %s, %s' %
                   (ori, tickLoc))
            raise ValueError(msg)

        if (ori in ['horiz', 'horizontal'] and
                    labelLoc not in [None, 'top', 'bottom']):
            msg = ('Invalid combination of `ori` and `labelLoc`: %s, %s' %
                   (ori, labelLoc))
            raise ValueError(msg)

        if (ori in ['vert', 'vertical'] and
                    labelLoc not in [None, 'left', 'right']):
            msg = ('Invalid combination of `ori` and `labelLoc`: %s, %s' %
                   (ori, labelLoc))
            raise ValueError(msg)

        if ((precision is not None) and
                not np.isclose((limits[1] - limits[0]) % precision, 0)):
            msg = '`max - min` must be a multiple of `precision`.'
            raise ValueError(msg)

        if units not in [None, 'norm', 'height', 'pix', 'pixels', 'cm', 'deg',
                         'degs', 'degFlat', 'degFlatPos']:
            msg = 'Unsupported screen units requested: %s' % units
            raise ValueError(msg)

    def _init_mouse(self):
        if self.iohub:
            from psychopy import iohub
            self._iohub_package = iohub

            io = self._iohub_package.client.ioHubConnection.ACTIVE_CONNECTION
            if io is None:
                msg = ('Cannot find active ioHub connection! Please ensure '
                       'that ioHub is running.')
                raise RuntimeError(msg)

            io_mouse = io.devices.mouse
            mouse = event.Mouse(win=self.win)
        else:
            io = None
            io_mouse = None
            mouse = event.Mouse(win=self.win)

        return mouse, io, io_mouse

    def _gen_default_label_loc(self):
        if self.tickLoc == 'top':
            label_loc = 'bottom'
        elif self.tickLoc == 'bottom':
            label_loc = 'top'
        elif self.tickLoc == 'left':
            label_loc = 'right'
        elif self.tickLoc == 'right':
            label_loc = 'left'
        elif self.tickLoc == 'both' and self.ori == 'vert':
            label_loc = 'right'
        elif self.tickLoc == 'both' and self.ori == 'horiz':
            label_loc = 'bottom'
        else:
            msg = ('You have encountered a bug. Please contact the '
                   'developers.')
            raise RuntimeError(msg)

        return label_loc

    def _gen_default_tick_label_alignments(self):
        if self.labelLoc == 'top':
            halign = 'center'
            valign = 'bottom'
        elif self.labelLoc == 'bottom':
            halign = 'center'
            valign = 'top'
        elif self.labelLoc == 'left':
            halign = 'right'
            valign = 'center'
        elif self.labelLoc == 'right':
            halign = 'left'
            valign = 'center'
        else:
            msg = 'You have encountered a bug. Please contact the developers.'
            raise RuntimeError(msg)

        return halign, valign

    def _gen_default_size(self, size_norm, dim):
        # We first convert the size to pixels, because pixels can be
        # conveniently transformed to all other required units.
        size_vertex_norm = np.zeros(2)
        size_vertex_norm[dim] = size_norm
        size_vertex_pix = convertToPix(size_vertex_norm, (0, 0), 'norm',
                                       self.win)

        size_pix = size_vertex_pix[dim]

        if self.units == 'norm':
            size = size_norm
        elif self.units == 'height':
            if dim == 1:  # Vertical dimension.
                size = size_norm
            else:  # Horizontal dimension.
                size = size_norm * (self.win.size[0] / self.win.size[1])
        elif self.units in ['pix', 'pixels']:
            size = size_pix
        elif self.units == 'cm':
            size = pix2cm(size_pix, self.win.monitor)
        elif self.units in ['deg', 'degs', 'degFlat', 'degFlatPos']:
            size = pix2deg(size_pix, self.win.monitor)
        else:
            msg = 'You have encountered a bug. Please contact the developers.'
            raise RuntimeError(msg)

        return size

    def _gen_coords(self):
        scale_values = np.linspace(self._min, self._max,
                                   (self._max - self._min)/self.precision + 1)

        pos_scale_axis = [(self.pos[self._scale_dim] - self.size / 2.0 +
                           (i * self.precision / (self._max - self._min) *
                            self.size))
                          for i, _ in enumerate(scale_values)]

        pos_tick_axis = [self.pos[self._tick_dim]] * len(pos_scale_axis)

        coords = pd.DataFrame(
            {'pos_scale_axis': pos_scale_axis,
             'pos_tick_axis': pos_tick_axis,
             'has_tickmark': [False],
             'label': [None]},
            index=pd.Index(scale_values, name='value')
        )

        coords.loc[self.ticks, 'has_tickmark'] = True
        coords.loc[self.ticks, 'label'] = self.tickLabels
        return coords

    def _gen_visual_elements(self):
        line_kwargs = dict(lineWidth=self.lineWidth, lineColor=self.color,
                           lineColorSpace=self.colorSpace, units=self.units,
                           autoLog=False)
        text_kwargs = dict(color=self.color, colorSpace=self.colorSpace,
                           units=self.units,
                           alignHoriz=self._tick_label_halign,
                           alignVert=self._tick_label_valign, autoLog=False)
        marker_kwargs = dict(lineWidth=self.lineWidth,
                             lineColor=self.markerColor,
                             lineColorSpace=self.colorSpace, units=self.units,
                             autoLog=False)

        visual_elements = []
        visual_elements.append(self._gen_scale(**line_kwargs))
        visual_elements.extend(self._gen_tick_marks(**line_kwargs))
        visual_elements.extend(self._gen_tick_labels(**text_kwargs))
        visual_elements.append(self._gen_selection_marker(**marker_kwargs))
        return visual_elements

    def _gen_scale(self, **line_kwargs):
        """
        The scale itself, without ticks or labels.
        """
        coords = self._coords

        if self.ori == 'horiz':
            start = np.array(
                [coords['pos_scale_axis'].iloc[0],
                 coords['pos_tick_axis'].iloc[0]])
            end = np.array(
                [coords['pos_scale_axis'].iloc[-1],
                 coords['pos_tick_axis'].iloc[-1]])
        else:
            start = np.array(
                [coords['pos_tick_axis'].iloc[0],
                 coords['pos_scale_axis'].iloc[0]])
            end = np.array(
                [coords['pos_tick_axis'].iloc[-1],
                 coords['pos_scale_axis'].iloc[-1]])

        scale = Line(self.win, start=start, end=end, **line_kwargs)
        return scale

    def _gen_tick_marks(self, **line_kwargs):
        coords = self._coords
        tick_marks = []

        for _, tick in coords.loc[self.ticks].iterrows():
            start = np.empty(2)
            end = np.empty(2)

            if self.tickLoc in ['top', 'right']:
                start[self._tick_dim] = tick['pos_tick_axis']
                start[self._scale_dim] = tick['pos_scale_axis']
                end[self._tick_dim] = tick['pos_tick_axis'] + self.tickSize
                end[self._scale_dim] = tick['pos_scale_axis']
            elif self.tickLoc in ['bottom', 'left']:
                start[self._tick_dim] = tick['pos_tick_axis']
                start[self._scale_dim] = tick['pos_scale_axis']
                end[self._tick_dim] = tick['pos_tick_axis'] - self.tickSize
                end[self._scale_dim] = tick['pos_scale_axis']
            else:
                start[self._tick_dim] = tick['pos_tick_axis'] - self.tickSize
                start[self._scale_dim] = tick['pos_scale_axis']
                end[self._tick_dim] = tick['pos_tick_axis'] + self.tickSize
                end[self._scale_dim] = tick['pos_scale_axis']

            tick_mark = Line(self.win, start=start, end=end, **line_kwargs)
            tick_marks.append(tick_mark)

        return tick_marks

    def _gen_tick_labels(self, **text_kwargs):
        coords = self._coords
        tick_labels = []

        for _, tick in coords.loc[self.ticks].iterrows():
            label_text = tick['label']
            pos = np.empty(2)

            if self.labelLoc in ['top', 'right']:
                pos[self._tick_dim] = tick['pos_tick_axis'] + self.labelPadding
                pos[self._scale_dim] = tick['pos_scale_axis']
            else:
                pos[self._tick_dim] = tick['pos_tick_axis'] - self.labelPadding
                pos[self._scale_dim] = tick['pos_scale_axis']

            tick_label = TextStim(self.win, text=label_text, pos=pos,
                                  **text_kwargs)
            tick_labels.append(tick_label)

        return tick_labels

    def _gen_selection_marker(self, **line_kwargs):
        """
        The participant-placed marker. It won't be drawn until a rating has
        been recorded. Initially, it will be created at an arbitrary position.
        """
        start = np.zeros(2)
        start[self._tick_dim] = -self.tickSize

        end = np.zeros(2)
        end[self._tick_dim] = self.tickSize

        marker = Line(self.win, start=start, end=end, **line_kwargs)
        return marker

    def _gen_bounding_box(self):
        """
        The bounding box in which mouse clicks are accepted as responses.
        """
        pos_scale_axis = self._coords['pos_scale_axis']
        pos_tick_axis = self._coords['pos_tick_axis']

        # Vertices.
        v0 = np.empty(2)
        v1 = np.empty(2)
        v2 = np.empty(2)
        v3 = np.empty(2)

        v0[self._scale_dim] = pos_scale_axis.iloc[0] - self.tickSize
        v0[self._tick_dim] = pos_tick_axis.iloc[0] - self.tickSize

        v1[self._scale_dim] = pos_scale_axis.iloc[0] - self.tickSize
        v1[self._tick_dim] = pos_tick_axis.iloc[0] + self.tickSize

        v2[self._scale_dim] = pos_scale_axis.iloc[-1] + self.tickSize
        v2[self._tick_dim] = pos_tick_axis.iloc[-1] + self.tickSize

        v3[self._scale_dim] = pos_scale_axis.iloc[-1] + self.tickSize
        v3[self._tick_dim] = pos_tick_axis.iloc[-1] - self.tickSize

        vertices = [v0, v1, v2, v3]
        return ShapeStim(self.win, units=self.units, vertices=vertices,
                         autoLog=False)

    def _check_for_response(self, finish_on_response):
        coords = self._coords

        if self._mouse.isPressedIn(self._bounding_box, buttons=[0]):
            # We got a response!

            self.win.units = self.units
            mouse_pos = self._mouse.getPos()
            self.win.units = self._orig_units

            if self.iohub:
                # Get the LAST registered button press. It has to be the
                # last one (and not the first) so we don't accidentally fetch
                # click on the screen area outside the scale that may have
                # occurred previously.
                press_event = self._io_mouse.getEvents(
                    event_type=(self._iohub_package
                                .EventConstants.MOUSE_BUTTON_PRESS))[-1]
                rt = press_event.time - self._time_start
            else:
                _, rt = self._mouse.getPressed(getTime=True)
                rt = rt[0]  # Only get response from left mouse button.

            # Which rating was closest to the mouse click position?
            _diff = (coords['pos_scale_axis'] -
                     mouse_pos[self._scale_dim])
            response = _diff.abs().sort_values().index[0]

            self._rt = rt
            self._response = response

            marker_pos = np.empty(2)
            marker_pos[self._tick_dim] = (coords.
                                          loc[response, 'pos_tick_axis'])
            marker_pos[self._scale_dim] = (coords
                                           .loc[response, 'pos_scale_axis'])
            self._visual_elements[-1].pos = marker_pos

            if self.autoLog:
                msg = ('SimpleRatingScale %s: got response %.2f after '
                       '%.3f s.' % (self.name, self._response, self._rt))
                logging.exp(msg)

            if finish_on_response:
                self.status = FINISHED
                if self.autoLog:
                    logging.exp('SimpleRatingScale %s: finished.' % self.name)

    def _check_if_finished(self, finish_on_response=None):
        if finish_on_response is None:
            finish_on_response = self.finishOnResponse

        if self._timer.getTime() < 0:
            self.status = FINISHED
            if self.autoLog:
                msg = ('SimpleRatingScale %s: maxTime exceeded, '
                       'finishing.' % self.name)
                logging.exp(msg)
        elif self.response is None:
            self._check_for_response(finish_on_response=finish_on_response)
        elif not finish_on_response:
            msg = ('SimpleRatingScale %s: waiting for maxTime to expire.'
                   % self.name)
            logging.exp(msg)
        else:
            msg = ('You have encountered a bug. Please contact the '
                   'developers.')
            raise RuntimeError(msg)

    def _set_mouse_pos(self, pos):
        self.win.units = self.units
        self._mouse.setPos(pos)
        self.win.units = self._orig_units

    def draw(self):
        """
        Draw the visual elements to the back buffer and check for responses.

        """
        if self.autoLog:
            logging.exp('SimpleRatingScale %s: draw().' % self.name)

        # This line is left here for debugging reasons.
        # self._bounding_box.draw()
        if self.response is None:
            [element.draw() for element in self._visual_elements[:-1]]
        else:
            [element.draw() for element in self._visual_elements]

        if self._first_flip:
            if self.resetOnFirstFlip:
                # We set self._first_flip to False immediately after calling
                # self.reset(), otherwise we would end up in an infinite loop:
                # self.reset() itself sets self._first_flip to True!
                self.win.callOnFlip(self.reset)
                self.win.callOnFlip(setattr, self, '_first_flip', False)

            if self.mousePos is not None:
                self.win.callOnFlip(self._set_mouse_pos, self.mousePos)

            self.status = STARTED
        elif self.status != FINISHED:
            self._check_if_finished()
        else:
            pass  # We're finished.

    def waitForResponse(self):
        """
        Wait until a response is collected or `maxTime` is exceeded.

        Notes
        -----
        Will ignore the `finishOnResponse` attribute and always finish once a
        response is collected.

        """
        while self.status != FINISHED:
            self._check_if_finished(finish_on_response=True)

    def reset(self):
        """
        Remove any previously recorded response and reset the response timer.

        """
        if self.autoLog:
            logging.exp('SimpleRatingScale %s: reset().' % self.name)

        if self.iohub:
            self._io_mouse.clearEvents()

        self._mouse.clickReset()

        self._rt = None
        self._response = None
        self.status = NOT_STARTED
        self._first_flip = True
        self._time_start = core.getTime()
        self._timer.reset(t=self.maxTime)
