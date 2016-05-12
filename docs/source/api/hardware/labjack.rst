.. _labjack:

labjacks (USB I/O devices)
=============================================

PsychoPy provides an interface to the labjack U3 class with a couple of minor
additions.

This is accessible by::

	from psychopy.hardware.labjacks import U3

Except for the additional `setdata` function the U3 class operates exactly as
that in the U3 library that labjack provides, documented here:

http://labjack.com/support/labjackpython

.. note::

	To use labjack devices you do need also to install the driver software
	described on the page above

.. autoclass:: psychopy.hardware.labjacks.U3
    :members: setData
