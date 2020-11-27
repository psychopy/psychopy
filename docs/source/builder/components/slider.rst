.. _slider:

Slider Component
________________

A slider uses mouse input to collect ratings, either on a continuous scale or Likert scale (1-to-7).

Properties
~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

Stop :
    The duration for which the stimulus is presented. See :ref:`startStop` for details.

Size : (width, height)
    The size controls the width and height of the slider.
    The slider is oriented horizontally when the width is greater than the height,
    and oriented vertically otherwise. Default is (1.0, 0.1)

Position : (X,Y)
    The position of the centre of the stimulus, in the units specified by the stimulus or window. Default is centered left-right, and somewhat lower than the vertical center (0, -0.4).

Ticks : (list or tuple of integers)
    The ticks that will be place on the slider scale. The first and last ticks will be placed
    on the ends of the slider, and the remaining are spaced between the endpoints corresponding
    to their values. For example, (1, 2, 3, 4, 5) will create 5 evenly spaced ticks.
    (1, 3, 5) will create three ticks, one at each end and one in the middle.

Labels : (list or tuple of strings)
    The text to go with each tick (or spaced evenly across the ticks).
    If you give 3 labels but 5 tick locations then the end and middle ticks
    will be given labels. If the labels can’t be distributed across the ticks
    then an error will be raised. If you want an uneven distribution you should
    include a list matching the length of ticks but with some values set to None.

Granularity :
    Specifies step size for rating. 0 corresponds to a continuous scale,
    1 corresponds to an integer or discrete scale.

Force end of Routine :
    If checked, when the subject makes a rating the routine will be ended.

Opacity : value from 0 to 1
    If opacity is reduced then the underlying images/stimuli will show through.

Units :
    See :doc:`../../general/units`.

Appearance
++++++++++

Font :
    Font for labels.

Flip :
    By default labels are below the scale or left of the scale.
    By checking this checkbox, the labels are placed above the scale or to the right of the scale.

Color :
    Color of the line, ticks, and labels. See :ref:`colorspaces`.

Styles :
   A selection of pre-defined styles. Multiple styles can be selected.

.. seealso::

    API reference for :class:`~psychopy.visual.Slider`
