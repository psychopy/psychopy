#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A live monitor for a joystick or gamepad.

Everything the device reports is drawn on screen, which is the quickest way to
work out which physical control maps onto which index on your own hardware:

* every button is a circle which lights up while that button is held down,
* every analogue axis has a read-only Slider showing its current position,
* the first two axes also drive a point around a quadrant display.

Inputs are labelled with their index and, where the device's input scheme names
them, with that name as well -- axis 0 is 'X', button 0 is 'A', and so on. See
`psychopy.hardware.joystick.mappings` for the schemes which ship with PsychoPy.

Presses and releases are printed to the console as they happen, taken from the
responses the device queues up for you.

The 'pyglet' backend used here needs a pyglet window which is being flipped in
order for the joystick state to update, which is why the window's winType is
matched to the joystick backend below. The 'glfw' backend needs no window and
works alongside a window created by any library.

If nothing is plugged in, PsychoPy falls back to an emulated joystick: the
mouse drives the X and Y axes, and holding 'ctrl' + 'alt' while pressing a
number key presses the button with that index.
"""

from math import ceil

from psychopy import visual, core, event
from psychopy.hardware import joystick

# ------------------------------------------------------------------------------
# Appearance
#

COL_BG = '#1b1c1e'       # window background
COL_PANEL = '#26282c'    # panel and button fills
COL_QUAD = '#212327'     # an empty quadrant
COL_QUAD_ON = '#2b4740'  # the quadrant the stick is currently in
COL_LINE = '#494d55'     # borders, ticks and guide lines
COL_TEXT = '#e7e9ec'     # headings and values
COL_DIM = '#868d97'      # secondary labels
COL_LIVE = '#3ecf8e'     # a button which is held down
COL_POINT = '#f2c14e'    # slider markers and the point in the quadrant display

HEAD_H = 0.030           # letter height for headings
TEXT_H = 0.022           # letter height for ordinary labels
SMALL_H = 0.019          # letter height for input names

# Panel bounds in height units. The window below is 800 x 600, so x runs from
# -0.667 to 0.667 and y from -0.5 to 0.5, which is what the widths here are
# budgeted against: the three panels across the middle and the gaps between
# them come to a little under the 1.33 available.
AXES_PANEL = {'left': -0.64, 'right': -0.115, 'top': 0.305, 'bottom': -0.055}
BTNS_PANEL = {'left': -0.64, 'right': 0.64, 'top': -0.145, 'bottom': -0.465}
HATS_PANEL = {'left': 0.34, 'right': 0.64, 'top': 0.305, 'bottom': -0.055}
QUAD_POS = (0.115, 0.125)  # centre of the quadrant display
QUAD_SIZE = 0.36           # its width and height

HEADING_Y = 0.365         # the row the panel headings sit on
STATUS_Y = -0.10          # the row of readouts under the panels

# A hat reports (x, y), each -1, 0 or +1, which is nine states: the eight
# compass directions and centred. Unlike a stick, +1 is up, so these signs map
# straight onto the screen with no flip.
HAT_NAMES = {
    (-1, 1): 'NW', (0, 1): 'N', (1, 1): 'NE',
    (-1, 0): 'W', (0, 0): '\u00b7', (1, 0): 'E',
    (-1, -1): 'SW', (0, -1): 'S', (1, -1): 'SE',
}

# ------------------------------------------------------------------------------
# Open a window and find a joystick
#

joystick.backend = 'pyglet'
# the pyglet backend reads the joystick through the window's event loop, so the
# winType and joystick.backend have to match
win = visual.Window(
    (800, 600), units='height', color=COL_BG, allowGUI=False,
    winType=joystick.backend)

if joystick.getNumJoysticks() == 0:
    print("You don't have a joystick connected, so this demo will run on an "
          "emulated one -- move the mouse for the X and Y axes, and hold "
          "'ctrl' + 'alt' while pressing a number key for a button.")

# NB: no window is passed here, so `getAllAxes()` reports the raw -1 to +1 range
# the device itself uses. Pass `win=win` if you would rather `getX()` and
# `getY()` came back already scaled to the window's units.
joy = joystick.Joystick(0)

nAxes = joy.getNumAxes()
nButtons = joy.getNumButtons()

# ------------------------------------------------------------------------------
# Labels
#

labels = []  # everything made by `addLabel`, drawn once per frame


def addLabel(text, pos, width, anchor='center', height=TEXT_H, color=COL_TEXT,
             bold=False):
    """Make a TextBox2 label with this demo's styling, and draw it each frame.

    The raw formatting syntax is used throughout so that device names
    containing markdown characters come out as they are written.
    """
    box = visual.TextBox2(
        win, text=text, pos=pos, size=(width, None), anchor=anchor,
        alignment=anchor, letterHeight=height, color=color, bold=bold,
        formattingSyntax='raw', padding=0, borderColor=None, fillColor=None,
        autoLog=False)
    labels.append(box)

    return box


def setText(box, text):
    """Push text into a TextBox2, but only when it has actually changed.

    Setting `.text` re-lays out the whole box, so skipping the unchanged ones
    keeps the frame rate up when there are this many of them on screen.
    """
    if box.text != text:
        box.text = text


def count(n, singular, plural):
    """Format a count with the noun that goes with it, e.g. '1 hat'."""
    return '{} {}'.format(n, singular if n == 1 else plural)


def describeInput(inputType, index):
    """Label an input by index, plus its name in the active input scheme."""
    name = joy.getInputName(inputType, index)

    return str(index) if name is None else '{}  {}'.format(index, name)


summary = '{}, {}, {}, via the {} backend'.format(
    count(nAxes, 'axis', 'axes'),
    count(nButtons, 'button', 'buttons'),
    count(joy.getNumHats(), 'hat', 'hats'), joy.inputLib)
print('found {}: {}'.format(joy.getName(), summary))

addLabel(joy.getName(), (0, 0.465), 1.3, height=HEAD_H, bold=True)
addLabel(summary, (-0.64, 0.425), 0.66, anchor='center-left', color=COL_DIM)
addLabel("press 'q' or 'escape' to quit", (0.64, 0.425), 0.45,
         anchor='center-right', color=COL_DIM)
addLabel('Axes', (AXES_PANEL['left'], HEADING_Y), 0.3, anchor='center-left',
         height=HEAD_H)
addLabel('Stick position', (QUAD_POS[0] - QUAD_SIZE / 2, HEADING_Y), 0.36,
         anchor='center-left', height=HEAD_H)
addLabel('Hat' if joy.getNumHats() == 1 else 'Hats',
         (HATS_PANEL['left'], HEADING_Y), 0.28, anchor='center-left',
         height=HEAD_H)
addLabel('Buttons', (BTNS_PANEL['left'], STATUS_Y), 0.3, anchor='center-left',
         height=HEAD_H)

# ------------------------------------------------------------------------------
# One row per axis: a name, a read-only Slider and a numeric readout
#

NAME_W = 0.13   # width of the axis name column
VALUE_W = 0.10  # width of the numeric readout column
COL_GAP = 0.03  # gap between those columns and the slider

sliderLeft = AXES_PANEL['left'] + NAME_W + COL_GAP
sliderRight = AXES_PANEL['right'] - VALUE_W - COL_GAP

# spread the rows down the panel, capping the spacing so a device with only a
# couple of axes doesn't leave them stranded far apart. They start at the top of
# the panel, so they line up with the displays beside them.
axisStep = min(0.07, (AXES_PANEL['top'] - AXES_PANEL['bottom']) / max(nAxes, 1))
axisTop = AXES_PANEL['top']

axisSliders = []
axisReadouts = []
for i in range(nAxes):
    y = axisTop - axisStep * (i + 0.5)
    addLabel(describeInput('axes', i), (AXES_PANEL['left'], y), NAME_W,
             anchor='center-left', color=COL_DIM)
    # a Slider makes a good readout as well as a control: it is read-only here,
    # and its marker is moved by setting `markerPos` rather than by the mouse
    axisSliders.append(visual.Slider(
        win, ticks=(-1, 0, 1), startValue=0, readOnly=True, granularity=0,
        pos=((sliderLeft + sliderRight) / 2, y),
        size=(sliderRight - sliderLeft, 0.028),
        style='rating', markerColor=COL_POINT, lineColor=COL_LINE,
        autoLog=False))
    axisReadouts.append(addLabel(
        '+0.00', (AXES_PANEL['right'] - VALUE_W, y), VALUE_W,
        anchor='center-left'))

# ------------------------------------------------------------------------------
# A quadrant display driven by the first two axes
#

quadX, quadY = QUAD_POS
quadHalf = QUAD_SIZE / 2

quadBox = visual.Rect(
    win, width=QUAD_SIZE, height=QUAD_SIZE, pos=QUAD_POS, fillColor=COL_PANEL,
    lineColor=COL_DIM, lineWidth=2, autoLog=False)

# One Rect per quadrant, so that the one the stick is in can be highlighted.
# These are keyed by the sign of each axis *on screen*: the Y axis is flipped
# when drawing, because pushing a stick forwards usually gives a negative value.
quadrants = {}
for signX in (-1, 1):
    for signY in (-1, 1):
        quadrants[(signX, signY)] = visual.Rect(
            win, width=quadHalf, height=quadHalf,
            pos=(quadX + signX * quadHalf / 2, quadY + signY * quadHalf / 2),
            fillColor=COL_QUAD, lineColor=None, autoLog=False)
        # label each quadrant with the signs of the raw axis values it covers
        addLabel(
            '{}X {}Y'.format('+' if signX > 0 else '-',
                             '-' if signY > 0 else '+'),
            (quadX + signX * (quadHalf - 0.014),
             quadY + signY * (quadHalf - 0.010)), 0.16,
            anchor='{}-{}'.format('top' if signY > 0 else 'bottom',
                                  'right' if signX > 0 else 'left'),
            height=SMALL_H, color=COL_DIM)

# thin rectangles rather than lines, as line widths above a pixel aren't
# supported by every driver
crosshair = [
    visual.Rect(win, width=QUAD_SIZE, height=0.003, pos=QUAD_POS,
                fillColor=COL_DIM, lineColor=None, autoLog=False),
    visual.Rect(win, width=0.003, height=QUAD_SIZE, pos=QUAD_POS,
                fillColor=COL_DIM, lineColor=None, autoLog=False)]

# guides which follow the point, making its position easier to read off
guideH, guideV = (
    visual.Rect(win, width=QUAD_SIZE, height=0.002, pos=QUAD_POS,
                fillColor=COL_POINT, lineColor=None, opacity=0.4,
                autoLog=False),
    visual.Rect(win, width=0.002, height=QUAD_SIZE, pos=QUAD_POS,
                fillColor=COL_POINT, lineColor=None, opacity=0.4,
                autoLog=False))

point = visual.Circle(
    win, size=(0.030, 0.030), pos=QUAD_POS, fillColor=COL_POINT,
    lineColor=None, autoLog=False)

quadStatus = addLabel('axes 0 and 1: centred', (quadX, STATUS_Y), 0.36,
                      color=COL_DIM)

# ------------------------------------------------------------------------------
# A 3 x 3 grid per hat, showing which of its nine states it is in
#

nHats = joy.getNumHats()

hatCells = []     # one {(x, y): Rect} per hat
hatStatus = []    # one readout per hat

if nHats:
    # stack the hats down the panel, so a device with several still fits
    slot = (HATS_PANEL['top'] - HATS_PANEL['bottom']) / nHats
    # each grid sits at the top of its slot, so the first one lines up with
    # the top of the quadrant display, and the rest of the slot leaves room
    # for that hat's readout
    # the 0.075 is the readout's own line plus a margin, so that a stacked
    # hat's readout stays clear of the grid below it
    gridSize = max(0.06, min(HATS_PANEL['right'] - HATS_PANEL['left'],
                             slot - 0.075))
    step = gridSize / 3
    hatX = (HATS_PANEL['left'] + HATS_PANEL['right']) / 2

    for h in range(nHats):
        hatY = HATS_PANEL['top'] - slot * h - gridSize / 2
        cells = {}
        for signX in (-1, 0, 1):
            for signY in (-1, 0, 1):
                pos = (hatX + signX * step, hatY + signY * step)
                cells[(signX, signY)] = visual.Rect(
                    win, width=step * 0.88, height=step * 0.88, pos=pos,
                    fillColor=COL_QUAD, lineColor=COL_LINE, lineWidth=2,
                    autoLog=False)
                addLabel(HAT_NAMES[(signX, signY)], pos, step,
                         height=SMALL_H, color=COL_DIM)
        hatCells.append(cells)
        hatStatus.append(addLabel(
            '{}: centred'.format(describeInput('hats', h)),
            (hatX, hatY - gridSize / 2 - 0.045), gridSize + 0.08,
            color=COL_DIM))
else:
    addLabel('this device has no hat',
             ((HATS_PANEL['left'] + HATS_PANEL['right']) / 2,
              (HATS_PANEL['top'] + HATS_PANEL['bottom']) / 2), 0.28,
             color=COL_DIM)

# ------------------------------------------------------------------------------
# One circle per button, lit up while that button is held
#

# share the buttons out evenly rather than filling one row and leaving a
# stub in the next, then keep the columns as tight as the rows and centre the
# grid, so a device with only a few buttons doesn't spread them across the
# whole window
nRows = ceil(nButtons / 12) or 1
nCols = ceil(nButtons / nRows) or 1
# size a button from whichever direction is the tighter, then cap it, so that
# a device with only a handful doesn't end up with enormous circles
btnSize = min(0.10,
              min((BTNS_PANEL['right'] - BTNS_PANEL['left']) / nCols,
                  (BTNS_PANEL['top'] - BTNS_PANEL['bottom']) / nRows) * 0.6)
# pack the grid around that size rather than spreading it out to fill the
# panel, and centre what's left over
colStep = btnSize * 1.6
rowStep = min(btnSize + 0.05,
              (BTNS_PANEL['top'] - BTNS_PANEL['bottom']) / nRows)
gridLeft = (BTNS_PANEL['left'] + BTNS_PANEL['right'] - colStep * nCols) / 2

buttonCircles = []
for i in range(nButtons):
    cx = gridLeft + colStep * (i % nCols + 0.5)
    cy = BTNS_PANEL['top'] - rowStep * (i // nCols + 0.5)
    buttonCircles.append(visual.Circle(
        win, size=(btnSize, btnSize), pos=(cx, cy), fillColor=COL_PANEL,
        lineColor=COL_LINE, lineWidth=2, autoLog=False))
    addLabel(str(i), (cx, cy), btnSize, height=SMALL_H)
    name = joy.getInputName('buttons', i)
    if name is not None:
        addLabel(name, (cx, cy - btnSize / 2 - 0.014), colStep * 0.95,
                 height=SMALL_H, color=COL_DIM)

# ------------------------------------------------------------------------------
# Run
#

# previous state, so that colours are only set when something has changed.
# `quadrantWas` starts off as False rather than None, since None is itself a
# perfectly good quadrant state -- the stick sitting on an axis.
buttonWas = [None] * nButtons
quadrantWas = False
hatWas = [None] * nHats

while not event.getKeys(keyList=['q', 'escape']):
    axisVals = joy.getAllAxes()
    buttonVals = joy.getAllButtons()
    hatVals = joy.getAllHats()

    # ... the quadrant display, from the first two axes
    x = axisVals[0] if nAxes > 0 else 0.0
    y = axisVals[1] if nAxes > 1 else 0.0
    # clamp, as a device which needs calibrating can report beyond +/-1
    x = max(-1.0, min(1.0, x))
    y = max(-1.0, min(1.0, y))

    point.pos = (quadX + x * quadHalf, quadY - y * quadHalf)
    guideH.pos = (quadX, quadY - y * quadHalf)
    guideV.pos = (quadX + x * quadHalf, quadY)

    # whichever quadrant the point is in, or None while it sits on an axis
    quadrant = None
    if x != 0 and y != 0:
        quadrant = (1 if x > 0 else -1, -1 if y > 0 else 1)
    if quadrant != quadrantWas:
        for key, rect in quadrants.items():
            rect.fillColor = COL_QUAD_ON if key == quadrant else COL_QUAD
        quadrantWas = quadrant
    setText(quadStatus, 'axes 0 and 1: {}'.format(
        'centred' if quadrant is None else '{}X {}Y'.format(
            '+' if x > 0 else '-', '+' if y > 0 else '-')))

    # ... the sliders and their readouts, one per axis
    for i, slider in enumerate(axisSliders):
        slider.markerPos = axisVals[i]
        setText(axisReadouts[i], '{:+.2f}'.format(axisVals[i]))

    # ... the hat grids, lighting the cell the hat is currently in
    for h, cells in enumerate(hatCells):
        # a hat only ever reports -1, 0 or +1, but round and clamp anyway so a
        # backend which scales its hats can't index a cell which isn't there
        pos = tuple(max(-1, min(1, int(round(v)))) for v in hatVals[h])
        if pos != hatWas[h]:
            for key, cell in cells.items():
                cell.fillColor = COL_LIVE if key == pos else COL_QUAD
            setText(hatStatus[h], '{}: {}'.format(
                describeInput('hats', h),
                'centred' if pos == (0, 0) else '{} {}'.format(
                    HAT_NAMES[pos], pos)))
            hatWas[h] = pos

    # ... and the button circles
    for i, circle in enumerate(buttonCircles):
        if buttonVals[i] != buttonWas[i]:
            circle.fillColor = COL_LIVE if buttonVals[i] else COL_PANEL
            buttonWas[i] = buttonVals[i]

    # draw back to front
    quadBox.draw()
    for rect in quadrants.values():
        rect.draw()
    for rect in crosshair:
        rect.draw()
    guideH.draw()
    guideV.draw()
    point.draw()
    for slider in axisSliders:
        slider.draw()
    for cells in hatCells:
        for cell in cells.values():
            cell.draw()
    for circle in buttonCircles:
        circle.draw()
    for label in labels:
        label.draw()

    # presses and releases are timestamped for you and queued as responses,
    # which `win.flip()` below fills in as it dispatches the device
    for response in joy.getResponses():
        print(response)

    win.flip()  # redraw the buffer, and update the joystick with it

joy.close()
win.close()
core.quit()

# The contents of this file are in the public domain.
