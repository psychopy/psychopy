:mod:`psychopy.iohub` - Asynchronous Event Processing
=====================================================

:mod:`psychopy.iohub` (ioHub) provides access many common devices used in
psychology research experiments.

ioHub processes device events in parallel with PsychoPy experiment
execution by running in a separate process from the PsychoPy experiment
Python runtime. This means, for instance, that keyboard and mouse events
are processed and time stamped quickly, regardless of whether the PsychoPy
experiment script is in a blocking state when the event is received.
The experiment blocks, for example, from when
:func:`psychopy.visual.window.flip()`
is called until the start of the next screen retrace.

ioHub device events can be accessed during experiment runtime via the
class:`psychopy.iohub.client.ioHubConnection` object. Optionally, events can
be saved to a `HDF5 <http://www.hdfgroup.org/HDF5/>`_ file.

All iohub events are timestamped using the same clock used by the
:func:`psychopy.core.getTime` function, making the comparison of important
experiment times and iohub event times straight forward.

A comprehensive set of examples that each use at least one of the iohub devices
is available in the psychopy/demos/coder/iohub folder.

.. note::

    This documentation is in very early stages of being written. Many sections
    regarding device usage details are simply placeholders.
    For information on devices or functionality that has not yet been migrated
    to the psychopy documentation, please visit the somewhat outdated
    `original ioHub doc's. <http://www.isolver-solutions.com/iohubdocs/>`_

Using psychopy.iohub:
-----------------------

.. toctree::
    :maxdepth: 2
    :glob:

    iohub/requirements
    iohub/starting
    iohub/devices

