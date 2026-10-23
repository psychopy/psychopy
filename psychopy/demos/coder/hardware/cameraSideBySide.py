"""Show live feeds from two cameras side-by-side in one window.

Each camera stream is drawn by its own ImageStim, scaled to fit half of the
window while keeping the camera's aspect ratio. Press escape to exit.

This file is public domain.

"""
from psychopy import visual, core, event
from psychopy.hardware.camera import Camera

# Cameras to show, left then right. Change `device` to pick different cameras.
# `frameSize` and `frameRate` can be left as `None` to use each camera's
# default. If the second camera fails to open with "No space left on device",
# both cameras share a USB controller that can't carry both streams at those
# settings, so ask one or both of them for a smaller `frameSize`.
cameraSettings = [
    {'device': 0, 'frameSize': None, 'frameRate': None},  # left
    {'device': 1, 'frameSize': None, 'frameRate': None},  # right
]

# open a window wide enough to hold two views
winSize = (1280, 600)
win = visual.Window(size=winSize, units='pix', color='black',
                    fullscr=False, allowGUI=True, title='Two camera feeds')

# open both cameras, use 'cv' mode since we're not recording to disk
cams = []
for settings in cameraSettings:
    cam = Camera(device=settings['device'],
                 frameSize=settings['frameSize'],
                 frameRate=settings['frameRate'],
                 win=win,
                 cameraLib=None,  # use the recommended library
                 usageMode='cv')
    cam.open()
    print("camera %s open: %s @ %s fps" % (
        settings['device'], cam.frameSize, cam.frameRate))
    cams.append(cam)

# each view gets half the window, less a margin around it
margin = 20
cellW = winSize[0] / 2 - margin * 2
cellH = winSize[1] - margin * 4  # leave room for the text below


def fitToCell(frameSize):
    """Scale a frame size to fit the cell without changing its shape."""
    w, h = frameSize
    scale = min(cellW / w, cellH / h)
    return w * scale, h * scale


# create an ImageStim for each camera, left one centred in the left half and
# the right one in the right half
camViews = []
labels = []
for cam, x in zip(cams, (-winSize[0] / 4, winSize[0] / 4)):
    camViews.append(
        visual.ImageStim(win, image=cam, size=fitToCell(cam.frameSize),
                         pos=(x, margin), units='pix'))
    labels.append(
        visual.TextStim(win, text="%s x %s @ %s fps" % (
                            cam.frameSize[0], cam.frameSize[1], cam.frameRate),
                        pos=(x, -winSize[1] / 2 + margin * 2.5),
                        height=18, color='white'))

# instruction text
instr = visual.TextStim(win, text="Press escape to exit.",
                        pos=(0, -winSize[1] / 2 + margin), height=16,
                        color='grey')

# main loop, drawing a view pulls the latest frame from its camera
while event.getKeys(keyList=['escape']) == []:
    for camView, label in zip(camViews, labels):
        camView.draw()
        label.draw()
    instr.draw()
    win.flip()

# clean up and close the cameras and window
for cam in cams:
    cam.close()
win.close()
core.quit()
