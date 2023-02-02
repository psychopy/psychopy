.. _advancedsurvey:

Pavlovia Survey
-------------------------------

**This component is only for use with online experiments**. You can now use Pavlovia.org to create feature rich surveys, with a range of response options, which display nicely across a range of devices (i.e. laptops, smart phones, tablets). To create and launch a Pavlovia Survey, you technically do not need the PsychoPy app at all. For more information on how to make and launch Pavlovia Surveys you can `watch our launch event here <https://www.youtube.com/watch?v=1fs8CVKBPGk>`_. However, if you want to integrate a Pavlovia Survey within an experiment (e.g. to show a survey several times in a loop or before/after your task without the need for daisy chaining), you can do so using the Pavlovia Survey component.

The Pavlovia Survey component is a "Standalone Routine", which means rather than adding a component to an existing Routine, it will create a whole new Routine, which you can then add to your flow.  Once you have selected the component, select Insert Routine and add it to your flow. 

.. image:: /images/PavloviaSurveyComponent.png
    :width: 60%

To specify a survey you can either use "Survey ID" or "Survey Model File".

Get ID
~~~~~~~~~~

You can make a Pavlovia Survey in Pavlovia by selecting "Dashboard" and Surveys (for details see `this guide <https://pavlovia.org/docs/surveys/overview>`_). Once you have created a Survey, the survey ID will be visible in the "Overview" tab of that survey as shown below. Alternatively, you can find the Survey directly from PsychoPy by selecting "Find online..."

.. image:: /images/FindSurveyID.png
    :width: 60%

Get JSON
~~~~~~~~~~

Another way you can add a Pavlovia Survey to your experiment is by directly adding the "Survey Model File". When creating a Survey in Pavlovia you can select "Download" to download the json file used to create that Survey (you could actually share this with others and they could "Import" your json to re-use your Survey!). In PsychoPy, if you select "Survey Model File" - you will need to load the json file you've downloaded. 

.. image:: /images/FindJSON.png
    :width: 60%


Basic
======

name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
survey type : Survey ID or Survey Model File
    See above for how to specify.

