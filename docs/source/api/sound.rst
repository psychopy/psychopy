:mod:`psychopy.sound` - play various forms of sound
==============================================================================

.. module:: psychopy.sound

:class:`Sound`
-------------------
PsychoPy currently supports a choice of two sound libraries: pyo, or pygame. Select which will be
used via the :ref:`audioLib<generalSettings>` preference. `sound.Sound()` will then refer to either
`SoundPyo` or `SoundPygame`. This can be set on a per-experiment basis by importing
preferences, and :doc:`setting the audioLib option</api/preferences>` to use.

It is important to use `sound.Sound()` in order for proper initialization of the
relevant sound library. Do not use `sound.SoundPyo` or `sound.SoundPygame` directly.
Because they offer slightly different features, the differences between pyo and
pygame sounds are described here. Pygame sound is more thoroughly tested, whereas
pyo offers lower latency and more features.

.. autoclass:: psychopy.sound.SoundPyo
    :members:

.. autoclass:: psychopy.sound.SoundPygame
    :members:
