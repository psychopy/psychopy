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

To recruit participants to your PsychoPy study you should see a screen as in :numref:`prolificSettingsOnline` while creating/modifying your study at https://prolific.co:

.. figure:: /images/prolificSettingsOnline.png
    :name: prolificSettingsOnline
    :align: center
    :figclass: align-center
    
    Prolific settings for integration for PsychoPy

Note in the above that I have set the `participant`, `session` and `study_id` for our study using a URL `query string`_. These values will be populated by |prolific|_ when participants are sent to the study URL. Prolific will help you to format these correctly if you tick the `Include URL Parameters?` box which will bring up the following dialog. I've changed the default values that PsychoPy will use to store the variables (e.g. to be `participant` and `session` which are the default names for these in PsychoPy):

.. figure:: /images/prolificSettingsInsertParams.png
    :name: prolificSettingsInsertParams
    :align: center
    :figclass: align-center

    Prolific settings (inserting parameters dialog box)

In each of the boxes in :numref:`prolificSettingsInsertParams`, you can see the name that Prolific gives to this value (e.g. `PROLIFIC_PID`) and the name that we want PsychoPy to use to store it (e.g. `participant`).

Setting the completion URL in PsychoPy
----------------------------------------

Do not show the completion code to your participants before they have completed your study. Displaying the completion code may result in data loss, since it encourages your participants to return to Prolific before they have completed your study. Instead copy the `Completion URL` from the main control panel above and paste that into the online tab for your PsychoPy `Experiment Settings` as in :numref:`prolificCompletionURLexpSettings`:

.. figure:: /images/prolificCompletionURLexpSettings.png
    :name: prolificCompletionURLexpSettings
    :align: center
    :figclass: align-center

    The completion URL pasted into Psychoy Experiment Settings
