#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for the use with the :py:class:`~psychopy.visual.rift.Rift` class.

This module exposes additional useful classes and functions from PsychXR without
needing to explicitly import the PsychXR library into your project. If PsychXR
is not available on your system, class objects will be `None`.

Copyright (C) 2019 - Matthew D. Cutone, The Centre for Vision Research, Toronto,
Ontario, Canada

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['LibOVRPose',
           'LibOVRPoseState',
           'LibOVRBounds',
           'LibOVRHapticsBuffer',
           'isHmdConnected',
           'isOculusServiceRunning']

_HAS_PSYCHXR_ = True

try:
    import psychxr.libovr as libovr
except ImportError:
    _HAS_PSYCHXR_ = False


LibOVRPose = libovr.LibOVRPose if _HAS_PSYCHXR_ else None
LibOVRPoseState = libovr.LibOVRPoseState if _HAS_PSYCHXR_ else None
LibOVRBounds = libovr.LibOVRBounds if _HAS_PSYCHXR_ else None
LibOVRHapticsBuffer = libovr.LibOVRHapticsBuffer if _HAS_PSYCHXR_ else None


def isHmdConnected(timeout=0):
    """Check if an HMD is connected.

    Parameters
    ----------
    timeout : int
        Timeout in milliseconds.

    Returns
    -------
    bool
        `True` if an HMD is connected.

    """
    if _HAS_PSYCHXR_:
        return libovr.isHmdConnected(timeout)

    return False


def isOculusServiceRunning(timeout=0):
    """Check if the Oculus(tm) service is currently running.

    Parameters
    ----------
    timeout : int
        Timeout in milliseconds.

    Returns
    -------
    bool
        `True` if the service is loaded and running.

    """
    if _HAS_PSYCHXR_:
        return libovr.isOculusServiceRunning(timeout)

    return False
