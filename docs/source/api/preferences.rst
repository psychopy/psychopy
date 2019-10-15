.. _preferences:

:mod:`psychopy.preferences` - getting and setting preferences
=================================================================================

You can set preferences on a per-experiment basis. For example, if you would like to use a specific :doc:`audio library</api/sound>`, but don't want to touch your user settings in general, you can import preferences and set the option :ref:`audioLib<generalSettings>` accordingly::

    from psychopy import prefs
    prefs.hardware['audioLib'] = ['pyo']
    from psychopy import sound

**!!IMPORTANT!!** You must import the sound module **AFTER** setting the preferences. To check that you are getting what you want (don't do this in your actual experiment)::

    print sound.Sound

The output should be ``<class 'psychopy.sound.SoundPyo'>`` for pyo, or ``<class 'psychopy.sound.SoundPygame'>`` for pygame.

You can find the names of the preferences sections and their different options :doc:`here</general/prefs>`.

:class:`Preferences`
------------------------------------
.. automodule:: psychopy.preferences
    :members: Preferences
