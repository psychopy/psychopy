.. include:: ../global.rst

.. _online:

Running and sharing studies online
=======================================

Online studies are realized via `PsychoJS <https://github.com/psychopy/psychojs>`_; the online counterpart of |PsychoPy|. To run your study online, these are the basic steps:

* Check the :ref:`features supported by PsychoJS <onlineStatus>` to ensure the components you need will work online.
* Make your experiment in :ref:`Builder <builder>`.
* :ref:`Configure the online settings <configureOnline>` of your experiment.
* :ref:`Launch your study on Pavlovia.org <usingPavlovia>`.


.. raw:: html

    <iframe width="560" height="315" src="https://www.youtube.com/embed/oYhcBDK2O10" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

When making an experiment to run online, there are a few important considerations to make and we **highly** recommend reading through the considerations below, as they could save a lot of time in the long run!

* Using :ref:`resources <handlingOnlineResources>` in online studies.
* :ref:`Multisession testing, Counterbalancing, and multiplayer games <usingShelf>`
* :ref:`Caveats and cautions <onlineCaveats>` (timing accuracy and web-browser support).

Related links
--------------

.. toctree::
  :maxdepth: 1

  Troubleshooting Online Studies <psychoJSCodingDebugging>
  How to search for experiments of other researchers and share your own experiment <sharingExperiments>
  How to recruit participants and connect with online services <onlineParticipants>
  How to counterbalance participants across conditions <counterbalancingOnline>
  How does it work? <tech>
  Manually coding PsychoJS studies <psychojsCode>


The first generation of PsychoJS was realized by a `Wellcome Trust <https://wellcome.org/>`_ grant, awarded in January 2018.  to make online studies possible from |PsychoPy|. This is what we call PsychoPy3 - the 3rd major phase of PsychoPy's development.