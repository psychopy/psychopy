.. _coder:

Coder
================================================

You can learn to use the scripting interface to PsychoPy in several ways, and you should probably follow a combination of them. These do not teach you about Python concepts, and you are recommended also to learn about that (`Python <http://www.python.org/>`_ has an excellent tutorial). In particular, dictionaries, lists and numpy arrays are used a great deal in most PsychoPy experiments:

	- :ref:`concepts`: some of the logic of PsychoPy scripting
	- :ref:`tutorials`:  walk you through the development of some semi-complete experiments
	- demos: in the demos menu of Coder view. Many and varied
	- use the :ref:`builder` to :ref:`compile a script <compileScript>` and see how it works
	- check the :ref:`api` for further details
	- ultimately go into PsychoPy and start examining the source code. It's just regular python!

.. note::
	
	Before you start, tell PsychoPy about your monitor(s) using the :ref:`monitorCenter`. That way you get to use units (like degrees of visual angle) that will transfer easily to other computers.

.. _concepts:

Basic Concepts
~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   :glob: 
   
   codeStimuli
   codeLogging
   code*
	
.. _tutorials:

Tutorials
~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2   
   :glob: 
   
   tutor*
   