"""
Tools for interacting with various stimuli.

For example, lists of styles for Form/Slider, so that these static values
can be quickly imported from here rather than importing `psychopy.visual` (which is slow)
"""

import inspect
import json
import numpy as np
from psychopy import logging
from psychopy.tools.attributetools import attributeSetter


formStyles = {
    'light': {
        'fillColor': [0.89, 0.89, 0.89],
        'borderColor': None,
        'itemColor': 'black',
        'responseColor': 'black',
        'markerColor': [0.89, -0.35, -0.28],
        'font': "Open Sans",
    },
    'dark': {
        'fillColor': [-0.19, -0.19, -0.14],
        'borderColor': None,
        'itemColor': 'white',
        'responseColor': 'white',
        'markerColor': [0.89, -0.35, -0.28],
        'font': "Open Sans",
    },
}

sliderStyles = ['slider', 'rating', 'radio', 'scrollbar', 'choice']
sliderStyleTweaks = ['labels45', 'triangleMarker']


class SerializationError(Exception):
    """
    Error raised when serialize is called on a value which is not serializable.
    """
    pass


def serialize(obj):
    """
    Get a JSON string representation of this stimulus, useful for recreating it in a different 
    process. Will attempt to create a dict based on the object's `__init__` method, so that this 
    can be used to create a new copy of the object. Attributes which are themselves serializable 
    will be recursively serialized.

    Parameters
    ----------
    obj : object
        Object to serialize.
    
    Raises
    ------
    SerializationError
        If the object is not already serialized and cannot be serialized.
    
    Returns
    -------
    str
        Either a dict, or a JSON string of a dict, representing the object.
    """
    # handle numpy types
    if isinstance(obj, np.integer):
        obj = int(obj)
    elif isinstance(obj, np.floating):
        obj = float(obj)
    elif isinstance(obj, np.ndarray):
        obj = obj.tolist()
    # if an array, serialize items
    if isinstance(obj, (list, tuple)):
        return [serialize(val) for val in obj]
    if isinstance(obj, dict):
        return {serialize(key): serialize(val) for key, val in obj.items()}
    # if already json serializable, return as is
    try:
        json.dumps(obj)
    except TypeError:
        pass
    except:
        # if we got something other than a TypeError, substitute None
        return None
    else:
        return obj
    # if object defines its own serialization, use it
    if hasattr(obj, "serialize"):
        return obj.serialize()
    
    def _getAttr(obj, param):
        """
        Get serialized attribute value.
        """
        got = False
        # if param looks to be stored in an attribute, add it
        if hasattr(obj, param):
            got = True
            value = getattr(obj, param)
        # if we have a get method for param, get its value
        getParam = "get" + param[0].upper() + param[1:]
        if hasattr(obj, getParam):
            got = True
            value = getattr(obj, getParam)()
        # if we couldn't get a value, raise an error
        if not got:
            raise SerializationError(f"Could not get value for {type(obj).__name__}.{param}")

        return serialize(value)
    
    # start off with an empty dict
    arr = {}
    # get init args
    initArgs = inspect.getargspec(obj.__init__)
    # if there are variable args, raise an error
    if initArgs.varargs:
        raise SerializationError("Cannot serialize object with variable args.")
    # how many init args are required?
    nReq = len(initArgs.args) - len(initArgs.defaults)
    # get required params
    for param in initArgs.args[:nReq]:
        # skip self
        if param == "self":
            continue
        # get attribute
        arr[param] = _getAttr(obj, param)
    # get optional params
    for param in initArgs.args[nReq:]:
        # get attribute, but don't worry if it fails
        try:
            arr[param] = _getAttr(obj, param)
        except SerializationError:
            pass
    
    return arr

