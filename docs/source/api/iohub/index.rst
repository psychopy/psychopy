:mod:`psychopy.iohub` - ioHub event monitoring framework
=========================================================

ioHub monitors for device events in parallel with the PsychoPy experiment
execution by running in a separate process than the main PsychoPy script. This
means, for instance, that keyboard and mouse event timing is not quantized
by the rate at which the window.flip() method is called.

ioHub reports device events to the PsychoPy experiment runtime as they occur.
Optionally, events can be saved to a `HDF5 <http://www.hdfgroup.org/HDF5/>`_
file.

All iohub events are timestamped using the PsychoPy global time base
(psychopy.core.getTime()). Events can be accessed as a device independent
event stream, or from a specific device of interest.

A comprehensive set of examples that each use at least one of the iohub devices
is available in the psychopy/demos/coder/iohub folder.

.. note::

    This documentation is in very early stages of being written. Comments and
    contributions are welcome.

.. toctree::
   :maxdepth: 2
   :glob:

   starting
   devices
   requirements
