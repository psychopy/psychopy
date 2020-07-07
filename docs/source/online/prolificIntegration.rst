.. include:: ../global.rst

.. _prolificIntegration:

Recruiting with Prolific
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|prolific|_ is a dedicated service designed specifically for behavioural scientists. It aims to provide improved data quality over the likes of Mechanical Turk, with better participant selection and screening, and to provide more ethical pay levels to participants in your study.

As described in the page :ref:`recruitingOnline`, connecting |prolific|_ to PsychoPy is simply a matter of telling Prolific the URL for your study (including parameters to receive the Study ID etc) and then telling PsychoPy the URL to use when the participant completes the study.

Example link to provide **to Prolific** as your study URL (you will need to replace `myUserName` and `myStudyName`)::

    http://run.pavlovia.org/myUserName/myStudyName/index.html?participant={{%PROLIFIC_PID%}}&study_id={{%STUDY_ID%}}&session={{%SESSION_ID%}}


Example link to provide **to PsychoPy** as your completion URL (you will need to change your study ID number)::

    https://app.prolific.co/submissions/complete?cc=T8ZI42EG


Further details on how to find and set these links and parameters are as follows. See also `Integrating Prolific with your study <https://helpcentre.prolific.ac/hc/en-gb/sections/360001936933-Integrating-with-your-study-survey-participant-IDs-and-completion-URLs>`_


Setting the study URL in |prolific|_
----------------------------------------

To recruit participants to your PsychoPy study you should see this screen while creating/modifying your study at https://prolific.ac:

.. image:: /images/prolificSettingsOnline.png
    :scale: 40%
    :align: center
    :alt: Prolific settings for integration for PsychoPy

Note in the above that I have set the `participant`, `session` and `study_id` for our study using a URL `query string`_. These values will be populated by `Prolific Academic`_ when participants are sent to the study URL. Prolific will help you to format these correctly if you tick the `Include URL Parameters?` box which will bring up the following dialog. I've changed the default values that PsychoPy will use to store the variables (e.g. to be `participant` and `session` which are the default names for these in PsychoPy):

.. image:: /images/prolificSettingsInsertParams.png
    :scale: 50%
    :align: center
    :alt: Prolific settings (inserting parameters dialog box)

In each of the boxes in the figure above, you can see the name that Prolific gives to this value (e.g. `PROLIFIC_PID`) and the name that we want PsychoPy to use to store it (e.g. `participant`).

Setting the completion URL in PsychoPy
----------------------------------------

The last thing you need to do is copy the `Completion URL` from the main control panel above and paste that into the online tab for your PsychoPy `Experiment Settings` as below:

.. image:: /images/prolificCompletionURLexpSettings.png
    :scale: 50%
    :align: center
    :alt: The completion URL pasted into Psychoy Experiment Settings

