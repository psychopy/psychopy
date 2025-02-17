.. _formcomponent:

-------------------------------
Form Component
-------------------------------

The Form component enables Psychopy to be used as a questionnaire tool, where
participants can be presented with a series of questions requiring responses.
Form items, defined as questions and response pairs, are presented
simultaneously onscreen with a scrollable viewing window.

*Note*: We have now introduced `Pavlovia Surveys <https://pavlovia.org/docs/surveys/overview>`_ which allow you to create online questionnaires. You can either use them by themselves or in conjunction with your experiments. Click here to watch our `Pavlovia Surveys Launch Webinar <https://youtu.be/1fs8CVKBPGk>`_ to find out more. 

Categories:
    Responses
Works in:
    PsychoPy, PsychoJS

**Note: Since this is still in beta, keep an eye out for bug fixes.**

Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _formcomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _formcomponent-startVal:
Start
    When the Form Component should start, see :ref:`startStop`.
    
.. _formcomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _formcomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _formcomponent-stopVal:
Stop
    When the Form Component should stop, see :ref:`startStop`.
    
.. _formcomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _formcomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _formcomponent-Items:
Items
    A csv / xlsx file **To get started, we recommend selecting the "Open/Create Icon" which will open up a template forms spreadsheet** A csv/xlsx file should have the following key, value pairs / column headers:
    *index*
        The item index as a number
    *itemText*
        The item question string
    *itemWidth*
        The question width between 0 : 1
    *type*
        The type of rating e.g., 'choice', 'rating', 'slider', 'free text'
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
    
.. _formcomponent-Randomize:
Randomize
    Do you want to randomize the order of your questions?
    
.. _formcomponent-Data Format:
Data format
    Store item data by columns, or rows
    
    Options:
    
    * columns
    
    * rows
    
Layout
===============================

How should the stimulus be laid out on screen? Padding, margins, size, position, etc.


.. _formcomponent-size:
Size [w,h]
    Size of this stimulus (either a single value or x,y pair, e.g. 2.5, [1,2] 
    
.. _formcomponent-pos:
Position [x,y]
    Position of this stimulus (e.g. [1,2] )
    
.. _formcomponent-Item Padding:
Item padding
    The padding or space between items.
    
Appearance
===============================

How should the stimulus look? Colors, borders, styles, etc.


.. _formcomponent-fillColor:
Fill color (*if :ref:`formcomponent-Style` is "Custom..."*)
    Color of the form's background
    
.. _formcomponent-borderColor:
Border color (*if :ref:`formcomponent-Style` is "Custom..."*)
    Color of the outline around the form
    
.. _formcomponent-itemColor:
Item color (*if :ref:`formcomponent-Style` is "Custom..."*)
    Base text color for questions
    
.. _formcomponent-responseColor:
Response color (*if :ref:`formcomponent-Style` is "Custom..."*)
    Base text color for responses, also sets color of lines in sliders and borders of textboxes
    
.. _formcomponent-markerColor:
Marker color (*if :ref:`formcomponent-Style` is "Custom..."*)
    Color of markers and the scrollbar
    
.. _formcomponent-Style:
Styles
    Styles determine the appearance of the form
    
    Options:
    
    * light
    
    * dark
    
    * custom...
    
.. _formcomponent-colorSpace:
Color space
    In what format (color space) have you specified the colors? See :ref:`colorspaces` for more info.
    
    Options:
    
    * rgb
    
    * dkl
    
    * lms
    
    * hsv
    
.. _formcomponent-opacity:
Opacity
    Vary the transparency, from 0.0 (invisible) to 1.0 (opaque)
    
.. _formcomponent-contrast:
Contrast
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)
    
Formatting
===============================

How should this stimulus handle text? Font, spacing, orientation, etc.


.. _formcomponent-Text Height:
Text height
    The size of the item text for Form
    
.. _formcomponent-Font:
Font
    What font should the text be displayed in? Locally, can be a font installed on your computer, saved to the "fonts" folder in your |PsychoPy| user folder, or the name of a `Google Font <https://fonts.google.com>`_. Online, can be any `web safe font <https://www.w3schools.com/cssref/css_websafe_fonts.php>`_ or a font file added to your resources list in :ref:`expSettings`.
    
Data
===============================

What information about this Component should be saved?


.. _formcomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _formcomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _formcomponent-disabled:
Disable Component
    Disable this Component
    
.. _formcomponent-validator:
Validate with...
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.

.. note::
    Top tip: Form has an attribute to check if all questions have been answered :code:`form.complete`. You could use this to make a "submit" button appear only when the form is completed!
.. seealso::

	API reference for :class:`~psychopy.visual.Form`
    