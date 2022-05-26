#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Extensible set of components for the PsychoPy Builder view
"""

import os
import glob
import copy
import shutil
from os.path import join, dirname, abspath, split
from importlib import import_module  # helps python 2.7 -> 3.x migration
from ._base import BaseVisualComponent, BaseComponent
from ..params import Param
from psychopy.localization import _translate
from psychopy.experiment import py2js
import psychopy.logging as logging

excludeComponents = ['BaseComponent', 'BaseVisualComponent', 'BaseStandaloneRoutine'  # templates only
                     ]  # this one isn't ready yet

pluginComponents = {}  # components registered by loaded plugins

# try to remove old pyc files in case they're detected as components
pycFiles = glob.glob(join(split(__file__)[0], "*.pyc"))
for filename in pycFiles:
    # check for matching py file
    if not os.path.isfile(filename[:-2]):
        try:
            os.remove(filename)
        except:
            pass  # may not have sufficient privs


def getAllCategories(folderList=()):
    allComps = getAllComponents(folderList)
    # Hardcode some categories to always appear first/last
    firstCats = ['Favorites', 'Stimuli', 'Responses', 'Custom']
    lastCats = ['I/O', 'Other']
    # Start getting categories
    allCats = firstCats
    for name, thisComp in list(allComps.items()):
        for thisCat in thisComp.categories:
            if thisCat not in allCats + lastCats:
                allCats.append(thisCat)
    return allCats + lastCats


def getAllComponents(folderList=(), fetchIcons=True):
    """Get a dictionary of all available components, from the builtins as well
    as all folders in the folderlist.
    User-defined components will override built-ins with the same name.
    """
    if isinstance(folderList, str):
        raise TypeError('folderList should be iterable, not a string')
    components = getComponents(fetchIcons=fetchIcons)  # get the built-ins
    for folder in folderList:
        userComps = getComponents(folder)
        for thisKey in userComps:
            components[thisKey] = userComps[thisKey]

    # add components registered by plugins that have been loaded
    components.update(pluginComponents)

    return components


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
       `from psychopy.experiment.components import BaseComponent, Param`
    """
    if folder is None:
        pth = folder = dirname(__file__)
        pkg = 'psychopy.experiment.components'
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
            explicit_rel_path = pkg + '.' + cmpfile[:-3]
        else:
            explicit_rel_path = pkg + '.' + cmpfile
        try:
            module = import_module(explicit_rel_path, package=pkg)
        except ImportError:
            logging.error(
                'Failed to load component package `{}`. Does it have a '
                '`__init__.py`?'.format(cmpfile))
            continue  # not a valid module (no __init__.py?)
            
        # check for orphaned pyc files (__file__ is not a .py file)
        if hasattr(module, '__file__'):
            if not module.__file__:
                # with Py3, orphans have a __pycharm__ folder but no file
                continue
            elif module.__file__.endswith('.pyc'):
                # with Py2, orphans have a xxxxx.pyc file
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

                if hasattr(module, 'tooltip'):
                    tooltips[name] = module.tooltip
                if hasattr(components[attrib], 'iconFile'):
                    iconFiles[name] = components[attrib].iconFile
                # assign the module categories to the Component
                if not hasattr(components[attrib], 'categories'):
                    components[attrib].categories = ['Custom']
    return components



def getInitVals(params, target="PsychoPy"):
    """Works out a suitable initial value for a parameter (e.g. to go into the
    __init__ of a stimulus object, avoiding using a variable name if possible
    """
    inits = copy.deepcopy(params)
    for name in params:
        if target == "PsychoJS":
            # convert (0,0.5) to [0,0.5] but don't convert "rand()" to "rand[]" and don't convert text
            valStr = str(inits[name].val).strip()
            if valStr.startswith("(") and valStr.endswith(")") and name != 'text':
                inits[name].val = py2js.expression2js(inits[name].val)
            # filenames (e.g. for image) need to be loaded from resources
            if name in ["sound"]:
                val = str(inits[name].val)
                if val not in [None, 'None', 'none', '']:
                    inits[name].val = ("psychoJS.resourceManager.getResource({})"
                                       .format(inits[name]))
                    inits[name].valType = 'code'

        if not hasattr(inits[name], 'updates'):  # might be settings parameter instead
            continue

        # value should be None (as code)
        elif inits[name].val in [None, 'None', 'none', '']:
            if name in ['text']:
                inits[name].val = None
                inits[name].valType = 'extendedStr'
            else:
                inits[name].val = 'None'
                inits[name].valType = 'code'

        # is constant so don't touch the parameter value
        elif inits[name].updates in ['constant', None, 'None']:
            continue  # things that are constant don't need handling

        # is changing so work out a reasonable default
        elif name in ['pos', 'fieldPos']:
            inits[name].val = '[0,0]'
            inits[name].valType = 'code'
        elif name in ['color', 'foreColor', 'borderColor', 'lineColor', 'fillColor']:
            inits[name].val = 'white'
            inits[name].valType = 'str'
        elif name in ['ori', 'sf', 'size', 'height', 'letterHeight', 'lineWidth',
                      'phase', 'opacity',
                      'volume',  # sounds
                      'coherence', 'nDots', 'fieldSize', 'dotSize', 'dotLife',
                      'dir', 'speed',
                      'contrast', 'moddepth', 'envori', 'envphase', 'envsf',
                      'noiseClip', 'noiseBWO', 'noiseFilterUpper', 'noiseFilterLower',
                      'noiseBaseSf', 'noiseBW', 'noiseElementSize', 'noiseFilterOrder',
                      'noiseFractalPower']:
            inits[name].val = "1.0"
            inits[name].valType = 'code'
        elif name in ['image', 'mask', 'envelope', 'carrier']:
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
            inits[name].val = ""
            inits[name].valType = 'str'
        elif name == 'flip':
            inits[name].val = ""
            inits[name].valType = 'str'
        elif name == 'sound':
            inits[name].val = "A"
            inits[name].valType = 'str'
        elif name == 'blendmode':
            inits[name].val = "avg"
            inits[name].valType = 'str'
        elif name == 'beat':
            inits[name].val = "False"
            inits[name].valType = 'str'
        elif name == 'noiseImage':
            inits[name].val = "None"
            inits[name].valType = 'str'
        elif name == 'noiseType':
            inits[name].val = 'Binary'
            inits[name].valType = 'str'
        elif name == 'emotiv_marker_label':
            inits[name].val = 'Label'
            inits[name].valType = 'str'
        elif name == 'emotiv_marker_value':
            inits[name].val = 'Value'
            inits[name].valType = 'str'
        elif name == 'buttonRequired':
            inits[name].val = "True"
            inits[name].valType = 'code'
        elif name == 'vertices':
            inits[name].val = "[[-0.5,-0.5], [-0.5, 0.5], [0.5, 0.5], [0.5, -0.5]]"
            inits[name].valType = 'code'
        elif name == 'movie':
            inits[name].val = 'None'
            inits[name].valType = 'code'
        else:
            print("I don't know the appropriate default value for a '%s' "
                  "parameter. Please email the mailing list about this error" %
                  name)

    return inits

tooltips = {}
iconFiles = {}
