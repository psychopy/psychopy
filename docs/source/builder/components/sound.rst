.. _sound:

Sound Component
-------------------------------

Parameters
~~~~~~~~~~~~

name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
start : float or integer
    The time that the stimulus should first play. See :ref:`startStop` for details.

stop : 
    For sounds loaded from a file leave this blank and then give the `Expected duration` below for 
    visualisation purposes. See :ref:`startStop` for details.
    
sound : 
    This sound can be described in a variety of ways:
      
      * a number can specify the frequency in Hz (e.g. 440)
      * a letter gives a note name (e.g. "C") and sharp or flat can also be added (e.g. "Csh" "Bf")
      * a filename, which can be a relative or absolute path (mid, wav, and ogg are supported).

Playback
========
How should stimulus play? Speed, volume, etc.

volume : float or integer
    The volume with which the sound should be played. It's a normalized value between 0 (minimum) 
    and 1 (maximum).

hamming window : bool
    For tones we can apply a hamming window to prevent 'clicks' that are caused by a sudden onset. 
    This delays onset by roughly 1ms.

Stop with Routine? : bool
    Should playback cease when the Routine ends? Untick to continue playing after the Routine has 
    finished.

Force end of Routine : bool
    Should the end of the sound cause the end of the Routine (e.g. trial)?

Device
========
Parameters for setting up the :class:`~psychopy.hardware.speaker.SpeakerDevice` which this sound will play on.

Speaker : str
    Choose from a dropdown list of available speaker devices which one to use.

Latency/exclusivity mode : int
    One of:
    - Shared: Don't take exclusive control over the speaker, so other apps can still use it. Send 
        sounds via the system mixer so that sample rates are all handled, even though this 
        introduces latency.
    - Shared low-latency: Don't take exclusive control over the speaker, so other apps can still use it. Send 
        sounds directly to reduce latency, so sounds will need to match the sample rate of the 
        speaker. **Recommended in most cases; if `resample` is True then sample rates are 
        already handled on load!**
    - Exclusive low-latency: Take exclusive control over the speaker, so other apps can't use it. Send sounds 
        directly to reduce latency, so sounds will need to be the same sample rate as one 
        another, but this can be any sample rate supported by the speaker.
    - Exclusive aggressive low-latency (with fallback): Take exclusive control over the speaker, so other apps can't use it. Send sounds 
        directly to reduce latency, so sounds will need to be the same sample rate as one 
        another, but this can be any sample rate supported by the speaker. Force the system to 
        prioritise resources towards playing sounds on this speaker for absolute minimum 
        latency, but fallback to mode 2 if the system rejects this.
    - Exclusive aggressive low-latency (no fallback): Take exclusive control over the speaker, so other apps can't use it. Send sounds 
        directly to reduce latency, so sounds will need to be the same sample rate as one 
        another, but this can be any sample rate supported by the speaker. Force the system to 
        prioritise resources towards playing sounds on this speaker for absolute minimum 
        latency, and raise an error if the system rejects this.
Resample : bool
    If the sample rate of an audio clip doesn't match the sample rate of the speaker, should 
    PsychoPy resample the sound on load?


.. seealso::
	
	API reference for :class:`~psychopy.sound.SoundPyo`
