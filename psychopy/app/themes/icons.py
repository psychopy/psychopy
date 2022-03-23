import re
from abc import ABC

import numpy
import wx
from pathlib import Path
from psychopy import prefs

theme = "light"
retStr = ""
resources = Path(prefs.paths['resources'])
iconCache = {}


class BaseIcon(wx.Icon):
    def __init__(self, stem, size=None):
        if stem in iconCache:
            # If already created, just copy instance
            wx.Icon.__init__(self, iconCache[stem])
            # Duplicate relevant attributes if relevant (depends on subclass)
            iconCache[stem]._copyTo(self)
        else:
            # Initialise base class
            wx.Icon.__init__(self)
            self.bitmap = None
            # Use subclass-specific populate call to create bitmaps
            self._populate(stem)
            # Set size
            self.size = size
            # Update from current bitmap
            if self.bitmap:
                self.CopyFromBitmap(self.bitmap)
            # Store ref to self in iconCache
            iconCache[stem] = self

    def _copyTo(self, other):
        raise NotImplementedError(
            "BaseIcon should not be instanced directly; it serves only as a base class for ButtonIcon and ComponentIcon"
        )

    def _populate(self, stem):
        raise NotImplementedError(
            "BaseIcon should not be instanced directly; it serves only as a base class for ButtonIcon and ComponentIcon"
        )

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        # Sanitize size value
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

        # Store value
        self._size = (width, height)
        # Do subclass-specific fitting method to adjust bitmap to desired size
        self._fitBitmap()

    def _fitBitmap(self):
        raise NotImplementedError(
            "BaseIcon should not be instanced directly; it serves only as a base class for ButtonIcon and ComponentIcon"
        )

    @staticmethod
    def resizeBitmap(bmp, size=None):
        assert isinstance(bmp, wx.Bitmap), (
            "Bitmap supplied to `resizeBitmap()` must be a `wx.Bitmap` object."
        )
        # If size is None, return bitmap as is
        if size is None:
            return bmp
        # Split up size value
        width, height = size
        # If size is unchanged, return bitmap as is
        if width == bmp.GetWidth() and height == bmp.GetHeight():
            return bmp
        # Convert to an image
        img = bmp.ConvertToImage()
        # Resize image
        img.Rescale(width, height, quality=wx.IMAGE_QUALITY_HIGH)
        # Return as bitmap
        return wx.Bitmap(img)


class ButtonIcon(BaseIcon):
    def _copyTo(self, other):
        other.bitmaps = self.bitmaps
        other.bitmap = self.bitmap

    def _populate(self, stem):
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
        self.bitmap = None

    def _fitBitmap(self):
        # If no stored bitmaps, do nothing (icon remains blank)
        if not self.bitmaps:
            return
        # Split up size value
        width, height = self.size
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
        self.bitmap = self.resizeBitmap(bmp, self.size)


class ComponentIcon(BaseIcon):
    def _copyTo(self, other):
        other.bitmap = self.bitmap
        if hasattr(self, "_beta"):
            other._beta = self._beta

    def _populate(self, cls):
        # Throw error if class doesn't have associated icon file
        if not hasattr(cls, "iconFile"):
            raise AttributeError(
                f"Could not retrieve icon for {cls} as the class does not have an `iconFile` attribute."
            )
        # Get file from class
        filePath = Path(cls.iconFile)
        # Get icon file stem and root folder from iconFile value
        stem = filePath.stem
        folder = filePath.parent
        # Look in appropriate theme folder for files
        matches = {}
        for match in (folder / theme).glob(f"{stem}*.png"):
            appendix = match.stem.replace(stem, "")
            matches[appendix] = match
        # Choose / resize file according to retina
        if retStr in matches:
            file = matches[retStr]
        else:
            file = list(matches.values())[0]
        img = wx.Image(str(file))
        # Use appropriate sized bitmap
        self.bitmap = wx.Bitmap(img)

    def _fitBitmap(self):
        self.bitmap = self.resizeBitmap(self.bitmap, self.size)

    @property
    def beta(self):
        if not hasattr(self, "_beta"):
            # Get appropriately sized beta sticker
            betaImg = ButtonIcon("beta", size=self.size).bitmap.ConvertToImage()
            # Get bitmap as image
            baseImg = self.bitmap.ConvertToImage()
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

            self._beta = wx.Bitmap(combined)

        return self._beta
