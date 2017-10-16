:mod:`psychopy.sound` - play various forms of sound
==============================================================================

.. module:: psychopy.sound

:class:`Sound`
-------------------
PsychoPy currently supports a choice of three sound libraries: pyo, sounddevice or pygame. Select which will be
used via the :ref:`audioLib<generalSettings>` preference. `sound.Sound()` will then refer to one of `SoundDevice`
`SoundPyo` or `SoundPygame`. This can be set on a per-experiment basis by importing
preferences, and :doc:`setting the audioLib option</api/preferences>` to use.

 - The `pygame` backend is the oldest and should always work without errors, but has the least good performance. Use it if latencies foryour audio don't mattter.
 - The `pyo` library is, in theory, the highest performer, but in practice it has ften had issues (at least on macOS) with crashes and freezing of experiments, or causing them not to finish properly. If those issues aren't affecting your studies then this could be the one for you.
 - The `sounddevice` library looks like the way of the future. The performance appears to be good (although this might be less so in cases where you have complex rendering being done as well because it operates from the same computer core as the main experiment code). It's newer than `pyo` and so more prone to bugs and we haven't yet added microphone support to record your participants.

.. autoclass:: psychopy.sound.Sound
    :members:
