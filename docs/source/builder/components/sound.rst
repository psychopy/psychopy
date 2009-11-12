Sound
-------------------------------

Parameters
~~~~~~~~~~~~

name : a string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no puncuation marks or spaces).

sound : 
    This sound can be described in a variety of ways:
      
      * a number can specify the frequency in Hz (e.g. 440)
      * a letter gives a note name (e.g. "C") and sharp or flat can also be added (e.g. "Csh" "Bf")
      * a filename, which can be a relative or absolute path. As at version 1.51.00 only .ogg and .wav files are supported, but this is expected to be greatly increased.

Times : [start, stop]
    A list of times (in secs) defining the start and stop times of the component. e.g. [0.5,2.0] will cause the sound to be played starting at 0.5s. For sounds from filenames, the end time is only used to show a useful endpoint on the Routine view; it will not cause the sound to end prematurely nor to repeat if the sound has ended.

.. seealso::
	
	API reference for :class:`~psychopy.sound.Sound`