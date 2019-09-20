.. _form:

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
        *questionText*
            The item question string
        *questionWidth*
            The question width between 0 : 1
        *type*
            The type of rating e.g., 'radio', 'rating', 'slider'
        *responseWidth*
            The question width between 0 : 1
        *options*
            A sequence of tick labels for options e.g., yes, no
        *layout*
            Response object layout e.g., 'horiz' or 'vert'
        *questionColor*
            The question text font color
        *responseColor*
            The response object color

    Missing column headers will be replaced by default entries. The default entries are:
        *index*
            0 (increments for each item)
        *questionText*
            Default question
        *questionWidth*
            0.7
        *type*
            rating
        *responseWidth*
            0.3
        *options*
            Yes, No
        *layout*
            horiz
        *questionColor*
            white
        *responseColor*
            white

Text height : float
    Text height of the Form elements (i.e., question and response text).

Size : [X,Y]
    Size of the stimulus, to be specified in 'height' units.

Pos : [X,Y]
    The position of the centre of the stimulus, to be specified in 'height' units.

Item padding : float
    Space or padding between Form elements (i.e., question and response text), to be specified in 'height' units.

Data format : menu
    Choose whether to store items data by column or row in your datafile.

randomize : bool
        Randomize order of Form elements

.. seealso::

	API reference for :class:`~psychopy.visual.Form`
