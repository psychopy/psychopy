Coder - interleave staircases
================================

Often psychophysicists using staircase procedures want to interleave multiple staircases, either with different start points, or for different conditions.

The follow script shows you how that can be done by nesting a pair of loops, one to loop through the number of trials and another to loop across the staircases. The staircases can be shuffled between trials, so that do not simply cycle.

.. note::

    Note the need to create a *copy* of the info. If you simply do `thisInfo=info` then all your staircases will end up pointing to the same object, and when you change the info in the final one, you will be changing it for all.

.. literalinclude:: interleaveStaircases.py
