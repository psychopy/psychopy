.. _pavloviasurveyroutine:

-------------------------------
Pavlovia Survey Routine
-------------------------------

**This component is only for use with online experiments**. 

You can use Pavlovia.org to create feature rich surveys, with a range of response options, which display nicely across a range of devices (i.e. laptops, smart phones, tablets). To create and launch a Pavlovia Survey, you technically do not need the PsychoPy app at all. 

Useful links for creating surveys:

*   `Pavlovia surveys launch video <https://www.youtube.com/watch?v=1fs8CVKBPGk>`_. 
*   `Pavlovia Surveys information <https://pavlovia.org/docs/surveys/overview>`_.
*   `YouTube tutorial on how to use the Pavlovia Surveys component <https://www.youtube.com/watch?v=WMLel29z-oY>`_.

The Pavlovia Survey Routine is used to integrate a Pavlovia Survey into a behavioural task you have created in PsychoPy.

The Pavlovia Survey Routine is a "Standalone Routine", which means rather than adding a Component to an existing Routine, it will create a whole new Routine, which you can then add to your flow. Once you have selected the Routine, select Insert Routine and add it to your flow. 

.. image:: /images/PavloviaSurveyComponent.png
    :width: 60%

To specify a survey you can either use "Survey ID" or "Survey Model File".

Categories:
    Responses
Works in:
    PsychoJS

Get ID
-------------------------------

You can make a Pavlovia Survey in Pavlovia by selecting "Dashboard" and Surveys (for details see `this guide <https://pavlovia.org/docs/surveys/overview>`_). Once you have created a Survey, the survey ID will be visible in the "Overview" tab of that survey as shown below. Alternatively, you can find the Survey directly from PsychoPy by selecting "Find online..."

.. image:: /images/FindSurveyID.png
    :width: 60%

Get JSON
-------------------------------

Another way you can add a Pavlovia Survey to your experiment is by directly adding the "Survey Model File". When creating a Survey in Pavlovia you can select "Download" to download the json file used to create that Survey (you could actually share this with others and they could "Import" your json to re-use your Survey!). In PsychoPy, if you select "Survey Model File" - you will need to load the json file you've downloaded. 

.. image:: /images/FindJSON.png
    :width: 60%


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _pavloviasurveyroutine-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _pavloviasurveyroutine-surveyType:
Survey type 
    How to specify the survey.
    
    Options:
    
    * Survey id: Linking to a survey ID from Pavlovia Surveys means that the content will automatically update if that survey changes (better for dynamic use)
    
    * Survey Model File: Inserting a JSON file (exported from Pavlovia Surveys) means that the survey is embedded within this project and will not change unless you import it again (better for archiving)
    
.. _pavloviasurveyroutine-surveyId:
Survey id (*if :ref:`pavloviasurveyroutine-surveytype` is "Survey id"*)
    The ID for your survey on Pavlovia. Tip: Right click to open the survey in your browser!
    
.. _pavloviasurveyroutine-surveyJson:
Survey JSON (*if :ref:`pavloviasurveyroutine-surveytype` is "Survey Model File"*)
    File path of the JSON file used to construct the survey
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _pavloviasurveyroutine-disabled:
Disable Routine 
    Disable this Routine
    