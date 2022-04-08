.. _emotiv_marking:

Emotiv Marking Component
-------------------------------

The Emotiv Marking component causes Psychopy to send a marker to the EEG datastream at the
time that the stimuli are presented.

For the Emotiv Marking component to work an emotiv_recording component should have already
been added to the experiment.

By default markers with labels and values can be added.  A time interval can be specified
by sending a stop marker. If the Marker intervals overlap it is important that the labels are
unique. Additionally the length of the interval
must be greater than 0.2 seconds.  If you need higher speeds than this, it is best to
record the times of your markers manually and compare them to the times in the raw EEG data.

If you are exporting the experiment to HTML the emotiv components will have no effect in Pavlovia.
To import the experiment into Emotiv OMNI, export the experiment to HTML and follow the instructions
in the OMNI platform.

Parameters
~~~~~~~~~~~~

Name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only
    letters, numbers and underscores (no punctuation marks or spaces).

Start :
    The time to send the marker to the EEG datastream

Stop Marker:
    If selected the stop marker will be sent as specified by the Stop parameter. If no stop
    marker is sent then the marker will be an "instance" marker and will indicate a point in
    time. If a stop marker is sent the marker will be an "interval" marker and have a
    startDatetime and endDatetime associated with it.

Stop :
    Governs the duration for which the stimulus is presented. See :ref:`startStop` for details.

marker label : string
    The label assigned to this marker

marker value : int
    The value assigned to this marker

stop marker : bool
    Whether or not this is a stop marker.  Note: stop markers were designed for relatively
    long intervals (of the order of one second).  If you wish to mark short intervals
    it is safer to send two instance markers and label them appropriately so that you can
    create the intervals in post processing.
