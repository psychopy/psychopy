:class:`psychopy.visual.VisualSystemHD`
---------------------------------------

Classes for using NordicNeuralLab's VisualSystemHD in-scanner display for
presenting visual stimuli. Support is preliminary so users must empirically
verify whether the default settings for barrel distortion and FOV are correct.
Support may be good enough at this point for studies that do not require precise
stereoscopy or stimulus sizes.

Overview
========

.. currentmodule:: psychopy.visual.nnlvs

.. autosummary::
    VisualSystemHD
    VisualSystemHD.monoscopic
    VisualSystemHD.lensCorrection
    VisualSystemHD.distCoef
    VisualSystemHD.diopters
    VisualSystemHD.setDiopters
    VisualSystemHD.eyeOffset
    VisualSystemHD.setEyeOffset
    VisualSystemHD.setBuffer
    VisualSystemHD.setPerspectiveView

Details
=======

.. autoclass:: VisualSystemHD
    :members:
    :undoc-members:
    :inherited-members:
