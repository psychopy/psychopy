.. _nonSlip:

Non-slip timing for imaging
------------------------------

For most behavioural/psychophysics studies timing is most simply controlled by setting some timer (e.g. a :class:`~psychopy.core.Clock()`) to zero and waiting until it has reached a certain value before ending the trial. We might call this a 'relative' timing method, because everything is timed from the start of the trial/epoch. In reality this will cause an overshoot of some fraction of one screen refresh period (10ms, say). For imaging (EEG/MEG/fMRI) studies adding 10ms to each trial repeatedly for 10 minutes will become a problem, however. After 100 stimulus presentations your stimulus and scanner will be de-synchronised by 1 second.

There are two ways to get around this:

 #. *Time by frames* If you are confident that you :ref:`aren't dropping frames <detectDroppedFrames>` then you could base your timing on frames instead to avoid the problem.
 
 #. *Non-slip (global) clock timing* The other way, which for imaging is probably the most sensible, is to arrange timing based on a global clock rather than on a relative timing method. At the start of each trial you add the (known) duration that the trial will last to a *global* timer and then wait until that timer reaches the necessary value. To facilitate this, the PsychoPy :class:`~psychopy.core.Clock()` was given a new `add()` method as of version 1.74.00 and a :class:`~psychopy.core.CountdownTimer()` was also added.

The non-slip method can only be used in cases where the trial is of a known duration at its start. It cannot, for example, be used if the trial ends when the subject makes a response, as would occur in most behavioural studies.
 
Non-slip timing from the Builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(new feature as of version 1.74.00)

When creating experiments in the :ref:`builder`, PsychoPy will attempt to identify whether a particular :ref:`Routine <routines>` has a known endpoint in seconds. If so then it will use non-slip timing for this Routine based on a global countdown timer called `routineTimer`. Routines that are able to use this non-slip method are shown in green in the :ref:`flow`, whereas Routines using relative timing are shown in red. So, if you are using PsychoPy for imaging studies then make sure that all the Routines within your loop of epochs are showing as green. (Typically your study will also have a Routine at the start waiting for the first scanner pulse and this will use relative timing, which is appropriate).
