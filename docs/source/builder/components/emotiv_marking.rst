.. _emotiv_marking:

Emotiv Marking Component
-------------------------------

The Emotiv Marking component causes Psychopy to send a marker to the EEG datastream at the time that the stimuli are presented.

For the Emotiv Marking component to work an Emotiv Recording component should have already been added to the experiment.

By default markers with labels and values can be added.  If an time interval can be specified by sending a stop marker. Marker intervals can not over lap as the stop marker will apply to the last sent start marker.

Parameters
~~~~~~~~~~~~

Name : string
