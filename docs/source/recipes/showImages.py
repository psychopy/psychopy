from pathlib import Path

import numpy as np
from PIL import Image
from psychopy import core, event, visual

# ---------------------
# Setup window
# ---------------------
win = visual.Window(
    (900, 900),
    screen=0,
    units="pix",
    allowGUI=True,
    fullscr=False,
)
# ---------------------
# Example 1: load a stimulus from disk
# ---------------------

# assume we're running from the root psychopy repo.
# you could replace with path to any image:
path_to_image_file = Path() / "PsychoPy2_screenshot.png"

# simply pass the image path to ImageStim to load and display:
image_stim = visual.ImageStim(win, image=path_to_image_file)
text_stim = visual.TextStim(
    win,
    text="Showing image from file",
    pos=(0.0, 0.8),
    units="norm",
    height=0.05,
    wrapWidth=0.8,
)

image_stim.draw()
text_stim.draw()
win.flip()
event.waitKeys()  # press space to continue

# ---------------------
# Example 2: convert image to numpy array
#
# Perhaps you want to convert an image to numpy, do some things to it,
# and then display. Here I use the Python Imaging Library for image loading,
# and a conversion function from skimage. PsychoPy has an internal
# "image2array" function but this only handles single-layer (i.e. intensity) images.
#
# ---------------------

pil_image = Image.open(path_to_image_file)
image_np = np.array(
    pil_image, order="C"
)  # convert to numpy array with shape width, height, channels
image_np = (
    image_np.astype(float) / 255.0
)  # convert to float in 0--1 range, assuming image is 8-bit uint.

# Note this float conversion is "quick and dirty" and will not
# fix potential out-of-range problems if you're going
# straight from a numpy array. See the img_as_float
# function of scikit image for a more careful conversion.

# flip image (row-axis upside down so we need to reverse it):
image_np = np.flip(image_np, axis=0)
image_stim = visual.ImageStim(
    win,
    image=image_np,
    units="pix",
    size=(
        image_np.shape[1],
        image_np.shape[0],
    ),  # here's a gotcha: need to pass the size (x, y) explicitly.
    colorSpace="rgb1",  # img_as_float converts to 0:1 range, whereas PsychoPy defaults to -1:1.
)
text_stim.text = "Showing image from numpy array"
image_stim.draw()
text_stim.draw()
win.flip()
event.waitKeys()  # press space to continue

win.close()
core.quit()
