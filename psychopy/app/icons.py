#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""utility classes for the Builder
"""

from __future__ import absolute_import, division, print_function
from os.path import join, abspath, dirname

from pkg_resources import parse_version
from PIL import Image
import wx

from psychopy import experiment, prefs
from psychopy.experiment import components

resourcesPath = prefs.paths['resources']

def pilToBitmap(pil, scaleFactor=1.0):
    if parse_version(wx.__version__) < parse_version('4.0.0a1'):
        image = wx.EmptyImage(pil.size[0], pil.size[1])
    else:
        image = wx.Image(pil.size[0], pil.size[1])

    # set the RGB values
    if hasattr(pil, 'tobytes'):
        image.SetData(pil.convert("RGB").tobytes())
        image.SetAlphaBuffer(pil.convert("RGBA").tobytes()[3::4])
    else:
        image.SetData(pil.convert("RGB").tostring())
        image.SetAlphaData(pil.convert("RGBA").tostring()[3::4])

    image.Rescale(image.Width * scaleFactor, image.Height * scaleFactor)
    return image.ConvertToBitmap()  # wx.Image and wx.Bitmap are different


def combineImageEmblem(main, emblem, pos='top_left'):
    """

    Parameters
    ----------
    main: filename
    emblem: filename
    pos: str ('bottom_left' etc)
    size: int (default=16)

    Returns
    -------
    A wx.Bitmap of the combined image ready for use in wxButton
    """
    # load images if they aren't already loaded
    main = Image.open(main).convert('RGBA')  # might be grey or indexed colors
    emblem = Image.open(emblem).convert('RGBA')
    if 'bottom' in pos:
        y = main.size[1] - emblem.size[1]
    elif 'top' in pos:
        y = 0
    if 'right' in pos:
        x = main.size[0] - emblem.size[0]
    elif 'left' in pos:
        x = 0
    elif 'center' in pos:
        x = int(main.size[0]/2-emblem.size[1]/2)

    main.paste(emblem, (x, y), mask=emblem)
    return pilToBitmap(main)

_allIcons = None


def getAllIcons(folderList=(), forceReload=False):
    """load the icons for all the components
    """
    global _allIcons
    if forceReload or _allIcons is None:
        compons = experiment.getAllComponents(folderList)
        _allIcons = {}
        for thisName, thisCompon in compons.items():
            if thisName in components.iconFiles:
                _allIcons[thisName] = getIcons(components.iconFiles[thisName])
            else:
                _allIcons[thisName] = getIcons(None)
        return _allIcons
    else:
        return _allIcons


def getIcons(filename=None):
    """Creates wxBitmaps ``self.icon`` and ``self.iconAdd`` based on the the image.
    The latter has a plus sign added over the top.

    png files work best, but anything that wx.Image can import should be fine
    """
    icons = {}
    if filename is None:
        filename = join(resourcesPath, 'base.png')

    # get the low-res version first
    im = Image.open(filename)
    icons['24'] = pilToBitmap(im, scaleFactor=0.5)
    icons['24add'] = pilToBitmap(im, scaleFactor=0.5)
    # try to find a 128x128 version
    filename128 = filename[:-4]+'128.png'
    if False: # TURN OFF FOR NOW os.path.isfile(filename128):
        im = Image.open(filename128)
    else:
        im = Image.open(filename)
    icons['48'] = pilToBitmap(im)
    # add the plus sign
    add = Image.open(join(resourcesPath, 'add.png'))
    im.paste(add, (0, 0, add.size[0], add.size[1]), mask=add)
    # im.paste(add, [im.size[0]-add.size[0], im.size[1]-add.size[1],
    #               im.size[0], im.size[1]], mask=add)
    icons['48add'] = pilToBitmap(im)

    return icons