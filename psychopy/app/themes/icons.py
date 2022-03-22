import re

import numpy
import wx
from pathlib import Path
from psychopy import prefs
from psychopy.experiment.components import BaseComponent
from psychopy.experiment.routines import BaseStandaloneRoutine

theme = "light"
retStr = ""
resources = Path(prefs.paths['resources'])


class Icon(wx.Icon):
    def __init__(self, stem, size=None):
        # Initialise self
        wx.Icon.__init__(self)

        # Get all files in the resource folder containing the given stem
        matches = [f for f in resources.glob(f"**/{stem}*.png")]
        # Create blank arrays to store retina and non-retina files
        ret = {}
        nret = {}
        # Validate matches
        for match in matches:
            # Reject match if in unused theme folder
            if match.parent.stem not in (theme, "Resources"):
                continue
            # Get appendix (any chars in file stem besides requested stem and retina string)
            appendix = match.stem.replace(stem, "").replace(retStr, "") or None
            # Reject non-numeric appendices (may be a longer word, e.g. requested "folder", got "folder-open")
            if appendix is not None and not appendix.isnumeric():
                continue
            elif appendix is not None:
                appendix = int(appendix)
            # If valid, append to array according to retina
            if "@2x" in match.stem:
                if appendix in ret and match.parent.stem != theme:
                    # Prioritise theme-specific if match is already present
                    continue
                ret[appendix] = match
            else:
                if appendix in nret and match.parent.stem != theme:
                    # Prioritise theme-specific if match is already present
                    continue
                nret[appendix] = match
        # Compare keys in retina and non-retina matches
        retOnly = set(ret) - set(nret)
        nretOnly = set(nret) - set(ret)
        both = set(ret) & set(nret)
        # Compare keys from both match dicts
        retKeys = list(retOnly)
        nretKeys = list(nretOnly)
        if retStr:
            # If using retina, prioritise retina matches
            retKeys += list(both)
        else:
            # Otherwise, prioritise non-retina matches
            nretKeys += list(both)
        # Merge match dicts
        files = {}
        for key in retKeys:
            files[key] = ret[key]
        for key in nretKeys:
            files[key] = nret[key]

        # Create bitmap array for files
        self.bitmaps = {}
        for key, file in files.items():
            self.bitmaps[key] = wx.Bitmap(str(file))
        self._bitmap = None

        # Set size (will pick appropriate bitmap)
        self.size = size

    @property
    def size(self):
        return self.GetWidth(), self.GetHeight()

    @size.setter
    def size(self, value):
        if isinstance(value, (tuple, list)):
            # If given an iterable, use first value as width
            width = value[0]
            height = value[1]
        else:
            # Otherwise, assume square
            width = value
            height = value
        if width is not None and not isinstance(width, int):
            # If width is not an integer, try to make it one
            width = int(width)
        if height is not None and not isinstance(height, int):
            # If height is not an integer, try to make it one
            height = int(height)

        # If no stored bitmaps, do nothing (icon remains blank)
        if not self.bitmaps:
            return

        # Find appropriate bitmap from list of bitmaps
        if width in self.bitmaps:
            # If value matches dict exactly, use match
            bmp = self.bitmaps[width]
        elif width is None:
            # If given no size, use the largest image
            i = max(self.bitmaps.keys())
            bmp = self.bitmaps[i]
        else:
            # If any other size, use closest match
            deltas = [(abs(width - sz), sz) for sz in self.bitmaps.keys() if sz is not None]
            if deltas:
                i = min(deltas)[1]
            else:
                i = None
            bmp = self.bitmaps[i]

        # Use appropriate sized bitmap
        self.CopyFromBitmap(bmp)
        self._bitmap = bmp
        # Set own size
        self.SetWidth(width)
        self.SetHeight(height)


class IconCache(dict):
    def getBitmap(self, stem, size=None):
        # If stem is a string, get from Resources folder
        if isinstance(stem, str):
            # If not cached, cache item
            if stem not in self:
                self[stem] = Icon(stem, size)
            return self[stem]._bitmap
        # If stem is a component/standalone routine, get from class def folder
        if isinstance(stem, (BaseComponent, BaseStandaloneRoutine)):
            self._getComponentIcon(stem, size)

    def _getComponentIcon(self, cls, size=None):
        """
        Get the icon for a component or standalone routine from its class.
        """
        # If cached, return the cached object
        if cls in self:
            return dict.__getitem__(self, cls)

        # Throw error if class doesn't have associated icon file
        if not hasattr(cls, "iconFile"):
            raise AttributeError(
                f"Could not retrieve icon for {cls} as the class does not have an `iconFile` attribute."
            )
        # Get icon file from class
        iconFile = Path(cls.iconFile)
        # Get icon file stem and root folder from iconFile value
        iconStem = iconFile.stem
        iconFolder = iconFile.parent
        # Create an image from icon file
        img = wx.Image(str(
                iconFolder / theme / (iconStem + retStr + ".png")
        ))
        # Resize if needed
        self._resizeImage(img, size)
        # Convert to bitmap
        bmp = wx.Bitmap(img)
        # Cache bitmap handle
        self[cls] = bmp
        # Return bitmap
        return bmp

    @staticmethod
    def _resizeImage(img, size):
        # Make sure size is a 1x2 iterable
        if isinstance(size, (int, float)):
            size = (size, size)
        # If width is given and is not the same as the image size, resize it
        if size is not None and any(size[i] != img.GetSize()[i] for i in (0, 1)):
            img.Rescale(*size, quality=wx.IMAGE_QUALITY_HIGH)


components = IconCache()
buttons = IconCache()


def appendBeta(bmp):
    """
    Append beta sticker to a component icon
    """
    # Get appropriately sized beta sticker
    betaImg = Icon("beta", size=list(bmp.Size))._bitmap.ConvertToImage()
    # Get bitmap as image
    baseImg = bmp.ConvertToImage()
    # Get color data and alphas
    betaData = numpy.array(betaImg.GetData())
    betaAlpha = numpy.array(betaImg.GetAlpha(), dtype=int)
    baseData = numpy.array(baseImg.GetData())
    baseAlpha = numpy.array(baseImg.GetAlpha(), dtype=int)
    # Overlay colors
    combinedData = baseData
    r = numpy.where(betaAlpha > 0)[0] * 3
    g = numpy.where(betaAlpha > 0)[0] * 3 + 1
    b = numpy.where(betaAlpha > 0)[0] * 3 + 2
    combinedData[r] = betaData[r]
    combinedData[g] = betaData[g]
    combinedData[b] = betaData[b]
    # Combine alphas
    combinedAlpha = numpy.add(baseAlpha, betaAlpha)
    combinedAlpha[combinedAlpha > 255] = 255
    combinedAlpha = numpy.uint8(combinedAlpha)
    # Set these back to the base image
    combined = betaImg
    combined.SetData(combinedData)
    combined.SetAlpha(combinedAlpha)

    return wx.Bitmap(combined)