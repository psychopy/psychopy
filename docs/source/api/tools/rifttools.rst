
:mod:`psychopy.tools.rifttools`
-------------------------------

.. currentmodule:: psychopy.tools.rifttools

Various tools for working with the :py:class:`~psychopy.visual.rift.Rift` class.
The documentation for classes in on this page originate from PsychXR and may
make references to functions and objects not included with PsychoPy.

Overview
========

Classes
~~~~~~~

These classes are included with PsychXR to use with the LibOVR interface. They
can be accessed from this module to avoid needing to explicitly import PsychXR.
If PsychXR is not available on the system, these classes will have values
`None`.

.. autosummary::
    LibOVRPose
    LibOVRPoseState
    LibOVRHapticsBuffer
    LibOVRBounds

Functions
~~~~~~~~~

These functions can be called without first starting a VR session (initializing
a :py:class:`~psychopy.visual.rift.Rift` instance) to check if the
drivers/services are running on this computer or if an HMD is connected.

.. autosummary::
    isHmdConnected
    isOculusServiceRunning

Details
=======

.. autoclass:: LibOVRPose
    :members:
    :undoc-members:
    :inherited-members:

.. autoclass:: LibOVRPoseState
    :members:
    :undoc-members:
    :inherited-members:

.. autoclass:: LibOVRBounds
    :members:
    :undoc-members:
    :inherited-members:

.. autoclass:: LibOVRHapticsBuffer
    :members:
    :undoc-members:
    :inherited-members:

.. autofunction:: isHmdConnected
.. autofunction:: isOculusServiceRunning