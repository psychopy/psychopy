
PsychoPy is an open-source application allowing you run a wide range of
neuroscience, psychology and psychophysics experiments.

PsychoPy aims to be:

- *Easy* enough for teaching
- *Precise* enough for psychophysics
- *Flexible* enough for everything else!

To achieve these goals PsychoPy provides a unique choice of interface: use the
**Builder interface** to build rich, flexible experiments easily or use the
**Coder interface** to write extremely powerful experiments in the widely-used
*Python* programming language. The best of both worlds!

.. raw:: html

    <style> .red {color:red} </style>

.. role:: red

News
====================

**New PsychoPy paper**: Please cite this if you use PsychoPy Builder in your studies

Peirce, J. W., Gray, J. R., Simpson, S., MacAskill, M. R., Höchenberger, R.,
Sogo, H., Kastman, E., Lindeløv, J. (2019). `PsychoPy2: experiments in behavior
made easy. <https://dx.doi.org/10.3758/s13428-018-01193-y>`_ Behavior Research
Methods. 10.3758/s13428-018-01193-y

**Latest version**: 3.1.2 April 2019

Release series 3.1.x adds a :class:`~psychopy.hardware.keyboard.Keyboard`
class which is much faster (polling the USB bus directly and at a higher rate)
and supplies key durations automatically where possible (for keys that have
been released). As always, see the :ref:`changelog` for full details.

**Buy the official book!**

You can now :red:`buy the book`, `Building Experiments in PsychoPy
<https://uk.sagepub.com/en-gb/eur/building-experiments-in-psychopy/book253480#reviews>`_
from Sage Publishing!

300 pages of great advice on how to create better experiments with a combination
of Builder and some code snippets! Suitable for a wide range of audiences, with
separate sections for:

- beginners (suitable for undergraduate teaching)
- professionals (more technical detail for the afficionado)
- and specialists (with particular use cases like EEG, fMRI, psychophysics).

See the full :doc:`changelog`


.. title:: Home

Contents
====================

.. toctree::
   :maxdepth: 1

   All docs <documentation>
   About <about/index>
   gettingStarted
   builder/builder
   coder/coder
   api/api
   changelog
   resources/resources
   developers/developers
   troubleshooting

Please remember to :ref:`cite PsychoPy <citingPsychoPy>`

.. |TM| unicode:: U+2122
    :ltrim:
