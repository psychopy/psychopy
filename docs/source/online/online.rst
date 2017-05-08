.. _online:

Running studies online
================================================

During 2016 we've been adding the option for PsychoPy to run studies in a web browser!

For Builder users: As of v1.85.x you can go the `File` menu of PsychoPy and export your study as HTML. This will generate a folder that you can drag to a web server and point participants to that server to run your study. Data will be saved there as '.csv' files in a data folder, in the same way that PsychoPy does on your local computer.

There is now a Javascript equivalent to the PsychoPy Python library. It's called `PsychoJS`_ and, just like the PsychoPy (Python) library Builder can generate experiments for you using that library.


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
