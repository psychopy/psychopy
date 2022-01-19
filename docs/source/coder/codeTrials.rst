.. _codeTrials:

Handling Trials and Conditions
-------------------------------

.. _trialHandler:

TrialHandler
============

This is what underlies the random and sequential loop types in :ref:`builder`, they work using the :term:`method of constants`. The trialHandler presents a predetermined list of conditions in either a sequential or random (without replacement) order.

see :class:`~psychopy.data.TrialHandler` for more details.

TrialHandlerExt (For oddball paradigms)
=======================================

For handling trial sequences in a *non-counterbalanced design* (i.e. *oddball paradigms*, https://en.wikipedia.org/wiki/Oddball_paradigm). The oddball paradigm is very popular in EEG research.

Its functions are a superset of the class TrialHandler, and as such, can also be used for normal trial handling.

see :class:`~psychopy.data.TrialHandlerExt` for more details.

.. _stairHandler:

StairHandler
============

This generates the next trial using an :term:`adaptive staircase`. The conditions are not predetermined and are generated based on the participant's responses.

Staircases are predominately used in psychophysics to measure the discrimination and detection thresholds. However they can be used in any experiment which varies a numeric value as a result of a 2 alternative forced choice (2AFC) response.

The StairHandler systematically generates numbers based on staircase parameters. These can then be used to define a stimulus parameter e.g. spatial frequency, stimulus presentation duration. If the participant gives the incorrect response the number generated will get larger and if the participant gives the correct response the number will get smaller.

see :class:`~psychopy.data.StairHandler` for more details
