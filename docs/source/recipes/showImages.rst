.. _showImages:

Coder - show images
================================

Sometimes we want to use PsychoPy to show images --- either read from an image file (such as `.png`) or from a Numpy array. We can use either the :class:`psychopy.visual.ImageStim` or :class:`psychopy.visual.GratingStim` to achieve this. However, some of the nuances of actually getting the correct image to screen can be difficult to figure out.

This recipe demonstrates (1) a way to use :class:`psychopy.visual.ImageStim` to read an image from disc and show it, and (2) using :class:`psychopy.visual.ImageStim` to show a numpy array as an image.

When showing and converting images, you need to be careful about data types and channels. The `scikit-image docs on this <https://scikit-image.org/docs/stable/user_guide/data_types.html>`_ are quite good.

.. literalinclude:: showImages.py
