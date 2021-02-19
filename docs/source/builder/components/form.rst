.. _formComponent:

Form Component
--------------

The Form component enables Psychopy to be used as a questionnaire tool, where
participants can be presented with a series of questions requiring responses.
Form items, defined as questions and response pairs, are presented
simultaneously onscreen with a scrollable viewing window.

Properties
~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start : int, float
    The time that the stimulus should first appear.

Stop : int, float
    Governs the duration for which the stimulus is presented.

Items : List of dicts or csv / xlsx file
    A list of dicts or csv file should have the following key, value pairs / column headers:
        *index*
            The item index as a number
        *itemText*
            The item question string
        *itemWidth*
            The question width between 0 : 1
        *type*
            The type of rating e.g., 'radio', 'rating', 'slider'
        *responseWidth*
            The question width between 0 : 1
        *options*
            A sequence of tick labels for options e.g., yes, no
        *layout*
            Response object layout e.g., 'horiz' or 'vert'
        *itemColor*
            The question text font color
        *responseColor*
            The response object color

    Missing column headers will be replaced by default entries, with the exception of `itemText` and `type`, which are required. The default entries are:
        *index*
            0 (increments for each item)
        *itemWidth*
            0.7
        *responseWidth*
            0.3
        *options*
            Yes, No
        *layout*
            horiz
        *itemColor*
            from style
        *responseColor*
            from style

Data format : menu
    Choose whether to store items data by column or row in your datafile.

randomize : bool
        Randomize order of Form elements

Appearance
==========
How should the stimulus look? Color, borders, etc.

style : light, dark
    Whether to style items in your form for a light or a dark background

border color : color
    See :ref:`colorspaces`

fill color : color
    See :ref:`colorspaces`

opacity :
    Vary the transparency, from 0.0 = invisible to 1.0 = opaque

Layout
======
How should the stimulus be laid out? Padding, margins, size, position, etc.

Size : [X,Y]
    Size of the stimulus, to be specified in 'height' units.

Pos : [X,Y]
    The position of the centre of the stimulus, to be specified in 'height' units.

Item padding : float
    Space or padding between Form elements (i.e., question and response text), to be specified in 'height' units.

Formatting
==========
Formatting text

Text height : float
    Text height of the Form elements (i.e., question and response text).

.. seealso::

	API reference for :class:`~psychopy.visual.Form`
