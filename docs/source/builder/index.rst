.. _builder:

Builder
================================================

Building experiments in a GUI
------------------------------
Making your experiments using the |PsychoPy| builder is the approach that we generally recommend. Why would we (a team of programmers) recommend using a GUI?:

*   It's much faster to make experiments
*   Your experiment will be less likely to have bugs (experiments coded from scratch can very easily contain errors - even when made by the best of programmers!).
*   You can easily make an experiment to run **online in a browser**. |PsychoPy| builder view is writing you a python script "under the hood" of your experiment, but if you want to run an experiment online it can also compile a javascript version of your task using PsychoPy's sister library `PsychoJS <https://github.com/psychopy/psychojs>`_. Remember that PsychoJS is younger than |PsychoPy| - so remember to check the `status of online options <https://www.psychopy.org/online/status.html>`_ *before* making an experiment you plan to run online! The easiest way to host a study online from |PsychoPy| is through the |Pavlovia| platform, and |PsychoPy| builder has inbuilt integration to interact with this platform.

There are a number of tutorials on how to get started making experiments in builder on the `PsychoPy Youtube channel <https://www.youtube.com/user/peircej>`_ as well as several written tutorials and `Experiment Recipes <https://workshops.psychopy.org/tutorials/index.html>`_.
You can also find a range of `materials for teaching <https://workshops.psychopy.org/teaching/index.html>`_ using builder view.

.. image:: /images/builder.png
    :width: 100%
    :alt: The Builder view


**Contents:**

.. toctree::
   :maxdepth: 2
   :glob:

   concepts
   routines
   flow
   blocksCounterbalance
   components
   settings
   startStop
   outputs
   gotchas
   compileScript
   *
