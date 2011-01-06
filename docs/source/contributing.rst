.. _contribute:

Contributing to the project
=====================================

PsychoPy is an open-source project. It was originally written by `Jon Peirce`_ to run vision science experiments in his lab. He felt that others might find it useful and made it available by releasing it for free on the web.

Why make it free?
---------------------
It has taken thousands of hours of programming to get PsychoPy where it is today and it is provided absolutely for free. If he had chosen to make people pay for PsychoPy then he could have spent all his time working on the code and fixing bugs. Because he made it free he has to work for a living and do this in odd spare moments. The reason to make it free, the reason that open source projects can be successful, is that more people  are likely to use them, and that those people are able to contribute back to the project, because they also have all the source code.

**Please, please, please** make the effort to give a little back to this project. If you found the documentation hard to understand then think about how you would have preferred it to be written and contribute it.

.. _git:

Accessing the git repository
-----------------------------
The central location for the PsychoPy source code is now the git repository at github.com:
    http://github.com/psychopy/psychopy
    
You can browse the current files there, look at differences between commits and download the latest copy of a single file (click on the 'raw' link for a file). You can also see the diffs between 'commits' to the repository.

If you learn about how to use git, then you can create your own read-write copy within github (e.g. Jon's personal copy is http://github.com/peircej/psychopy) or take a read-only copy directly onto your own machine.

Documentation
--------------
The documentation is all written using `Sphinx`_ and the source for this is also stored in the git repository, under `docs/source`

How do I contribute changes?
-----------------------------
For simple changes, and for users that aren't so confident with things like version control systems then just email your suggested changes to the mailing list. 

If you want to make more substantial changes then discuss them on the `developers mailing list <http://groups.google.com/group/psychopy-dev>`_. 

The ideal model, for developers that know about git and may make more frequent contributions, is to create your own clone of the project on github, make changes to that and then send a pull request to have them merged back into the main repository.

.. _Jon Peirce: http://www.peirce.org.uk
.. _Sphinx: http://sphinx.pocoo.org



----------------

.. _credits:

Credits
=====================================

Developers
---------------
PsychoPy is predominantly written and maintained by `Jon Peirce`_ but has received code from a number of contributors:

    - Jeremy Gray (various aspects of code and ideas)
    - Yaroslav Halchenko (building the Debian package and a lot more)
    - Dave Britton
    - Ariel Rokem
    - Gary Strangman
    - C Luhmann

Included packages
-------------------

The PsychoPy library always includes a copy of:

    - `pyparallel <http://pyserial.sourceforge.net/pyparallel.html>`_ by Chris Liechti. Used by :ref:`psychopy.parallel <parallel>`
    - `quest.py <http://www.visionegg.org/Quest>`_ by Andrew Straw. Used by :class:`~psychopy.data.QuestHandler`

The Standalone versions also include the :ref:`suggestedPackages`

Funding
----------------

PsychoPy project has attracted small grants from the `HEA Psychology Network`_ and `Cambridge Research Systems`_

Jon is paid by `The University of Nottingham`_, and has been funded by the `BBSRC`_

.. _The University of Nottingham: http://www.nottingham.ac.uk
.. _BBSRC:  http://www.bbsrc.ac.uk
.. _University of Nottingham: http://www.nottingham.ac.uk
.. _HEA Psychology Network: http://www.psychology.heacademy.ac.uk/s.php?p=256&db=104
.. _Cambridge Research Systems: http://www.crsltd.com/