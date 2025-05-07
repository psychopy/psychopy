#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for spatial tracking devices in PsychoPy.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import psychopy.tools.mathtools as mt
import numpy as np


class TrackerData:
    """Class for storing motion tracking data.

    This class is used to store data from a motion tracking device. The data
    includes the position and orientation of the tracker, as well as the
    angular and linear velocity and acceleration values reported by the device.

    Parameters
    ----------
    absSampleTime : float
        The absolute sample time of the tracker data in seconds.
    pos : tuple
        The position of the tracker in [x, y, z] coordinates.
    ori : tuple
        The orientation of the tracker in [x, y, z, w] quaternion.
    linearVelocity : tuple
        The linear velocity of the tracker in [vx, vy, vz] coordinates.
    angularVelocity : tuple
        The angular velocity of the tracker in [vx, vy, vz] coordinates.
    linearAcceleration : tuple
        The linear acceleration of the tracker in [ax, ay, az] coordinates.
    angularAcceleration : tuple
        The angular acceleration of the tracker in [ax, ay, az] coordinates.
    compassHeading : float
        The compass heading of the tracker in degrees.

    """
    def __init__(
            self, 
            absSampleTime,
            pos=(0., 0., 0.),
            ori=(0., 0., 0., 1.),
            linearVelocity=(0., 0., 0.),
            angularVelocity=(0., 0., 0.),
            linearAcceleration=(0., 0., 0.),
            angularAcceleration=(0., 0., 0.),
            compassHeading=0.0):
        
        # time the data was sampled from the device
        self._absSampleTime = float(absSampleTime)

        # tracker pose
        self._thePose = mt.RigidBodyPose(pos, ori, dtype=float)

        # IMU data
        self._angularVelocity = np.asarray(angularVelocity, dtype=float)
        self._linearVelocity = np.asarray(linearVelocity, dtype=float)
        self._angularAcceleration = np.asarray(linearAcceleration, dtype=float)
        self._linearAcceleration = np.asarray(angularAcceleration, dtype=float)
        self._compassHeading = float(compassHeading)

    @property
    def thePose(self):
        """The pose of the tracker in 3D space.

        Returns
        -------
        RigidBodyPose
            The pose of the tracker.

        """
        return self._thePose 
    
    @thePose.setter
    def thePose(self, value):
        if not isinstance(value, mt.RigidBodyPose):
            raise TypeError("Expected a `RigidBodyPose` object.")
        
        self._thePose = value

    @property
    def pos(self):
        """Return the position of the tracker.

        Returns
        -------
        numpy.ndarray
            The position of the tracker.

        """
        return self._trackerPose.getPos()
    
    @pos.setter
    def pos(self, value):
        self._trackerPose.setPos(value)

    @property
    def ori(self):
        """Return the orientation of the tracker.

        Returns
        -------
        numpy.ndarray
            The orientation of the tracker.

        """
        return self._trackerPose.getOri()

    @ori.setter
    def ori(self, value):
        self._trackerPose.setOri(value)

    @property
    def posOri(self):
        """Return the position and orientation of the tracker.

        Returns
        -------
        tuple
            The position and orientation of the tracker.

        """
        return self._trackerPose.getPosOri()

    @posOri.setter
    def posOri(self, value):
        self._trackerPose.setPosOri(value)

    @property
    def absSampleTime(self):
        """Return the absolute sample time of the tracker data.

        Returns
        -------
        float
            The absolute sample time of the tracker data.

        """
        return self._absSampleTime
    
    @absSampleTime.setter
    def absSampleTime(self, value):
        self._absSampleTime = float(value)

    @property
    def angularVelocity(self):
        """Return the angular velocity of the tracker.

        Returns
        -------
        numpy.ndarray
            The angular velocity of the tracker.

        """
        return self._angularVelocity
    
    @angularVelocity.setter
    def angularVelocity(self, value):
        self._angularVelocity[:] = value
    
    @property
    def linearVelocity(self):
        """Return the linear velocity of the tracker.

        Returns
        -------
        numpy.ndarray
            The linear velocity of the tracker.

        """
        return self._linearVelocity
    
    @linearVelocity.setter
    def linearVelocity(self, value):
        self._linearVelocity[:] = value

    @property
    def angularAcceleration(self):
        """Return the angular acceleration of the tracker.

        Returns
        -------
        numpy.ndarray
            The angular acceleration of the tracker.

        """
        return self._angularAcceleration
    
    @angularAcceleration.setter
    def angularAcceleration(self, value):
        self._angularAcceleration[:] = value
    
    @property
    def linearAcceleration(self):
        """Return the linear acceleration of the tracker.

        Returns
        -------
        numpy.ndarray
            The linear acceleration of the tracker.

        """
        return self._linearAcceleration
    
    @linearAcceleration.setter
    def linearAcceleration(self, value):
        self._linearAcceleration[:] = value

    @property
    def compassHeading(self):
        """Return the compass heading of the tracker.

        Returns
        -------
        float
            The compass heading of the tracker.

        """
        return self._compassHeading
    
    @compassHeading.setter
    def compassHeading(self, value):
        self._compassHeading = value


if __name__ == "__main__":
    pass

