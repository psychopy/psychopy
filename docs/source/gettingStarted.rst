Getting Started
=====================================

PsychoPy has three main components; the application :doc:`Coder <coder/coder>` view, the :doc:`Builder <builder/builder>` view and an underlying :doc:`API <api/api>` programming library. These can be used in various ways depending on the user's preference and experience:

#. :doc:`Builder view <builder/builder>`. For those that prefer not to program, and for those new to Python, you can generate a wide range of experiments easily from the Builder. This has an intuitive, graphical user interface (GUI). You can always export your experiment to a script for fine-tuning, and this might be an ideal way for experienced programmers to learn the syntax of `python`_
	
#. :doc:`Coder view <coder/coder>` For those comfortable with programming, but maybe inexperienced with Python, the Coder view is ideal. This is a relative basic editor but does support syntax highlighting and code folding etc... It also has a demo menu where you can checkout a wide variety of PsychoPy scripts to get you started.
	
#. :doc:`The API <api/api>` Experienced python programmers can simply import the libraries and use like any other package (the :doc:`Coder <coder/coder>` tutorials and demos should help get you going and the :doc:`API reference <api/api>` will give you the details). 

.. _python : http://www.python.org

The Builder and Coder views are both components of the PsychoPy app. If you've installed the standalone version of PsychoPy on MS Windows then there should be an obvious link to PsychoPy in your >Start>Programs. If you installed the standalone version on OS X then the app is where you dragged it (!). On these two platforms you can open the Builder and Coder views from the View menu and the default view can be set from the preferences.

If the PsychoPy app is created with flags --coder (or -c), or --builder (or -b) e.g. on Linux, then the preferences will be overridden and that view will be created as the app opens.