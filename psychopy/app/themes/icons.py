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


class IconCache(dict):
    def __getitem__(self, item):
        if item in self:
            return dict.__getitem__(self, item)
        elif isinstance(item, (BaseComponent, BaseStandaloneRoutine)):
            self[item] = self._getComponentIcon(item)
        else:
            self[item] = self._getResourcesIcon(item)

    def _getResourcesIcon(self, stem, size=None):
        def _validateMatch(match):
            # Start off assuming valid and unsized
            valid = True
            sz = None
            # If file is not in the root folder or correct theme folder, don't use it
            if file.parent.stem not in [theme, resources.stem]:
                valid = False
            # Anything appended to stem must be numeric
            appendage = match.stem.replace(stem, "").replace(retStr, "")
            if appendage.isnumeric():
                # If has a numeric appendage, store it as size
                sz = int(appendage)
            elif not appendage:
                valid = False

            return match, valid, sz

        # If cached, return the cached object
        if stem in self:
            return dict.__getitem__(self, stem)

        # Start blank list for possible matches
        matches = {}
        # Look for all retina-specific matches in Resources folder
        for file in resources.glob(f"{stem}*{retStr}.png"):
            # Check this file
            file, valid, sz = _validateMatch(file)
            # If valid, append along with size details (if any)
            if valid:
                matches[sz] = file
        # Accept retina non-specific if no matches
        if not matches:
            for file in resources.glob(f"{stem}*.png"):
                # Check this file
                file, valid, sz = _validateMatch(file)
                # If valid, append along with size details (if any)
                if valid:
                    matches[sz] = file
        # Try theme folder if not in root
        themeFolder = resources / theme
        if not matches:
            for file in themeFolder.glob(f"{stem}*{retStr}.png"):
                # Check this file
                file, valid, sz = _validateMatch(file)
                # If valid, append along with size details (if any)
                if valid:
                    matches[sz] = file
        # Accept retina non-specific if no matches in theme folder
        if not matches:
            for file in themeFolder.glob(f"{stem}*.png"):
                # Check this file
                file, valid, sz = _validateMatch(file)
                # If valid, append along with size details (if any)
                if valid:
                    matches[sz] = file
        # Prioritise unsized images, but accept closest sized image otherwise
        if None in matches:
            img = wx.Image(
                str(matches[None])
            )
        elif matches:
            deltas = [(abs(size[0] - sz), sz) for sz in matches.keys()]
            sz = min(deltas)[1]
            img = wx.Image(
                str(matches[sz])
            )
        else:
            raise FileNotFoundError(
                f"Found no matches for stem {stem} in {resources}"
            )
        # Resize if needed
        self._resizeImage(img, size)
        # Convert to bitmap
        bmp = wx.Bitmap(img)
        # Cache bitmap handle
        self[stem] = bmp
        # Return bitmap
        return bmp

    def _getComponentIcon(self, cls, size=None, beta=False):
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


def appendBeta(bmp):
    """
    Append beta sticker to a component icon
    """
    # Get appropriately sized beta sticker
    betaImg = components._getResourcesIcon("beta", size=list(bmp.Size)).ConvertToImage()
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