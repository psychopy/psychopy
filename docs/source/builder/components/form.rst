.. _formComponent:

Form Component
--------------

*Please note that this component is still in Beta mode and is therefore developing*

The Form component enables Psychopy to be used as a questionnaire tool, where
participants can be presented with a series of questions requiring responses.
Form items, defined as questions and response pairs, are presented
simultaneously onscreen with a scrollable viewing window.

Properties
~~~~~~~~~~

Name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start : int, float
    The time that the stimulus should first appear.

Stop : int, float
    Governs the duration for which the stimulus is presented.

Items : A csv / xlsx file **To get started, we recommend selecting the "Open/Create Icon" which will open up a template forms spreadsheet** A csv/xlsx file should have the following key, value pairs / column headers:
    *index*
        The item index as a number
    *itemText*
        The item question string
    *itemWidth*
        The question width between 0 : 1
    *type*
        The type of rating e.g., 'choice', 'rating', 'slider', 'free-text'
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
    *granularity*
        If you are using a slider, what do you want the granularity of the slider to be?

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

Layout
======
How should the stimulus be laid out? Padding, margins, size, position, etc.

Size : [X,Y]
    Size of the stimulus, to be specified in 'height' units.

Pos : [X,Y]
    The position of the centre of the stimulus, to be specified in 'height' units.

Item padding : float
    Space or padding between Form elements (i.e., question and response text), to be specified in 'height' units.

Appearance
==========
How should the stimulus look? Color, borders, etc. Many of these read-only parameters become editable when *Styles* is set to *custom*.

style : light, dark
    Whether to style items in your form for a light or a dark background

border color : color
    See :ref:`colorspaces`

fill color : color
    See :ref:`colorspaces`

opacity :
    Vary the transparency, from 0.0 = invisible to 1.0 = opaque

Formatting
==========
Formatting text

Text height : float
    Text height of the Form elements (i.e., question and response text).

Font
    Font to use in text.

.. note::
    Top tip: Form has an attribute to check if all questions have been answered :code:`form.complete`. You could use this to make a "submit" button appear only when the form is completed!
.. seealso::

	API reference for :class:`~psychopy.visual.Form`
