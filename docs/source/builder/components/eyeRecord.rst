.. _eyeRecord:

Eye Tracker Record Component
-------------------------------

The EyeRecord component can be used to start / stop eye data collection and to
access eye sample data. The coordinates of gaze positions are
given in the same coordinates as the Window, with (0,0) in the center.

Scenarios
~~~~~~~~~~~~~~~~~

This can be used in various ways.

TODO: Complete content.

Parameters
~~~~~~~~~~~~~~

TODO: complete update parameters available in EyeRecord component.

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

start :
    The time that the eye tracker should first be checked. See :ref:`startStop` for details.

stop :
    When the eye tracker is no longer checked. See :ref:`startStop` for details.

Force End Routine on Press
    If this box is checked then the :ref:`Routine <Routines>` will end as soon as one of the mouse buttons is pressed.

Save Eye State
    How often do you need to save the state of the eye(s) being tracked? Every ... TODO: complete text.
    Note that this controls how often eye data is saved to psychopy output file types, not the ioHub HDF5 file.

Time Relative To
    Whenever the eye state is saved a time is saved too. Do you want this time to be relative to start of the :ref:`Routine <Routines>`, or the start of the whole experiment?

.. seealso::

    API reference for :mod:`~psychopy.iohub.devices.EyeTracker`

