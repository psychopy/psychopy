"""Extensible set of components for the PsychoPy Builder view
"""
# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import

import os
import glob
import copy
import shutil
import wx
from PIL import Image
from os.path import join, dirname, abspath, split
from importlib import import_module  # helps python 2.7 -> 3.x migration

excludeComponents = ['BaseComponent', 'BaseVisualComponent',  # templates only
                     'EyetrackerComponent']  # this one isn't ready yet

# try to remove old pyc files in case they're detected as components
pycFiles = glob.glob(join(split(__file__)[0], "*.pyc"))
for filename in pycFiles:
    # check for matching py file
    if not os.path.isfile(filename[:-2]):
        try:
            os.remove(filename)
        except:
            pass  # may not have sufficient privs
        
def pilToBitmap(pil, scaleFactor=1.0):
    image = wx.EmptyImage(pil.size[0], pil.size[1])

    try:  # For PIL.
        image.SetData(pil.convert("RGB").tostring())
        image.SetAlphaData(pil.convert("RGBA").tostring()[3::4])
    except Exception:  # For Pillow.
        image.SetData(pil.convert("RGB").tobytes())
        image.SetAlphaData(pil.convert("RGBA").tobytes()[3::4])

    image.Rescale(image.Width * scaleFactor, image.Height * scaleFactor)
    return image.ConvertToBitmap()  # wx.Image and wx.Bitmap are different


def getIcons(filename=None):
    """Creates wxBitmaps ``self.icon`` and ``self.iconAdd`` based on the the image.
    The latter has a plus sign added over the top.

    png files work best, but anything that wx.Image can import should be fine
    """
    icons = {}
    if filename is None:
        filename = join(dirname(abspath(__file__)), 'base.png')
        
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
    add = Image.open(join(dirname(abspath(__file__)), 'add.png'))
    im.paste(add, [0, 0, add.size[0], add.size[1]], mask=add)
    # im.paste(add, [im.size[0]-add.size[0], im.size[1]-add.size[1],
    #               im.size[0], im.size[1]], mask=add)
    icons['48add'] = pilToBitmap(im)

    return icons


def getComponents(folder=None, fetchIcons=True):
    """Get a dictionary of available components for the Builder experiments.

    If folder is None then the built-in components will be imported and
    returned, otherwise the components found in the folder provided will be.

    Changed v1.84.00:
    The Builder preference "components folders" should be of the form:
    `/.../.../compts`. This is unchanged from previously, and allows for
    backwards compatibility.

    New as of v1.84: A slightly different directory structure is needed. An
    existing directory will be automatically upgraded if the previous one
    was not empty. However, files starting with '_' will be skipped, as will any
    directories. You will need to manually move those into the new
    directory (from the old .../compts/ into the new .../compts/compts/).

    As of v1.84, a components path needs directory structure `/.../.../compts/compts`.
    That is, the path should end with the name repeated. (It does not need to
    be 'compts' literally.)
    The .py and .png files for a component should all go in this directory.
    (Previously, files were in `/.../.../compts`.) In addition, the directory
    must contain a python init file, ` /.../.../compts/compts/__init__.py`,
    to allow it to be treated as a module in python so that the components
    can be imported. For this reason, the file name for a component
    cannot begin with a number; it must be a legal python name.

    The code within the component.py file itself must use absolute paths for
    importing from psychopy:
       `from psychopy.app.builder.components._base import BaseComponent, Param`
    """
    if folder is None:
        pth = folder = dirname(__file__)
        pkg = 'psychopy.app.builder.components'
    else:
        # default shared location is often not actually a folder
        if not os.path.isdir(folder):
            return {}
        pth = folder = folder.rstrip(os.sep)
        pkg = os.path.basename(folder)
        if not folder.endswith(join(pkg, pkg)):
            folder = os.path.join(folder, pkg)

        # update the old style directory (v1.83.03) to the new style
        # try to retain backwards compatibility: copy files, not move them
        # ideally hard link them, but permissions fail on windows
        if not os.path.isdir(folder):
            files = [f for f in glob.glob(join(pth, '*'))
                     if not os.path.isdir(f) and
                     not f[0] in '_0123456789']
            if files:
                os.mkdir(folder)
                with open(join(folder, '__init__.py'), 'a') as fileh:
                    fileh.write('')
                for f in files:
                    if f.startswith('_'):
                        continue
                    shutil.copy(f, folder)
    if not pth in os.sys.path:
        os.sys.path.insert(0, pth)

    components = {}
    # setup a default icon
    if fetchIcons and 'default' not in icons.keys():
        icons['default'] = getIcons(filename=None)

    # go through components in directory
    cfiles = glob.glob(os.path.join(folder, '*.py'))  # old-style: just comp.py
    # new-style: directories w/ __init__.py
    dfiles = [d for d in os.listdir(folder)
              if os.path.isdir(os.path.join(folder, d))]
    for cmpfile in cfiles + dfiles:
        cmpfile = os.path.split(cmpfile)[1]
        if cmpfile[0] in '_0123456789':  # __init__.py, _base.py, leading digit
            continue
        # can't use imp - breaks py2app:
        # module = imp.load_source(file[:-3], fullPath)
        # v1.83.00 used exec(implicit-relative), no go for python3:
        # exec('import %s as module' % file[:-3])

        # importlib.import_module eases 2.7 -> 3.x migration
        if cmpfile.endswith('.py'):
            explicit_rel_path = '.' + cmpfile[:-3]
        else:
            explicit_rel_path = '.' + cmpfile
        module = import_module(explicit_rel_path, package=pkg)
        # check for orphaned pyc files (__file__ is not a .py file)
        if module.__file__.endswith('.pyc'):
            if not os.path.isfile(module.__file__[:-1]):
                continue  # looks like an orphaned pyc file
        # give a default category
        if not hasattr(module, 'categories'):
            module.categories = ['Custom']
        # check if module contains a component
        for attrib in dir(module):
            name = None
            # fetch the attribs that end with 'Component'
            if (attrib.endswith('omponent') and
                    attrib not in excludeComponents):
                name = attrib
                components[attrib] = getattr(module, attrib)

                # skip if this class was imported, not defined here
                if module.__name__ != components[attrib].__module__:
                    continue  # class was defined in different module

                # also try to get an iconfile
                if fetchIcons:
                    if hasattr(module, 'iconFile'):
                        icons[name] = getIcons(module.iconFile)
                    else:
                        icons[name] = icons['default']
                if hasattr(module, 'tooltip'):
                    tooltips[name] = module.tooltip
                # assign the module categories to the Component
                if not hasattr(components[attrib], 'categories'):
                    components[attrib].categories = ['Custom']
    return components


