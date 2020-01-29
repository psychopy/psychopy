.. _emotiv_marking:

Emotiv Marking Component
-------------------------------

The Emotiv Marking component causes Psychopy to send a marker to the EEG datastream at the
time that the stimuli are presented.

For the Emotiv Marking component to work an emotiv_recording component should have already
been added to the experiment.

By default markers with labels and values can be added.  A time interval can be specified
by sending a stop marker. Marker intervals can not overlap.

Parameters
~~~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only
    letters, numbers and underscores (no punctuation marks or spaces).

Start :
    The time to send the marker to the EEG datastream

Stop Marker:
    If selected the stop marker will be sent as specified by the Stop parameter

Stop :
    Governs the duration for which the stimulus is presented. See :ref:`startStop` for details.

