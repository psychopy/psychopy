.. _unknowncomponent:

-------------------------------
Unknown Component
-------------------------------

Unknown Component is the placeholder for any Component which PsychoPy doesn't recognise (and which doesn't declare itself as coming from a plugin, as in :ref:`unknownplugincomponent`). If you see an Unknown Component, there's two most likely explanations:

* **This experiment was built in an older version of PsychoPy, and this Component has since been removed**. Usually, when we remove a Component from PsychoPy, it's either because we've moved it out to a plugin, or there's a newer Component which covers everything it does and does so in a better way. In this case, you should search online for the modern equivalent of the removed Component (try `the PsychoPy forum! <https://discourse.psychopy.org/>`_)

* **This experiment was built in a newer version of PsychoPy, and this Component wasn't added yet in your version**. This one's an easy fix, just update to the latest version! Or, at least, the version in which that Component was added. You can see what Components were added when via `PsychoPy's GitHub release notes <https://github.com/psychopy/psychopy/releases>`_.
