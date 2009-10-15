Components
-------------------------------

Routines in the Builder contain any number of components, which typically define the parameters of a stimulus or an input/output device.

The following components are available, as at version 1.50, but further components will be added in the future including a Mouse, Parallel/Serial ports, other visual stimuli (e.g. GeometricStim) and a Custom component that will allow arbitrary code to be executed.

.. toctree::
   :maxdepth: 1   
   :glob:

   components/*

Entering parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Most of the entry boxes for Component parameters take simple text input and this will later be converted into `Python`_ code. This means that, for Component parameters where a numerical value is appropriate,a number can be typed into this box, or any other python code that generates a number. For example, to randomise the orientation of a stimulus whenever the program is run you could set the orientation to `numpy.random.rand()`_ rather than a fixed number. If you wanted to give the stimulus a random location or size, you could set these parameters to `numpy.random.rand(2)` to get two random values.

Using these features obviously requires some level of `Python`_ knowledge and users are encouraged to go through some of the basic Python the tutorials online (and probably `numpy`_ too).

.. note::

    The fact that Python code can be entered directly into the dialog boxes does have a side-effect that could catch out new users trying to enter text into boxes (e.g. for the :doc:`components/text` component). On these occasions text needs to be given quotation marks (double or single - your choice) to tell PsychoPy that it should not treat this as code, but as actual raw text to be presented. If these quotes are ommitted then PsychoPy will treat the text as a variable or other Python code and, when the experiment is run, an error will occur (either a 'Syntax error' or a 'Name error' depending on whether or not their were spaces in your text).
   
Dynamic stimuli
~~~~~~~~~~~~~~~~~
One of the powers of PsychoPy is it's ability to alter the presentation of stimuli. By default, the parameters of Components are set to be `constant`; the parameter will be set at the beginning of the experiment and will remain that way for the duration. Alternatively, most parameters can be set to change either on `every repeat` in which case the parameter will be set at the beginning of the Routine on each repeat of it. Lastly many parameters can even be set `on every frame`, allowing them to change constantly on every refresh of the screen.

.. _Python: http://www.python.org
.. _numpy.random.rand(): http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.rand.html#numpy.random.rand
.. _numpy: http://numpy.scipy.org/