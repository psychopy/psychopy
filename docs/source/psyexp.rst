PsychoPy Experiment file format (.psyexp)
============================================

The file format used to save experiments constructed in PsychoPy builder was created especially for the purpose, but is an open format, using a basic xml form, that may be of use to other similar software. Indeed the builder itself could be used to generate experiments on different backends (such as Vision Egg, PsychToolbox or PyEPL). The xml format of the file makes it extremely platform independent, as well as moderately(?!) easy to read by humans. There was a further suggestion to generate an XSD (or similar) `schema against which psyexp files could be validated <https://groups.google.com/forum/?fromgroups=#!topic/psychopy-dev/j3XkZEYj_PQ>`_. That is a low priority but welcome addition if you wanted to work on it(!)
There is a basic XSD (XML Schema Definition) available in `psychopy/app/builder/experiment.xsd`.

The simplest way to understand the file format is probably simply to create an experiment, save it and open the file in an xml-aware editor/viewer (e.g. change the file extension from .psyexp to .xml and then open it in Firefox). An example (from the stroop demo) is shown below.

The file format maps fairly obviously onto the structure of experiments constructed with the :ref:`builder` interface, as described :doc:`here <builder/concepts>`. There are general :ref:`settingsXML` for the experiment, then there is a list of :ref:`routinesXML` and a :ref:`flow` that describes how these are combined. 

As with any xml file the format contains object `nodes` which can have direct properties and also child nodes. For instance the outermost node of the .psyexp file is the experiment node, with properties that specify the version of PsychoPy that was used to save the file most recently and the encoding of text within the file (ascii, unicode etc.), and with child nodes :ref:`settingsXML`, :ref:`routinesXML` and :ref:`flowXML`. 

.. _paramsXML:

Parameters
---------------------------
Many of the nodes described within this xml description of the experiment contain Param entries, representing different parameters of that Component. Nearly all parameter nodes have a `name` property and a `val` property. The parameter node with the name "advancedParams" does not have them. Most also have a `valType` property, which can take values 'bool', 'code', 'extendedCode', 'num', 'str' and an `updates` property that specifies whether this parameter is changing during the experiment and, if so, whether it changes 'every frame' (of the monitor) or 'every repeat' (of the Routine).

.. _settingsXML:

Settings
---------------------------
The Settings node contains a number of parameters that, in PsychoPy, would normally be set in the :ref:`expSettings` dialog, such as the monitor to be used. This node contains a number of :ref:`paramsXML` that map onto the entries in that dialog.

.. _routinesXML:

Routines
---------------------------

This node provides a sequence of xml child nodes, each of which describes a :ref:`Routine <routines>`. Each Routine contains a number of children, each specifying a :ref:`Component <components>`, such as a stimulus or response collecting device. In the :ref:`Builder` view, the :ref:`routines` obviously show up as different tabs in the main window and the :ref:`components` show up as tracks within that tab.

.. _componentsXML:

Components
---------------------------

Each :ref:`Component <components>` is represented in the .psyexp file as a set of parameters, corresponding to the entries in the appropriate component dialog box, that completely describe how and when the stimulus should be presented or how and when the input device should be read from. Different :ref:`Components` have slightly different nodes in the xml representation which give rise to different sets of parameters. For instance the `TextComponent` nodes has parameters such as `colour` and `font`, whereas the `KeyboardComponent` node has parameters such as `forceEndTrial` and `correctIf`.

.. _flowXML:

Flow
---------------------------

The Flow node is rather more simple. Its children simply specify objects that occur in a particular order in time. A Routine described in this flow must exist in the list of Routines, since this is where it is fully described. One Routine can occur once, more than once or not at all in the Flow. 
The other children that can occur in a Flow are LoopInitiators and LoopTerminators which specify the start and endpoints of a loop. All loops must have exactly one initiator and one terminator. 

.. _namesXML:

Names
---------

For the experiment to generate valid PsychoPy code the name parameters of all objects (Components, Loops and Routines) must be unique and contain no spaces. That is, an experiment can not have two different Routines called 'trial', nor even a Routine called 'trial' and a Loop called 'trial'.

The Parameter names belonging to each Component (or the Settings node) must be unique within that Component, but can be identical to parameters of other Components or can match the Component name themselves. A TextComponent should not, for example, have multiple 'pos' parameters, but other Components generally will, and a Routine called 'pos' would also be also permissible.

.. literalinclude:: stroop.psyexp
   :language: xml

