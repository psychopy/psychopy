.. _interleavedStairs:

Coder - interleave staircases
================================

Often psychophysicists using staircase procedures want to interleave multiple staircases, either with different start points, or for different conditions.

There is now a class, :class:`psychopy.data.MultiStairHandler` to allow simple access to interleaved staircases of either basic or QUEST types. That can also be used from the :ref:`loops` in the :ref:`builder`. The following method allows the same to be created in your own code, for greater options.

The method works by nesting a pair of loops, one to loop through the number of trials and another to loop across the staircases. The staircases can be shuffled between trials, so that they do not simply alternate.

.. note::

    Note the need to create a *copy* of the info. If you simply do `thisInfo=info` then all your staircases will end up pointing to the same object, and when you change the info in the final one, you will be changing it for all.

.. literalinclude:: interleaveStaircases.py
