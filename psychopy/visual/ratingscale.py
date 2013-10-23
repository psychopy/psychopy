#!/usr/bin/env python

'''A class for getting numeric or categorical ratings, e.g., a 1-to-7 scale.'''

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys

import psychopy  # so we can get the __path__
from psychopy import core, logging, event

from psychopy.colors import isValidColor
from psychopy.visual.circle import Circle
from psychopy.visual.patch import PatchStim
from psychopy.visual.shape import ShapeStim
from psychopy.visual.text import TextStim
from psychopy.visual.helpers import pointInPolygon, groupFlipVert

import numpy
from numpy import cos

from psychopy.constants import FINISHED, STARTED, NOT_STARTED


class RatingScale:
    """A class for getting numeric or categorical ratings, e.g., a 1-to-7 scale.

    Returns a re-usable rating-scale object having a .draw() method, with
    customizable visual appearance and full data options, including RT and history.

    The .draw() method displays the rating scale, handles the subject's responses,
    and updates the display. When the subject makes a final response, .noResponse
    goes False (i.e., there is a response). You can then call .getRating() to
    obtain the final rating, .getRT() to get the decision time, or .getHistory()
    to obtain all intermediate values (rating, RT), up to an including the final
    one. This feature can be used to obtain continuous ratings using a single
    RatingScale object.

    The experimenter has to draw the item to be rated, i.e., draw() it in the same
    window each frame. A RatingScale instance has no idea what else is on the screen.

    The subject can
    use the arrow keys (left, right) to move the marker in small increments (e.g.,
    1/100th of a tick-mark if precision = 100).

    Auto-rescaling happens if the low-anchor is 0 and the high-anchor is a multiple
    of 10, just to reduce visual clutter.

    **Example 1**:

        The default 7-point scale::

            myItem = <create your text, image, movie, ...>
            myRatingScale = visual.RatingScale(myWin)
            while myRatingScale.noResponse:
                myItem.draw()
                myRatingScale.draw()
                myWin.flip()
            rating = myRatingScale.getRating()
            decisionTime = myRatingScale.getRT()
            choiceHistory = myRatingScale.getHistory()

    **Example 2**:

        Key-board only. Considerable customization is possible. For fMRI, if your
        response box sends keys 1-4, you could specify left, right, and accept
        keys, and no mouse::

            myRatingScale = visual.RatingScale(myWin, markerStart=4,
                leftKeys='1', rightKeys = '2', acceptKeys='4')

    **Example 3**:

        Non-numeric choices (categorical, unordered)::

            myRatingScale = visual.RatingScale(myWin, choices=['agree', 'disagree'])

        A text version of the item will be displayed, but the value returned by
        getResponse() will be of type you gave it::

            var = 3.14
            myRatingScale = visual.RatingScale(myWin,
                                choices=['cherry', 'apple', True, var, 'pie'])

        So if the subject chooses True,
        getResponse() will return True (bool) and not u'True' (unicode).

    See Coder Demos -> stimuli -> ratingScale.py for examples. As another example,
    fMRI_launchScan.py uses a rating scale for the experimenter to choose between
    two modes (and not for subjects giving ratings).

    The Builder RatingScale component gives a restricted set of options, but also
    allows full control over a RatingScale (via 'customizeEverything').

    :Authors:
        2010 Jeremy Gray, with on-going updates
        2012 Henrik Singmann: tickMarks, labels, ticksAboveLine
    """
    def __init__(self,
                win,
                scale='<default>',
                choices=None,
                low=1,
                high=7,
                lowAnchorText=None,
                highAnchorText=None,
                tickMarks=None,
                labels=None,
                precision=1,
                textSizeFactor=1.0,
                textColor='LightGray',
                textFont='Helvetica Bold',
                showValue=True,
                showScale=True,
                showAnchors=True,
                showAccept=True,
                acceptKeys='return',
                acceptPreText='key, click',
                acceptText='accept?',
                acceptSize=1.0,
                leftKeys='left',
                rightKeys='right',
                respKeys=(),
                lineColor='White',
                ticksAboveLine=True,
                markerStyle='triangle',
                markerColor=None,
                markerStart=False,
                markerExpansion=1,
                customMarker=None,
                escapeKeys=None,
                allowSkip=True,
                skipKeys='tab',
                mouseOnly=False,
                singleClick=False,
                displaySizeFactor=1.0,
                stretchHoriz=1.0,
                pos=None,
                minTime=1.0,
                maxTime=0.0,
                disappear=False,
                flipVert=False,
                name='',
                autoLog=True):
        """
    :Parameters:

        win :
            A :class:`~psychopy.visual.Window` object (required)
        scale :
            explanation of the numbers to display to the subject, shown above the line;
            string, default = '<low>=not at all, <high>=extremely'.
            To suppress all text above the line, set `showScale=False`.
            If `labels` is not `False` and `choices` or `tickMarks` exists,
            `scale` defaults to `False`.
        choices :
            a list of items which the subject can choose among;
            takes precedence over `low`, `high`, `lowAnchorText`, `highAnchorText`,
            `showScale`, `tickMarks`, `precision`.
        low :
            lowest numeric rating / low anchor (integer, default = 1)
        high :
            highest numeric rating / high anchor (integer, default = 7; at least `low + 1`)
        lowAnchorText :
            text to dsiplay for the low end of the scale (default = numeric low value)
        highAnchorText :
            text to display for the high end of the scale (default = numeric high value)
        tickMarks :
            list of positions at which tick marks should be placed
            (low and high need to be included if tick marks should be at the edges of the scale).
            If `None` (the default), tick marks are automatically equally spaced,
            one per integer value; auto-rescaling (by a factor of 10) can happen to reduce visual clutter.
        labels :
            text to be placed at each tick mark as placed by tickMarks and controls where labels
            of choices are displayed. Default is `None`.
            If `None` and `choices`:  choices will be plotted at ticks and
            `showAnchors=False`, but `scale` can be used for plotting above the line.
            If `None` and  `tickMarks`: `tickMarks` will be used and `showAnchors=False`.
            If `False`, no labels are plotted at tick marks.
        precision :
            portions of a tick to accept as input [1, 10, 100], default = 1 tick (no fractional parts)

            .. note:: pressing a key in `leftKeys` or `rightKeys` will move the marker by one portion of a tick.

            .. note:: precision is incompatible with `choices`.

        textSizeFactor :
            the size of text elements of the scale.
            For larger than default text (expand) set > 1; for smaller, set < 1.
        textColor :
            color to use for anchor and scale text (assumed to be RGB), default = 'LightGray'
        textFont :
            name of the font to use, default = 'Helvetica Bold'
        showValue :
            show the subject their currently selected number, default = `True`
        showScale :
            show the `scale` text (the text above the line), default = `True`.
            If `False`, will not show any text above the line.
        showAnchors :
            show the two end points of the scale (`low`, `high`), default = `True`
        showAccept :
            show the button to click to accept the current value by using the mouse, default = `True`

            .. note::
                If showAccept is False and acceptKeys is empty, `acceptKeys` is reset to `['return']`
                to give the subject a way to respond.

        acceptKeys :
            a key or list of keys that are used to mean "accept the current response", default = `['return']`
        acceptPreText :
            text to display before any value has been selected
        acceptText :
            text to display in the 'accept' button after a value has been selected
        acceptSize :
            width of the accept box relative to the default (e.g., 2 is twice as wide)
        leftKeys :
            a key or list of keys that mean "move leftwards", default = `['left']`
        rightKeys :
            a key or list of keys that mean "move rightwards", default = `['right']`
        respKeys :
            a list of key characters to use for responding, in the desired order.
            The first item will be the left-most choice, the second item will be the
            next choice, and so on. If there are
            fewer respKeys than choices, the right-most choices will not be selectable
            using respKeys, but rightKeys can be used to navigate there.
        lineColor :
            color to use for the scale line, default = 'White'
        ticksAboveLine :
            should the tick marks be displayed above the line (the default) or below
        markerStyle :
            'triangle' (DarkBlue), 'circle' (DarkRed), 'glow' (White, expanding),
            or 'slider' (translucent Black, looks best with `precision=100`)
        markerColor :
            `None` = use defaults; or any legal RGB colorname, e.g., '#123456', 'DarkRed'
        markerStart :
            `False`, or the value in [`low`..`high`] to be pre-selected upon initial display
        markerExpansion :
            how much the glow marker expands when moving to the right; 0=none, negative shrinks; try 10 or -10
        customMarker :
            allows for a user-defined marker; must have a `.draw()` method, such as a
            :class:`~psychopy.visual.TextStim()` or :class:`~psychopy.visual.GratingStim()`
        escapeKeys :
            keys that will quit the experiment if pressed by the subject (by calling
            `core.quit()`). default = `[ ]` (no escape keys).

            .. note:: in the Builder, the default is `['escape']` (to be consistent
            with other Builder conventions)

        allowSkip :
            if True, the subject can skip an item by pressing a key in `skipKeys`, default = `True`
        skipKeys :
            list of keys the subject can use to skip a response, default = `['tab']`

            .. note::
                to require a response to every item, use `allowSkip=False`

        mouseOnly :
            require the subject use the mouse only (no keyboard), default = `False`.
            can be used to avoid competing with other objects for keyboard input.

            .. note::
                `mouseOnly=True` and `showAccept=False` is a bad combination,
                so `showAccept` wins (`mouseOnly` is reset to `False`);
                similarly, `mouseOnly` and `allowSkip` can conflict, because
                skipping an item is done via key press (`mouseOnly` wins)
                `mouseOnly=True` is helpful if there will be something else
                on the screen expecting keyboard input
        singleClick :
            enable a mouse click to both indicate and accept the rating, default = `False`.
            Note that the 'accept' box is visible, but clicking it has no effect,
            its just to display the value. A legal key press will also count as a singleClick.
        pos : tuple (x, y)
            where to position the rating scale (x, y) in terms of the window's units (pix, norm);
            default `(0.0, -0.4)` in norm units
        displaySizeFactor :
            how much to expand or contract the overall rating scale display
            (not just the line length)
        stretchHoriz:
            how much to stretch (or compress) the scale
            horizontally (3 -> use the whole window);
            acts like `displaySizeFactor`, but only in the horizontal direction
        minTime :
            number of seconds that must elapse before a reponse can be accepted,
            default = `1.0`.
        maxTime :
            number of seconds after which a reponse cannot be made accepted.
            if `maxTime` <= `minTime`, there's unlimited time.
            default = `0.0` (wait forever).
        disappear :
            if `True`, the rating scale will be hidden after a value is accepted;
            useful when showing multiple scales. The default is to remain on-screen.
        flipVert :
            if ``True``, flip the rating scale display in the vertical direction
        name : string
            The name of the object to be using during logged messages about
            this stim
        autolog :
            whether logging should be done automatically
    """

        logging.exp('RatingScale %s: init()' % name)
        self.win = win
        self.name = name
        self.autoLog = autoLog
        self.disappear = disappear

        # internally work in norm units, restore to orig units at the end of __init__:
        self.savedWinUnits = self.win.units
        self.win.units = 'norm'

        # make things well-behaved if the requested value(s) would be trouble:
        self._initFirst(showAccept, mouseOnly, singleClick, acceptKeys,
                        markerStart, low, high, precision, choices, lowAnchorText,
                        highAnchorText, scale, showScale, showAnchors,
                        tickMarks, labels, ticksAboveLine)
        self._initMisc(minTime, maxTime)

        # Set scale & position, key-bindings:
        self._initPosScale(pos, displaySizeFactor, stretchHoriz)
        self._initKeys(self.acceptKeys, skipKeys, escapeKeys, leftKeys, rightKeys, respKeys, allowSkip)

        # Construct the visual elements:
        self._initLine(tickMarkValues=tickMarks, lineColor=lineColor)
        self._initMarker(customMarker, markerExpansion, markerColor, markerStyle)
        try:
            float(textSizeFactor)
        except:
            textSizeFactor = 1.0
        self._initTextElements(win, self.lowAnchorText, self.highAnchorText,
            self.scale, textColor, textFont, textSizeFactor, showValue, tickMarks)
        self._initAcceptBox(self.showAccept, acceptPreText, acceptText, acceptSize,
            self.markerColor, self.textSizeSmall, textSizeFactor, self.textFont)

        # List-ify the visual elements; self.marker is handled separately
        self.visualDisplayElements = []
        if self.showScale:   self.visualDisplayElements += [self.scaleDescription]
        if self.showAnchors: self.visualDisplayElements += [self.lowAnchor, self.highAnchor]
        if self.showAccept:  self.visualDisplayElements += [self.acceptBox, self.accept]
        if self.labelTexts:
            for text in self.labels:
                self.visualDisplayElements.append(text)
        self.visualDisplayElements += [self.line]  # last b/c win xp had display issues

        # Mirror (flip) vertically if requested
        self.flipVert = False
        self.setFlipVert(flipVert)

        # Final touches:
        self.origScaleDescription = self.scaleDescription.text
        self.reset()  # sets .status, among other things
        self.win.units = self.savedWinUnits

    def _initFirst(self, showAccept, mouseOnly, singleClick, acceptKeys,
                   markerStart, low, high, precision, choices,
                   lowAnchorText, highAnchorText, scale, showScale, showAnchors,
                   tickMarks, labels, ticksAboveLine):
        """some sanity checking; various things are set, especially those that are
        used later; choices, anchors, markerStart settings are handled here
        """
        self.showAccept = bool(showAccept)
        self.mouseOnly = bool(mouseOnly)
        self.singleClick = bool(singleClick)
        self.acceptKeys = acceptKeys
        if choices and precision != 1:
            precision = 1  # a fractional choice is undefined
            logging.exp('RatingScale: precision is incompatible with choices')
        self.precision = precision
        self.showAnchors = bool(showAnchors)
        self.labelTexts = None
        self.ticksAboveLine = ticksAboveLine

        if not self.showAccept:
            # the accept button is the mouse-based way to accept the current response
            if len(list(self.acceptKeys)) == 0:
                # make sure there is in fact a way to respond using a key-press:
                self.acceptKeys = ['return']
            if self.mouseOnly and not self.singleClick:
                # then there's no way to respond, so deny mouseOnly / enable using keys:
                self.mouseOnly = False
                logging.warning("RatingScale %s: ignoring mouseOnly (because showAccept and singleClick are False)" % self.name)

        # 'choices' is a list of non-numeric (unordered) alternatives:
        self.scale = scale
        self.showScale = showScale
        self.lowAnchorText = lowAnchorText
        self.highAnchorText = highAnchorText
        if choices and len(list(choices)) < 2:
            logging.warning("RatingScale %s: ignoring choices=[ ]; it requires 2 or more list elements" % self.name)
        if choices and len(list(choices)) >= 2:
            low = 0
            high = len(list(choices)) - 1
            if labels is False:
                # anchor text defaults to blank, unless low or highAnchorText is requested explicitly:
                if lowAnchorText is None and highAnchorText is None:
                    self.showAnchors = False
                else:
                    self.lowAnchorText = unicode(lowAnchorText)
                    self.highAnchorText = unicode(highAnchorText)
                self.scale = '  '.join(map(unicode, choices)) # unicode for display
                self.choices = choices
            else:
                # anchor text is ignored when choices are present (HS, 16/11/2012)
                self.showAnchors = False
                self.labelTexts = choices
                self.choices = choices
                if self.scale == "<default>":
                    self.scale = False
        else:
            self.choices = False

        # Anchors need to be well-behaved [do after choices]:
        try:
            self.low = int(low) # low anchor
        except:
            self.low = 1
        try:
            self.high = int(high) # high anchor
        except:
            self.high = self.low + 1
        if self.high <= self.low:
            self.high = self.low + 1
            self.precision = 100

        if tickMarks:
            if not(labels is False):
                self.showAnchors = False # To avoid overplotting.
                if labels is None:
                    self.labelTexts = tickMarks
                else:
                    self.labelTexts = labels
                if len(self.labelTexts) != len(tickMarks):
                    logging.warning("RatingScale %s: len(labels) not equal to len(tickMarks), using tickMarcks as labels" % self.name)
                    self.labelTexts = tickMarks
                if self.scale == "<default>":
                    self.scale = False

        # Marker preselected and valid? [do after anchors]
        if ( (type(markerStart) == float and self.precision > 1 or
                type(markerStart) == int) and
                markerStart >= self.low and markerStart <= self.high):
            self.markerStart = markerStart
            self.markerPlacedAt = markerStart
            self.markerPlaced = True
        elif isinstance(markerStart, basestring) and type(self.choices) == list and markerStart in self.choices:
            self.markerStart = self.choices.index(markerStart)
            self.markerPlacedAt = markerStart
            self.markerPlaced = True
        else:
            self.markerStart = None
            self.markerPlaced = False

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
        self.pulseColor = [0.6 + 0.22 * float(cos(i/15.65)) for i in range(frames_per_cycle)]

    def _initPosScale(self, pos, displaySizeFactor, stretchHoriz):
        """position (x,y) and magnitification (size) of the rating scale
        """
        # Screen position (translation) of the rating scale as a whole:
        if pos:
            if len(list(pos)) == 2:
                offsetHoriz, offsetVert = pos
            else:
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
            self.stretchHoriz = float(stretchHoriz)
        except:
            self.stretchHoriz = 1.
        try:
            self.displaySizeFactor = float(displaySizeFactor) * 0.6
        except:
            self.displaySizeFactor = 0.6
        if not 0.06 < self.displaySizeFactor < 3:
            logging.warning("RatingScale %s: unusual displaySizeFactor" % self.name)
        self.displaySizeFactor = min(5, self.displaySizeFactor)

    def _initKeys(self, acceptKeys, skipKeys, escapeKeys, leftKeys, rightKeys, respKeys, allowSkip):
        # keys for accepting the currently selected response:
        if self.mouseOnly:
            self.acceptKeys = [ ] # no valid keys, so must use mouse
        else:
            if type(acceptKeys) not in [list, tuple]:
                acceptKeys = [acceptKeys]
            self.acceptKeys = acceptKeys
        self.skipKeys = [ ]
        if allowSkip and not self.mouseOnly:
            if skipKeys is None:
                skipKeys = [ ]
            elif type(skipKeys) not in [list, tuple]:
                skipKeys = [skipKeys]
            self.skipKeys = list(skipKeys)
        if type(escapeKeys) not in [list, tuple]:
            if escapeKeys is None:
                escapeKeys = [ ]
            else:
                escapeKeys = [escapeKeys]
        self.escapeKeys = escapeKeys
        if type(leftKeys) not in [list, tuple]:
            leftKeys = [leftKeys]
        self.leftKeys = leftKeys
        if type(rightKeys) not in [list, tuple]:
            rightKeys = [rightKeys]
        self.rightKeys = rightKeys

        # allow responding via aribtrary keys if given as a param:
        if respKeys and hasattr(respKeys, '__iter__'):
            self.respKeys = respKeys
            self.enableRespKeys = True
            if (set(self.respKeys).intersection(self.leftKeys + self.rightKeys +
                        self.acceptKeys + self.skipKeys + self.escapeKeys)):
                logging.warning('RatingScale %s: respKeys may conflict with other keys' % self.name)
        else:
            # allow resp via numeric keys if the response range is in 0-9
            self.respKeys = [ ]
            if (not self.mouseOnly and self.low > -1 and self.high < 10):
                self.respKeys = [str(i) for i in range(self.low, self.high + 1)]
            # but if any digit is used as an action key, that should take precedence
            # so disable using numeric keys:
            if (set(self.respKeys).intersection(self.leftKeys + self.rightKeys +
                                    self.acceptKeys + self.skipKeys + self.escapeKeys) == set([]) ):
                self.enableRespKeys = True
            else:
                self.enableRespKeys = False
        if self.enableRespKeys:
            self.tickFromKeyPress = {}
            for i, key in enumerate(self.respKeys):
                self.tickFromKeyPress[key] = i + self.low

        self.allKeys = (self.rightKeys + self.leftKeys + self.acceptKeys +
                        self.escapeKeys + self.skipKeys + self.respKeys)

    def _initLine(self, tickMarkValues=None, lineColor='White'):
        """define a ShapeStim to be a graphical line, with tick marks.

        ### Notes (JRG Aug 2010)
        Conceptually, the response line is always -0.5 to +0.5 ("internal" units). This line, of unit length,
        is scaled and translated for display. The line is effectively "center justified", expanding both left
        and right with scaling, with pos[] specifiying the screen coordinate (in window units, norm or pix)
        of the mid-point of the response line. Tick marks are in integer units, internally 0 to (high-low),
        with 0 being the left end and (high-low) being the right end. (Subjects see low to high on the screen.)
        Non-numeric (categorical) choices are selected using tick-marks interpreted as an index, choice[tick].
        Tick units get mapped to "internal" units based on their proportion of the total ticks (--> 0. to 1.).
        The unit-length internal line is expanded / contracted by stretchHoriz and displaySizeFactor, and then
        is translated to position pos (offsetHoriz=pos[0], offsetVert=pos[1]). pos is the name of the arg, and
        its values appear in the code as offsetHoriz and offsetVert only for historical reasons (should be
        refactored for clarity).

        Auto-rescaling reduces the number of tick marks shown on the
        screen by a factor of 10, just for nicer appearance, without affecting the internal representation.

        Thus, the horizontal screen position of the i-th tick mark, where i in [0,n], for n total ticks (n = high-low),
        in screen units ('norm') will be:
          tick-i             == offsetHoriz + (-0.5 + i/n ) * stretchHoriz * displaySizeFactor
        So two special cases are:
          tick-0 (left end)  == offsetHoriz - 0.5 * stretchHoriz * displaySizeFactor
          tick-n (right end) == offsetHoriz + 0.5 * stretchHoriz * displaySizeFactor
        The vertical screen position is just offsetVert (in screen norm units).
        To elaborate: tick-0 is the left-most tick, or "low anchor"; here 0 is internal, the subject sees <low>.
        tick-n is the right-most tick, or "high anchor", or internal-tick-(high-low), and the subject sees <high>.
        Intermediate ticks, i, are located proportionally between -0.5 to + 0.5, based on their proportion
        of the total number of ticks, float(i)/n. The "proportion of total" is used because its a line of unit length,
        i.e., the same length as used to internally represent the scale (-0.5 to +0.5).
        If precision > 1, the user / experimenter is asking for fractional ticks. These map correctly
        onto [0, 1] as well without requiring special handling (just do ensure float() ).

        Another note: -0.5 to +0.5 looked too big to be the default size of the rating line in screen norm units,
        so I set the internal displaySizeFactor = 0.6 to compensate (i.e., making everything smaller). The user can
        adjust the scaling around the default by setting displaySizeFactor, stretchHoriz, or both.
        This means that the user / experimenter can just think of > 1 being expansion (and < 1 == contraction)
        relative to the default (internal) scaling, and not worry about the internal scaling.

        ### Notes (HS November 2012)
        To allow for labels at the ticks, the positions of the tick marks are saved in self.tickPositions.
        If tickMarks, those positions are used instead of the automatic positions.
        """

        self.lineColor = lineColor
        self.tickSize = 0.04 # vertical height of each tick, norm units
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
        self.hStretchTotal = self.stretchHoriz * self.displaySizeFactor

        # ends of the rating line, in norm units:
        self.lineLeftEnd  = self.offsetHoriz - 0.5 * self.hStretchTotal
        self.lineRightEnd = self.offsetHoriz + 0.5 * self.hStretchTotal

        # space around the line within which to accept mouse input:
        pad = 0.06 * self.displaySizeFactor
        self.nearLine = [
            [self.lineLeftEnd - pad, -2 * pad + self.offsetVert],
            [self.lineLeftEnd - pad, 2 * pad + self.offsetVert],
            [self.lineRightEnd + pad, 2 * pad + self.offsetVert],
            [self.lineRightEnd + pad, -2 * pad + self.offsetVert] ]

        # vertices for ShapeStim:
        self.tickPositions = []  # list to hold horizontal positions
        vertices = [[self.lineLeftEnd, self.offsetVert]]  # first vertex
        vertExcursion = self.tickSize * self.displaySizeFactor
        if not self.ticksAboveLine:
            vertExcursion *= -1  # flip ticks to display below the line
        lineLength = self.lineRightEnd - self.lineLeftEnd
        for count, tick in enumerate(tickMarkPositions):
            horizTmp = self.lineLeftEnd + lineLength * tick
            vertices += [[horizTmp, self.offsetVert + vertExcursion],
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
            lineWidth=4, lineColor=self.lineColor, name=self.name+'.line')

    def _initMarker(self, customMarker, expansion, markerColor, style):
        """define a GratingStim or ShapeStim to be used as the indicator
        """
        # preparatory stuff:
        self.markerStyle = style
        if customMarker and not 'draw' in dir(customMarker):
            logging.warning("RatingScale: the requested customMarker has no draw method; reverting to default")
            self.markerStyle = 'triangle'
            customMarker = None
        self.markerSize = 8. * self.displaySizeFactor
        self.markerOffsetVert = 0.
        if isinstance(markerColor, basestring):
            markerColor = markerColor.replace(' ', '')

        # define self.marker:
        if customMarker:
            self.marker = customMarker
            if markerColor == None:
                if hasattr(customMarker, 'color'):
                    if not customMarker.color: # 0 causes other problems, so ignore it here
                        customMarker.color = 'DarkBlue'
                elif hasattr(customMarker, 'fillColor'):
                    customMarker.color = customMarker.fillColor
                else:
                    customMarker.color = 'DarkBlue'
                markerColor = customMarker.color
                if not hasattr(self.marker, 'name'):
                    self.marker.name = 'customMarker'
        elif self.markerStyle == 'triangle':
            scaledTickSize = self.tickSize * self.displaySizeFactor
            vert = [[-1 * scaledTickSize * 1.8, scaledTickSize * 3],
                    [ scaledTickSize * 1.8, scaledTickSize * 3], [0, -0.005]]
            if markerColor == None or not isValidColor(markerColor):
                markerColor = 'DarkBlue'
            self.marker = ShapeStim(win=self.win, units='norm', vertices=vert,
                lineWidth=0.1, lineColor=markerColor, fillColor=markerColor,
                name=self.name+'.markerTri', autoLog=False)
        elif self.markerStyle == 'slider':
            scaledTickSize = self.tickSize * self.displaySizeFactor
            vert = [[-1 * scaledTickSize * 1.8, scaledTickSize],
                    [ scaledTickSize * 1.8, scaledTickSize],
                    [ scaledTickSize * 1.8, -1 * scaledTickSize],
                    [-1 * scaledTickSize * 1.8, -1 * scaledTickSize]]
            if markerColor == None or not isValidColor(markerColor):
                markerColor = 'black'
            self.marker = ShapeStim(win=self.win, units='norm', vertices=vert,
                lineWidth=0.1, lineColor=markerColor, fillColor=markerColor,
                name=self.name+'.markerSlider', opacity=0.8, autoLog=False)
        elif self.markerStyle == 'glow':
            if markerColor == None or not isValidColor(markerColor):
                markerColor = 'White'
            self.marker = PatchStim(win=self.win, tex='sin', mask='gauss',
                color=markerColor, opacity = 0.85, autoLog=False,
                name=self.name+'.markerGlow')
            self.markerBaseSize = self.tickSize * self.markerSize
            self.markerOffsetVert = .02
            self.markerExpansion = float(expansion) * 0.6
            if self.markerExpansion == 0:
                self.markerBaseSize *= self.markerSize * 0.7
                if self.markerSize > 1.2:
                    self.markerBaseSize *= .7
                self.marker.setSize(self.markerBaseSize/2.)
        else: # self.markerStyle == 'circle':
            if markerColor == None or not isValidColor(markerColor):
                markerColor = 'DarkRed'
            x,y = self.win.size
            windowRatio = float(y)/x
            self.markerSizeVert = 3.2 * self.tickSize * self.displaySizeFactor
            size = [self.markerSizeVert * windowRatio, self.markerSizeVert]
            self.markerOffsetVert = self.markerSizeVert / 2.
            self.marker = Circle(self.win, size=size, units='norm',
                lineColor=markerColor, fillColor=markerColor,
                name=self.name+'.markerCir', autoLog=False)
            self.markerBaseSize = self.tickSize
        self.markerColor = markerColor
        self.markerYpos = self.offsetVert + self.markerOffsetVert

    def _initTextElements(self, win, lowAnchorText, highAnchorText, scale, textColor,
                          textFont, textSizeFactor, showValue, tickMarks):
        """creates TextStim for self.scaleDescription, self.lowAnchor, self.highAnchor
        """
        # text appearance (size, color, font, visibility):
        self.showValue = bool(showValue) # hide if False
        self.textColor = textColor  # rgb
        self.textFont = textFont
        self.textSize = 0.2 * textSizeFactor * self.displaySizeFactor
        self.textSizeSmall = self.textSize * 0.6
        self.showValue = bool(showValue)

        if lowAnchorText:
            lowText = unicode(lowAnchorText)
        else:
            lowText = unicode(self.low)
        if highAnchorText:
            highText = unicode(highAnchorText)
        else:
            highText = unicode(self.high)
        self.lowAnchorText = lowText
        self.highAnchorText = highText
        if not scale:
            scale = ' '
        elif scale == '<default>': # set the default
            scale = lowText + u' = not at all . . . extremely = ' + highText

        # create the TextStim:
        vertPosTmp = -2 * self.textSizeSmall * self.displaySizeFactor + self.offsetVert
        self.scaleDescription = TextStim(win=self.win, height=self.textSizeSmall,
            pos=[self.offsetHoriz, 0.22 * self.displaySizeFactor + self.offsetVert],
            color=self.textColor, wrapWidth=2 * self.hStretchTotal, name=self.name+'.scale')
        self.scaleDescription.setFont(textFont)
        self.lowAnchor = TextStim(win=self.win, height=self.textSizeSmall,
            pos=[self.offsetHoriz - 0.5 * self.hStretchTotal, vertPosTmp],
            color=self.textColor, name=self.name+'.lowAnchor')
        self.lowAnchor.setFont(textFont)
        self.lowAnchor.setText(lowText)
        self.highAnchor = TextStim(win=self.win, height=self.textSizeSmall,
            pos=[self.offsetHoriz + 0.5 * self.hStretchTotal, vertPosTmp],
            color=self.textColor, name=self.name+'.highAnchor')
        self.highAnchor.setFont(textFont)
        self.highAnchor.setText(highText)
        self.labels = []
        if self.labelTexts:
            for c, lab in enumerate(self.labelTexts):
                self.labels.append(TextStim(win=self.win, text=unicode(lab), font=textFont,
                    pos=[self.tickPositions[c], vertPosTmp], height=self.textSizeSmall,
                    color=self.textColor, name=self.name+'.tickLabel.'+unicode(lab)))
        self.setDescription(scale) # do after having set the relevant things

    def setDescription(self, scale=None):
        """Method to set the text description that appears above the rating line.

        Useful when using the same RatingScale object to rate several dimensions.
        `setDescription(None)` will reset the description to its initial state.
        Set to a space character (' ') to make the description invisible.
        The description will not be visible if `showScale` is False.
        """
        if scale is None:
            scale = self.origScaleDescription
        self.scaleDescription.setText(scale)
        logging.exp('RatingScale %s: setDescription="%s"' % (self.name, self.scaleDescription.text))
        if not self.showScale:
            logging.exp('RatingScale %s: description set but showScale is False' % self.name)

    def _initAcceptBox(self, showAccept, acceptPreText, acceptText, acceptSize,
                       markerColor, textSizeSmall, textSizeFactor, textFont):
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
        sizeFactor = self.displaySizeFactor * textSizeFactor
        leftRightAdjust = 0.2 * max(0.1, acceptSize) * sizeFactor
        self.acceptBoxtop = acceptBoxtop = self.offsetVert - boxVert[0] * sizeFactor
        self.acceptBoxbot = acceptBoxbot = self.offsetVert - boxVert[1] * sizeFactor
        self.acceptBoxleft = acceptBoxleft = self.offsetHoriz - leftRightAdjust
        self.acceptBoxright = acceptBoxright = self.offsetHoriz + leftRightAdjust

        # define a rectangle with rounded corners; for square corners, set delta2 to 0
        delta = 0.025 * self.displaySizeFactor
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
            interpolate=interpolate, name=self.name+'.accept', autoLog=False)

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
        if log and self.autoLog:
            self.win.logOnFlip("Set %s flipVert=%s" % (self.name, self.flipVert),
                level=logging.EXP, obj=self)

    def draw(self):
        """Update the visual display, check for response (key, mouse, skip).

        sets response flags as appropriate (`self.noResponse`, `self.timedOut`).
        `draw()` only draws the rating scale, not the item to be rated
        """
        self.win.units = 'norm'  # original units do get restored
        if self.firstDraw:
            self.firstDraw = False
            self.clock.reset()
            self.status = STARTED
            self.history = [(self.markerStart, 0.0)]  # this will grow
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
                self.marker.setPos((0, -.012), ('+', '-')[self.flipVert])  # drop it onto the line
                self.markerPosFixed = True  # flag to park it there
            self.marker.draw()
            if self.showAccept:
                self.acceptBox.draw()  # hides the text
            self.win.units = self.savedWinUnits
            return  # makes the marker unresponsive

        mouseX, mouseY = self.myMouse.getPos() # norm units

        # draw a dynamic marker:
        if self.markerPlaced or self.singleClick:
            # expansion for 'glow', based on proportion of total line
            proportion = self.markerPlacedAt / self.tickMarks
            if self.markerStyle == 'glow' and self.markerExpansion:
                if self.markerExpansion > 0:
                    newSize = 0.1 * self.markerExpansion * proportion
                    newOpacity = 0.2 + proportion
                else:  # self.markerExpansion < 0:
                    newSize = - 0.1 * self.markerExpansion * (1 - proportion)
                    newOpacity = 1.2 - proportion
                self.marker.setSize(self.markerBaseSize + newSize)
                self.marker.setOpacity(min(1, max(0, newOpacity)))
            # update position:
            if self.singleClick and pointInPolygon(mouseX, mouseY, self.nearLine):
                self.setMarkerPos(self._getMarkerFromPos(mouseX))
            elif not hasattr(self, 'markerPlacedAt'):
                self.markerPlacedAt = False
            # set the marker's screen position based on tick (== markerPlacedAt)
            if self.markerPlacedAt is not False:
                x = self.offsetHoriz + self.hStretchTotal * (-0.5 + proportion)
                self.marker.setPos((x, self.markerYpos))
                self.marker.draw()
            if self.showAccept:
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
                if key in self.escapeKeys:
                    core.quit()
                if key in self.skipKeys:
                    self.markerPlacedAt = None
                    self.noResponse = False
                elif self.enableRespKeys and key in self.respKeys:
                    # place the marker at the corresponding tick (from key)
                    self.markerPlaced = True
                    resp = self.tickFromKeyPress[key]
                    self.markerPlacedAt = self._getMarkerFromTick(resp)
                    proportion = self.markerPlacedAt / self.tickMarks
                    self.marker.setPos([self.displaySizeFactor * (-0.5 + proportion), 0])
                    if self.singleClick and self.beyondMinTime:
                        self.noResponse = False
                        self.marker.setPos((0, self.offsetVert), '+')
                        logging.data('RatingScale %s: (key single-click) rating=%s' %
                                     (self.name, unicode(self.getRating())) )
                if not self.markerPlaced:
                    continue
                elif key in self.leftKeys:
                    leftwards = self.markerPlacedAt - self.keyIncrement
                    self.markerPlacedAt = max(0, leftwards)
                elif key in self.rightKeys:
                    rightwards = self.markerPlacedAt + self.keyIncrement
                    self.markerPlacedAt = min(self.tickMarks, rightwards)
                elif key in self.acceptKeys and self.beyondMinTime:
                    self.noResponse = False
                    self.history.append((self.getRating(), self.getRT()))  # RT when accept pressed
                    logging.data('RatingScale %s: (key response) rating=%s' %
                                     (self.name, unicode(self.getRating())) )

        # handle mouse left-click:
        if self.myMouse.getPressed()[0]:
            #mouseX, mouseY = self.myMouse.getPos() # done above
            # if click near the line, place the marker there:
            if pointInPolygon(mouseX, mouseY, self.nearLine):
                self.markerPlaced = True
                self.markerPlacedAt = self._getMarkerFromPos(mouseX)
                if self.singleClick and self.beyondMinTime:
                    self.noResponse = False
                    logging.data('RatingScale %s: (mouse single-click) rating=%s' %
                                 (self.name, unicode(self.getRating())) )
            # if click in accept box and conditions are met, accept the response:
            elif (self.showAccept and self.markerPlaced and self.beyondMinTime and
                    self.acceptBox.contains(mouseX, mouseY)):
                self.noResponse = False  # accept the currently marked value
                self.history.append((self.getRating(), self.getRT()))
                logging.data('RatingScale %s: (mouse response) rating=%s' %
                            (self.name, unicode(self.getRating())) )

        # decision time = secs from first .draw() to when first 'accept' value:
        if not self.noResponse and self.decisionTime == 0:
            self.decisionTime = self.clock.getTime()
            logging.data('RatingScale %s: rating RT=%.3f' % (self.name, self.decisionTime))
            # minimum time is enforced during key and mouse handling
            self.status = FINISHED
            if self.showAccept:
                self.acceptBox.setFillColor(self.acceptFillColor, log=False)
                self.acceptBox.setLineColor(self.acceptLineColor, log=False)

        # build up response history:
        tmpRating = self.getRating()
        if self.history[-1][0] != tmpRating:
            self.history.append((tmpRating, self.getRT()))  # tuple

        # restore user's units:
        self.win.units = self.savedWinUnits

    def reset(self):
        """Restores the rating-scale to its post-creation state.

        The history is cleared, and the status is set to NOT_STARTED. Does not
        restore the scale text description (such reset is needed between
        items when rating multiple items)
        """
        # only resets things that are likely to have changed when the ratingScale instance is used by a subject
        self.noResponse = True
        self.markerPlaced = False
        self.markerPlacedAt = False
        #NB markerStart could be 0; during __init__, its forced to be numeric and valid, or None (not boolean)
        if self.markerStart != None:
            self.markerPlaced = True
            self.markerPlacedAt = self.markerStart - self.low # __init__ assures this is valid
        self.firstDraw = True # triggers self.clock.reset() at start of draw()
        self.decisionTime = 0
        self.markerPosFixed = False
        self.frame = 0 # a counter used only to 'pulse' the 'accept' box
        if self.showAccept:
            self.acceptBox.setFillColor(self.acceptFillColor, 'rgb')
            self.acceptBox.setLineColor(self.acceptLineColor, 'rgb')
            self.accept.setColor('#444444','rgb') # greyed out
            self.accept.setText(self.keyClick)
        logging.exp('RatingScale %s: reset()' % self.name)
        self.status = NOT_STARTED
        self.history = None

    def getRating(self):
        """Returns the final, accepted rating, or the current (non-accepted) intermediate
        selection. The rating is None if the subject skipped this item, or False
        if not available. Returns the currently indicated rating even if it has
        not been accepted yet (and so might change until accept is pressed).
        """
        if self.noResponse and self.status == FINISHED:
            return False
        if not type(self.markerPlacedAt) in [float, int]:
            return None # eg, if skipped a response

        if self.precision == 1: # set type for the response, based on what was wanted
            response = int(self.markerPlacedAt * self.autoRescaleFactor) + self.low
        else:
            response = float(self.markerPlacedAt) * self.autoRescaleFactor + self.low
        if self.choices:
            response = self.choices[response]
            # retains type as given by experimenter, eg, str bool etc
            # boolean False will have an RT value, however
        return response

    def getRT(self):
        """Returns the seconds taken to make the rating (or to indicate skip).
        Returns None if no rating available, or maxTime if the response timed out.
        Returns the time elapsed so far if no rating has been accepted yet (e.g.,
        for continuous usage).
        """
        if self.status != FINISHED:
            return self.clock.getTime()
        if self.noResponse:
            if self.timedOut:
                return self.maxTime
            return None
        return self.decisionTime

    def getHistory(self):
        """Return the subject's intermediate selection history, up to and including
        the final accepted choice, as a list of (rating, time) tuples. The history
        can be retrieved at any time, allowing for continuous ratings to be
        obtained in real-time. Both numerical and categorical choices are stored
        automatically in the history.
        """
        return self.history
