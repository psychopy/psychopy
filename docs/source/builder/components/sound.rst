Sound
-------------------------------

Parameters
~~~~~~~~~~~~

name : a string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no puncuation marks or spaces).
    
startTime : float or integer
    The time (relative to the beginning of this Routine) that the stimulus will begin playing.

duration : float or integer
    The duration for which the stimulus is presented. This is only needed for sounds, such as tones, that do not have predefined durations. For sounds coming from a file, for instance, this parameter will be ignored.

sound : 
    This sound can be described in a variety of ways:
      
      * a number can specify the frequency in Hz (e.g. 440)
      * a letter gives a note name (e.g. "C") and sharp or flat can also be added (e.g. "Csh" "Bf")
      * a filename, which can be a relative or absolute path. As at version 1.51.00 only .ogg and .wav files are supported, but this is expected to be greatly increased.


.. seealso::
	
	API reference for :class:`~psychopy.sound.Sound`