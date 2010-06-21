.. _timing:

Timing Issues and synchronisation
==================================

Many people ask about how precisely PsychoPy can time stimulus presentation and response recording. While For many scientific experiments precise timing is critical. some software and hardware manufacturers make this sound like a simple question, listing millisecond precision as a feature of their products, it is not actually so simple. This page considers some of 

The main timing implications come from the fact that PsychoPy uses OpenGL and does so in in double-buffered mode (usually synchronised to the vertical blank of the screen). Since nearly all modern stimulus display methods share these features, much of the information below is relevant to other software products.

Contents:

.. toctree::
   :maxdepth: 2
   
   millisecondPrecision
   detectingFrameDrops
   reducingFrameDrops
   timingMechanisms
   synchronisingInfMRI
   synchronisingInEEG