def getAllComponents(folderList=(), fetchIcons=True):
    """Get a dictionary of all available components, from the builtins as well
    as all folders in the folderlist.

    User-defined components will override built-ins with the same name.
    """
    if isinstance(folderList, basestring):
        raise TypeError, 'folderList should be iterable, not a string'
    components = getComponents(fetchIcons=fetchIcons)  # get the built-ins
    for folder in folderList:
        userComps = getComponents(folder)
        for thisKey in userComps.keys():
            components[thisKey] = userComps[thisKey]
    return components


def getAllCategories(folderList=()):
    allComps = getAllComponents(folderList)
    allCats = ['Stimuli', 'Responses', 'Custom']
    for name, thisComp in allComps.items():
        for thisCat in thisComp.categories:
            if thisCat not in allCats:
                allCats.append(thisCat)
    return allCats


def getInitVals(params):
    """Works out a suitable initial value for a parameter (e.g. to go into the
    __init__ of a stimulus object, avoiding using a variable name if possible
    """
    inits = copy.deepcopy(params)
    for name in params.keys():

        if not hasattr(inits[name], 'updates'):  # might be settings parameter instead
            continue

        # value should be None (as code)
        elif inits[name].val in [None, 'None', 'none', '']:
            inits[name].val = 'None'
            inits[name].valType = 'code'

        # is constant so don't touch the parameter value
        elif inits[name].updates in ['constant', None, 'None']:
            continue  # things that are constant don't need handling

        # is changing so work out a reasonable default
        elif name in ['pos', 'fieldPos']:
            inits[name].val = '[0,0]'
            inits[name].valType = 'code'
        elif name in ['ori', 'sf', 'size', 'height', 'letterHeight',
                      'color', 'lineColor', 'fillColor',
                      'phase', 'opacity',
                      'volume',  # sounds
                      'coherence', 'nDots', 'fieldSize', 'dotSize', 'dotLife',
                      'dir', 'speed']:
            inits[name].val = "1.0"
            inits[name].valType = 'code'
        elif name in ['image', 'mask']:
            inits[name].val = "sin"
            inits[name].valType = 'str'
        elif name == 'texture resolution':
            inits[name].val = "128"
            inits[name].valType = 'code'
        elif name == 'colorSpace':
            inits[name].val = "rgb"
            inits[name].valType = 'str'
        elif name == 'font':
            inits[name].val = "Arial"
            inits[name].valType = 'str'
        elif name == 'units':
            inits[name].val = "norm"
            inits[name].valType = 'str'
        elif name == 'text':
            inits[name].val = "default text"
            inits[name].valType = 'str'
        elif name == 'flip':
            inits[name].val = ""
            inits[name].valType = 'str'
        elif name == 'sound':
            inits[name].val = "A"
            inits[name].valType = 'str'
        else:
            print("I don't know the appropriate default value for a '%s' "
                  "parameter. Please email the mailing list about this error" %
                  name)
    return inits

tooltips = {}
icons = {}
