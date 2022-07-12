import numpy as np
from PIL import Image as pil
from PIL import GifImagePlugin as gif
from pathlib import Path
from time import time

from .image import ImageStim
from ..tools.attributetools import attributeSetter
from ..localization import _translate


class FrameAnimation(ImageStim):
    """
    A frame-by-frame animation from a list of images.

    win : psychopy.Window
        Window to draw images to
    images : list, tuple, numpy.ndarray
        List of images, in order, to be the frames of this animation. Images can be any format accepted by ImageStim.
    frameRate : int
        Number of frames to display per second
    frameStart : int
        Index of frame to start animation at - defaults to 0
    loop : bool
        Should the animation loop once each frame has been shown?

    Other params are all the same as used in ImageStim
    """
    def __init__(self, win,
                 images=None,
                 frameRate=30,
                 frameStart=0,
                 loop=True,
                 # from here on is all the same as ImageStim
                 mask=None,
                 units="",
                 pos=(0.0, 0.0),
                 size=None,
                 anchor="center",
                 ori=0.0,
                 color=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 contrast=1.0,
                 opacity=None,
                 depth=0,
                 interpolate=False,
                 flipHoriz=False,
                 flipVert=False,
                 texRes=128,
                 name=None,
                 autoLog=None,
                 maskParams=None):
        # Initialise base class
        ImageStim.__init__(self,
                           win,
                           image=None,
                           mask=mask,
                           units=units,
                           pos=pos,
                           size=size,
                           anchor=anchor,
                           ori=ori,
                           color=color,
                           colorSpace=colorSpace,
                           contrast=contrast,
                           opacity=opacity,
                           depth=depth,
                           interpolate=interpolate,
                           flipHoriz=flipHoriz,
                           flipVert=flipVert,
                           texRes=texRes,
                           name=name,
                           autoLog=autoLog,
                           maskParams=maskParams)

        # Store params
        self.images = images
        self.frameRate = frameRate
        self.loop = loop
        self.frameIndex = frameStart

        # Create timer
        self._lastFrameTime = time()

    @attributeSetter
    def images(self, value, log=True):
        """
        List of images for each frame of this animation. Can be any format accepted by `ImageStim.image`
        """
        # Make sure input is iterable
        if not isinstance(value, (list, tuple, np.ndarray)):
            value = [value]
        # Store original value
        self._requestedImages = value
        # Load/store requested images
        self._images = []
        for req in self._requestedImages:
            if isinstance(req, (str, Path)) and Path(req).suffix == ".gif":
                # If given a gif, load now and append each frame
                for img in _imageListFromGif(req):
                    self._images.append(img)
            elif isinstance(req, (str, Path)) and req != "defualt.png":
                # If given a file path, load now and append
                img = pil.open(req)
                self._images.append(img)
            else:
                # Otherwise, store image itself
                self._images.append(req)
        # Store
        self.__dict__['images'] = self._images

    @attributeSetter
    def frameIndex(self, i, log=False):
        """
        Index of current frame in animation
        """
        assert isinstance(i, int), _translate(
            "Frame index for FrameAnimation must be an integer."
        )
        # If index exceeds number of images...
        if i >= self.nFrames:
            if self.loop:
                # If we're looping, get looped index
                i = i % self.nFrames
            else:
                # Otherwise, get last frame
                i = self.nFrames - 1
        # Store index
        self.__dict__['frameIndex'] = i
        # Get corresponding image
        self.setImage(self._images[i], log=log)

    @property
    def nFrames(self):
        """
        Number of frames in this animation
        """
        return len(self._images)

    def draw(self, win=None):
        """
        Draw this frame and, if sufficient time has passed, move on to next frame
        """
        # Check if we're due a frame iteration
        if time() - self._lastFrameTime >= 1 / self.frameRate:
            # Move on to next frame
            self.frameIndex = self.frameIndex + 1
            # Store frame time
            self._lastFrameTime = time()
        # Do usual image draw
        ImageStim.draw(self, win=win)


def _imageListFromGif(value):
    """
    Convert a single animated .gif image to a list of static images
    """
    # Load gif
    gifImg = gif.GifImageFile(value)
    # Iterate through frames
    frames = []
    for i in range(gifImg.n_frames):
        # Seek to this frame
        gifImg.seek(i)
        # Create new image from this frame
        frame = gifImg.copy()
        # Append
        frames.append(frame)

    return frames
