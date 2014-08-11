.. _components:

Components
-------------------------------

Routines in the Builder contain any number of components, which typically define the parameters of a stimulus or an input/output device.

The following components are available, as at version 1.65, but further components will be added in the future including Parallel/Serial ports and other visual stimuli (e.g. GeometricStim).

.. toctree::
   :maxdepth: 1   
   :glob:

   components/*

Entering parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most of the entry boxes for Component parameters simply receive text or numeric values or lists (sequences of values surrounded by square brackets) as input. In addition, the user can insert variables and code into most of these, which will be interpreted either at the beginning of the experiment or at regular intervals within it.

To indicate to PsychoPy that the value represents a variable or python code, rather than literal text, it should be preceded by a `$`. For example, inserting `intensity` into the text field of the Text Component will cause that word literally to be presented, whereas `$intensity` will cause python to search for the variable called intensity in the script.

Variables associated with :ref:`loops` can also be entered in this way (see :ref:`accessingParams` for further details). But it can also be used to evaluate arbitrary python code. 

For example:

    * $random(2)
        will generate a pair of random numbers

    * $"yn"[randint(2)]
        will randomly choose the first or second character (y or n)

    *  $globalClock.getTime()
        will insert the current time in secs of the globalClock object

    *  $[sin(angle), cos(angle)]
        will insert the sin and cos of an angle (e.g. into the x,y coords of a stimulus)


How often to evaluate the variable/code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you do want the parameters of a stimulus to be evaluated by code in this way you need also to decide how often it should be updated. By default, the parameters of Components are set to be `constant`; the parameter will be set at the beginning of the experiment and will remain that way for the duration. Alternatively, they can be set to change either on `every repeat` in which case the parameter will be set at the beginning of the Routine on each repeat of it. Lastly many parameters can even be set `on every frame`, allowing them to change constantly on every refresh of the screen.

.. _Python: http://www.python.org
.. _numpy.random.rand(): http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.rand.html#numpy.random.rand
.. _numpy: http://numpy.scipy.org/
