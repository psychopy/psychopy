#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for using trigger boxes.

Trigger boxes are used to send electrical signals to external devices. They are
typically used to synchronize the presentation of stimuli with the recording of
physiological data. This module provides a common interface for accessing
trigger boxes from within PsychoPy.

This module serves as the entry point for plugin classes implementing
third-party trigger box interfaces. All installed interfaces are discoverable
by calling the :func:`getAllTriggerBoxes()` function. To have your trigger box
interface discovered by PsychoPy, you need to create a Python module that
defines a class inheriting from :class:`BaseTriggerBox` and set its entry point
to ``psychopy.hardware.triggerbox`` in your plugin setup script or configuration 
file.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'BaseTriggerBox',
    'ParallelPortTrigger',
    'getAllTriggerBoxes'
]

from psychopy.hardware.triggerbox.base import BaseTriggerBox
from psychopy.hardware.triggerbox.parallel import ParallelPortTrigger


def getAllTriggerBoxes():
    """Get all trigger box interface classes.

    Returns
    -------
    dict
        Mapping of trigger box classes.

    """
    foundTriggerBoxes = {}
    # todo: handle legacy names

    # classes from this namespace
    foundTriggerBoxes.update({
        name: cls for name, cls in globals().items()
            if isinstance(cls, type) and issubclass(cls, BaseTriggerBox)
                and cls is not BaseTriggerBox})  # exclude `BaseTriggerBox`

    return foundTriggerBoxes


if __name__ == "__main__":
    pass
