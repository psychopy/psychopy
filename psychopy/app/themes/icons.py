import re
from abc import ABC

import numpy
import wx
from pathlib import Path
from psychopy import prefs
from . import theme as appTheme

retStr = ""
resources = Path(prefs.paths['resources'])
iconCache = {}


class BaseIcon:
    def __init__(self, stem, size=None, theme=None):
        # Initialise bitmaps array
        self.bitmaps = {}
        self._bitmap = None
        self.size = size

        if theme in (appTheme.icons, None) and stem in iconCache:
            # Duplicate relevant attributes if relevant (depends on subclass)
            self.bitmaps = iconCache[stem].bitmaps
        else:
            # Use subclass-specific populate call to create bitmaps
            self._populate(stem, theme=theme)
            # Set size
            self.size = size
            # Store ref to self in iconCache if using app theme
            if theme in (appTheme.icons, None):
                iconCache[stem] = self

    def _populate(self, stem, theme=None):
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
        # Clear bitmap cache
        self._bitmap = None

    @property
    def bitmap(self):
        if self._bitmap is None:
            # Get list of sizes cached
            cachedSizes = list(self.bitmaps)
            # If we don't have any cached sizes, return a blank bitmap
            if not len(cachedSizes):
                return wx.Bitmap()

            if self.size in cachedSizes:
                # If requested size is cached, return it
                self._bitmap = self.bitmaps[self.size]
            elif self.size[1] is None and self.size[0] is not None:
                # If height is None, check for correct width
                widths = [w for w, h in cachedSizes]
                if self.size[0] in widths:
                    i = widths.index(self.size[0])
                    self._bitmap = self.bitmaps[cachedSizes[i]]
            elif self.size[0] is None and self.size[1] is not None:
                # If width is None, check for correct height
                heights = [h for w, h in cachedSizes]
                if self.size[1] in heights:
                    i = heights.index(self.size[1])
                    self._bitmap = self.bitmaps[cachedSizes[i]]
            elif self.size[0] is None and self.size[1] is None:
                # If both size values are None, use biggest bitmap
                areas = [w * h for w, h in cachedSizes]
                i = areas.index(max(areas))
                self._bitmap = self.bitmaps[cachedSizes[i]]
            else:
                # Otherwise, resize the closest bitmap in size
                areas = [w * h for w, h in cachedSizes]
                area = self.size[0] * self.size[1]
                deltas = [abs(area - a) for a in areas]
                i = deltas.index(min(deltas))
                bmp = self.bitmaps[cachedSizes[i]]
                self._bitmap = self.resizeBitmap(bmp, self.size)
                self.bitmaps[self._bitmap.GetWidth(), self._bitmap.GetHeight()] = self._bitmap

        return self._bitmap

    @staticmethod
    def resizeBitmap(bmp, size=None):
        assert isinstance(bmp, wx.Bitmap), (
            "Bitmap supplied to `resizeBitmap()` must be a `wx.Bitmap` object."
        )
        # If size is None, return bitmap as is
        if size in (None, (None, None)):
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

    def _populate(self, stem, theme=None):
        # Use current theme if none requested
        if theme is None:
            theme = appTheme.icons
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
        for file in files.values():
            bmp = wx.Bitmap(str(file), wx.BITMAP_TYPE_PNG)
            self.bitmaps[(bmp.GetWidth(), bmp.GetHeight())] = bmp


class ComponentIcon(BaseIcon):

    def _populate(self, cls, theme=None):
        # Throw error if class doesn't have associated icon file
        if not hasattr(cls, "iconFile"):
            raise AttributeError(
                f"Could not retrieve icon for {cls} as the class does not have an `iconFile` attribute."
            )
        # Use current theme if none requested
        if theme is None:
            theme = appTheme.icons
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
        bmp = wx.Bitmap(img)
        self.bitmaps[(bmp.GetWidth(), bmp.GetHeight())] = bmp

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
