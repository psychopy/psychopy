.. _coder:

Coder
================================================

The coder view is designed for those wishing to make scripts from scratch, either to make their experiments or do other things. Coder view does not teach you about Python `per se`, and you are recommended also to learn about that (`Python <http://www.python.org/>`_ has many excellent tutorials for programmers and non-programmers alike). In particular, dictionaries, lists and numpy arrays are used a great deal in most |PsychoPy| experiments.

.. only:: html

    .. image:: /images/coder_small.gif
       :alt: The Coder view

You can program |PsychoPy| experiments in any python development environment (e.g. `PyCharm <https://www.jetbrains.com/pycharm/>`_, `Spyder <https://www.spyder-ide.org/>`_ would be excellent examples of full-featured editors).
So, *why use Coder view in PsychoPy?* The answer is that the PsychoPy as a standalone package also includes several common python libraries you would use when making experiments in python.
In general there will therefore be fewer steps to take to configure your python environment in coder. So if you are teaching python, there should be less work to set up the environment for each student! *However* if you are teaching python for many purposes beyond making experiments, you might want to move to another IDE (Integrated Development Environment), because |PsychoPy| coder won't have *everything* you need imported.


You can learn to use the scripting interface to |PsychoPy| in several ways, and you should probably follow a combination of them:

- Check the content of our `PsychoPy workshops <https://workshops.psychopy.org/3days/index.html>`_ (we currently focus on coding concepts on day 3).
- :ref:`concepts`: some of the logic of |PsychoPy| scripting
- :ref:`tutorials`:  walk you through the development of some semi-complete experiments
- demos: in the demos menu of Coder view.
- use the :ref:`builder` to :ref:`compile a script <compileScript>` and see how it works (you can actually compile to Python or Javascript to learn a bit of both!). This is also useful for understanding the :ref:`code`, you can write a snippet in a code component in builder and compile to see where it is written in the script (but remember exporting to coder is a one way street, you can't make edits in coder and hope that is reflected back in the builder experiment).

.. only:: html

    .. image:: /images/compile_code.gif
       :alt: The Coder view

You should check the :ref:`api` for further details and, ultimately, go into `PsychoPy <https://github.com/psychopy/psychopy>`_ and start examining the source code. It's just regular python!

.. _concepts:

Basic Concepts
~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   :glob:

   codeStimuli
   codeLogging
   codeTrials
   globalKeys

.. _tutorials:

|PsychoPy| Tutorials
~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   :glob:

   tutor*
