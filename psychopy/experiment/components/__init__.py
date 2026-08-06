#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Extensible set of components for the PsychoPy Builder view.
"""

from pathlib import Path
import os
import glob
import copy
import inspect
from os.path import join, split
import importlib, importlib.metadata
from ._base import BaseVisualComponent, BaseComponent, BaseDeviceComponent
from ..params import Param
from psychopy.localization import _translate
from psychopy.experiment import py2js
import psychopy.logging as logging

excludeComponents = [
    'BaseComponent',
    'BaseVisualComponent',
    'BaseDeviceComponent',
]  # this one isn't ready yet

# Plugin components are added dynamically at runtime, usually from plugin
# packages. These are managed by a different system than 'legacy'
# components.
pluginComponents = {}

# try to remove old pyc files in case they're detected as components
pycFiles = glob.glob(join(split(__file__)[0], "*.pyc"))
for filename in pycFiles:
    # check for matching py file
    if not os.path.isfile(filename[:-2]):
        try:
            os.remove(filename)
        except OSError:
            pass  # may not have sufficient privs


def addComponent(compClass):
    """Add a component to Builder.

    This function will override any component already loaded with the same
    class name. Usually, this function is called by the plugin system. The user
    typically does not need to call this.

    Parameters
    ----------
    compClass : object
        Component class. Should be a subclass of `BaseComponent`.

    """
    global pluginComponents  # components loaded at runtime

    compName = compClass.__name__
    logging.debug("Registering Builder component class `{}`.".format(compName))

    # check type and attributes of the class
    if not issubclass(compClass, (BaseComponent, BaseVisualComponent)):
        return
    elif not hasattr(compClass, 'categories'):
        logging.warning(
            "Component `{}` does not define a `.categories` attribute.".format(
                compName))

    pluginComponents[compName] = compClass


def getAllCategories(folderList=(), fetchIcons=False):
    """Get all component categories.

    Parameters
    ----------
    folderList : list or tuple
        List of directories to search for components. These are for
        'legacy'-style components. Using plugins is now the prefered method of
        adding components to Builder.

    Returns
    -------
    list of str
        Names of all categories which the working set of components specify.

    """
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


def filterComponent(comp):
    """
    Function for filtering Components to remove e.g. base classes and excluded Components.

    Parameters
    ----------
    comp : BaseComponent
        Class of the Component to check
    
    Returns
    -------
    bool
        True if Component is fine to include
    """
    # filter non-classes
    if not inspect.isclass(comp):
        return False
    # SettingsComponent is a special case (not a subclass of BaseComponent)
    if comp.__name__ == "SettingsComponent":
        return True
    # filter non-Components
    if not issubclass(comp, BaseComponent):
        return False
    # filter protected classes
    if comp.__name__.startswith("_"):
        return False
    # filter base Components
    if comp.__name__.lower().startswith("base"):
        return False
    # filter unknown Components
    if comp.__name__.lower().startswith("unknown"):
        return False
    # filter ignored Components
    if comp.__name__ in excludeComponents:
        return False
    
    return True


def getAllComponents(folderList=None, fetchIcons=True):
    """
    Get all available components, from the builtins, plugins and folders.

    User-defined components will override built-ins with the same name.

    Parameters
    ----------
    folderList : list or tuple
        List of additional directories to search for components.
    fetchIcons : bool
        Whether to also fetch icons. Default is `True`.

    """
    # make sure folder list is iterable
    if folderList is None:
        folderList = []
    if isinstance(folderList, str):
        folderList = [folderList]
    
    # get builtin Components
    components = getComponents()

    # find plugin Components...
    for point in importlib.metadata.entry_points(group="psychopy.experiment.components"):
        # load entry point
        member = point.load()
        # if it's a Component, add it
        if filterComponent(member):
            components[member.__name__] = member

    # get Components from folder list
    for folder in folderList:
        for key, value in getComponents(folder).items():
            if filterComponent(value):
                components[key] = value

    return components


def getComponents(folder=None, package=None, fetchIcons=False):
    """
    Get Component classes from a given directory and package. Leave folder and package as None to 
    get Components from the folder/package within PsychoPy.

    Component classes should be a subclass of BaseComponent, their name should end with "Component" 
    and they should be available from the __init__.py file of a module under the given 
    folder/package.

    Parameters
    ----------
    folder : Path
        Folder to search in, if None will use the folder of psychopy.experiment.components
    package : str
        Package spec of the given folder, if None will use psychopy.experiment.components
    """
    # default to components folder
    if folder is None:
        folder = Path(__file__).parent
    # default to components package
    if package is None:
        package = "psychopy.experiment.components"
    # make sure folder is a Path
    folder = Path(folder)

    # start with blank dict
    components = {}
    # search folder for modules which look like they contain a Component...
    for subfolder in folder.glob("*/__init__.py"):
        # import each submodule
        mod = importlib.import_module(
            f"{package}.{subfolder.parent.stem}"
        )
        # go through members in module
        for attrib in dir(mod):
            # get member
            member = getattr(mod, attrib)
            # if member is a Component, add it
            if filterComponent(member):
                components[member.__name__] = member

    return components


def getInitVals(params, target="PsychoPy"):
    """Works out a suitable initial value for a parameter (e.g. to go into the
    __init__ of a stimulus object, avoiding using a variable name if possible
    """
    inits = copy.deepcopy(params)
    # Alias units = from exp settings with None
    if 'units' in inits and str(inits['units'].val).lower() in (
            "from experiment settings",
            "from exp settings",
            "none"
    ):
        if target == "PsychoJS":
            inits['units'].val = "psychoJS.window.units"
        else:
            inits['units'].val = "win.units"

        inits['units'].valType = 'code'

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
                inits[name].val = None
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
                      'noiseFractalPower', 'zoom']:
            inits[name].val = "1.0"
            inits[name].valType = 'code'
        elif name in ['progress']:
            inits[name].val = "0.0"
            inits[name].valType = 'code'
        elif name in ['image']:
            inits[name].val = "default.png"
            inits[name].valType = 'str'
        elif name in ['mask', 'envelope', 'carrier']:
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
        elif name in ('text', 'placeholder'):
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
        elif name == 'shape':
            inits[name].val = 'triangle'
            inits[name].valType = 'str'
        elif name in ('movie', 'latitude', 'longitude', 'elevation', 'azimuth', 'speechPoint'):
            inits[name].val = 'None'
            inits[name].valType = 'code'
        elif name == 'allowedKeys':
            inits[name].val = "[]"
            inits[name].valType = 'code'
        elif name == "deviceLabel":
            inits[name].valType = "device"
        else:
            # if not explicitly handled, default to None
            inits[name].val = "None"
            inits[name].valType = "code"

    return inits


tooltips = {}
iconFiles = {}

if __name__ == "__main__":
    pass

