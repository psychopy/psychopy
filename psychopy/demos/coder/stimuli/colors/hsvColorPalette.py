"""
This demo creates a HSV color picker which shows how HSV colors work.

The contents of this file are in the public domain.
"""

from psychopy import locale_setup, visual, core, event, colors
import numpy as np
from psychopy import misc

# how big do we want the palette to be (in pixels)?
size = 400

# setup the window
win = visual.Window(
    size=[1920, 1080], 
    fullscr=False, 
    units='height'
)

# generate a 2d palette showing hue and saturation
hs = np.ones(
    [size, size, 3], dtype=float
)
hs[:, :, 0] = np.linspace(
    0, 360, size, endpoint=False
)
for i in range(size):
    hs[:, i, 1] = np.linspace(
        0, 1, size, endpoint=False
    )
# convert to rgb (0-1)
hs = (misc.hsv2rgb(hs) + 1) / 2
# create an image to show this palette
colorPalette = visual.ImageStim(
    win,
    name="colorPalette",
    image=hs, 
    units="pix",
    mask=None,
    texRes=64,
    # should be a square the size of the palette
    size=size,
)
# create a 1d palette showing value
v = np.zeros(
    [30, size, 3], dtype=float
)
v[:,:,2] = np.linspace(
    0, 1, size, endpoint=False
)
# convert to rgb (0-1)
v = (misc.hsv2rgb(v) + 1)
# create an image to show this palette
valuePalette = visual.ImageStim(
    win,
    name="valuePalette",
    image=v,
    units="pix",
    # should be below the 2d palette, and the same width
    size=[size, 30],
    pos=[0, -size / 2 - 50],
)

# create sliders to control h, s and v
hueSlider = visual.Slider(
    win, 
    name='hueSlider',
    style="slider",
    size=(size, 20), 
    pos=[0, size / 2 + 20],
    units="pix",
    ticks=[0, 360]
)
satSlider = visual.Slider(
    win, 
    name='satSlider',
    style="slider",
    size=(20, size), 
    pos=[size / 2 + 20, 0],
    units="pix",
    ticks=[0, 1]
)
valSlider = visual.Slider(
    win, 
    name='valSlider',
    style="slider",
    size=(size, 20), 
    pos=[0, -size / 2 - 80],
    units="pix",
    ticks=[0, 1]
)
# create a rect to show current color
preview = visual.Rect(
    win,
    name="preview",
    colorSpace="hsv",
    size=(100, 100),
    pos=(-20, size / 2 + 60),
    anchor="bottom right",
    units="pix"
)
previewText = visual.TextBox2(
    win,
    text="",
    name="previewText",
    size=(400, 100),
    pos=(20, size / 2 + 60),
    anchor="bottom left",
    units="pix"
)

# add some instructions
instText = visual.TextBox2(
    win=win, 
    name='instText',
    text=(
        "Use the sliders to change:\n"
        "Hue (top)\n"
        "Saturation (right)\n"
        "Value (bottom)\n"
        "\n"
        "Press ESCAPE to quit."
    ),
    anchor="center left",
    alignment="center left",
    pos=(-0.75, 0),
    size=(1, 1),
    padding=0.05,
    units="norm"
)

# start frame loop until Escape is pressed
while not event.getKeys(keyList=['escape']):
    # work out current color from sliders
    hue = hueSlider.markerPos or 0
    sat = satSlider.markerPos or 0
    val = valSlider.markerPos or 0.5
    # set preview
    preview.fillColor = [hue, sat, val]
    previewText.text = f"Hue: {hue:.0f}\nSat: {sat:.2f}\nVal: {val:.2f}"
    # draw everything
    colorPalette.draw()
    valuePalette.draw()
    hueSlider.draw()
    satSlider.draw()
    valSlider.draw()
    preview.draw()
    previewText.draw()
    instText.draw()
    # flip the window
    win.flip()
