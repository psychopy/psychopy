.. _BitsSharp:

:class:`BitsSharp`
------------------------------------------------------------------------

.. currentmodule:: psychopy.hardware.crs.bits

Control a CRS Bits# device. See typical usage in the class summary (and in the
menu demos>hardware>BitsBox of PsychoPy's Coder view).

Attributes
=============

.. autosummary::

    BitsSharp
    BitsSharp.mode
    BitsSharp.isAwake
    BitsSharp.getInfo
    BitsSharp.checkConfig
    BitsSharp.gammaCorrectFile
    BitsSharp.temporalDithering
    BitsSharp.monitorEDID
    BitsSharp.beep
    BitsSharp.getVideoLine
    BitsSharp.start
    BitsSharp.stop

Direct communications with the serial port:

.. autosummary::

    BitsSharp.sendMessage
    BitsSharp.getResponse

Control the CLUT (Bits++ mode only):

.. autosummary::

    BitsSharp.setContrast
    BitsSharp.setGamma
    BitsSharp.setLUT



Details
=============

.. autoclass:: BitsSharp
    :members:
    :undoc-members: read
    :inherited-members: