#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for the Oculus Rift.

Copyright (C) 2018 - Matthew D. Cutone, The Centre for Vision Research, Toronto,
Ontario, Canada

"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import psychxr.ovr as ovr

# math types exposed by PsychXR
ovrSizei = ovr.math.ovrSizei
ovrRect = ovr.math.ovrRecti
ovrVector3f = ovr.math.ovrVector3f
ovrMatrix4f = ovr.math.ovrMatrix4f
ovrQuat = ovr.math.ovrQuatf
ovrPosef = ovr.math.ovrPosef
ovrFovPort = ovr.math.ovrFovPort

# misc constants exposed by PsychXR
OVR_EYE_LEFT = ovr.capi.ovrEye_Left
OVR_EYE_RIGHT = ovr.capi.ovrEye_Right
OVR_HAND_LEFT = 0
OVR_HAND_RIGHT = 1
