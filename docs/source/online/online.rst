.. _online:

Running studies online
================================================

In 2016 we wrote a proof-of-principle that PsychoPy could generate studies for online use. In January 2018 we began a `Wellcome Trust <http://www.wellcome.ac.uk>`_ grant to develop it fully. This is what we call PsychoPy3 - the 3rd major phase of PsychoPy's development.

The key steps to this are basically to:

	- export your experiment to JavaScript, ready to run online
	- upload it to Pavlovia.org (or potentially your own server) to be launched
	- distribute the web address (URL) needed to run the study

Information on how to carry out those steps is below, as well as technical information regarding the precision, about how the project actually works, and about the status of the work.

Contents:

.. toctree::
:maxdepth: 1

       fromBuilder

.. toctree::
:maxdepth: 1

       status
       tech
       psychojsCode
       syncOSF
       cautions

.. _PsychoJS: https://github.com/psychopy/psychojs
.. _pavlovia: https://pavlovia.org

