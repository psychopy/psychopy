.. include:: ../global.rst

.. _recruitingOnline:

Recruiting participants and connecting with online services
-------------------------------------------------------------

Having created your study in Builder, :ref:`uploaded it to Pavlovia <pavloviaUpload>`, and :ref:`activated it to run <pavloviaActivate>`, you now need to recruit your participants to run the study.

At the simplest level you can get the URL for the study and distribute it to participants manually (e.g. by email or social media). To get the URL to run you can either press the Builder button to "Run online" |pavloviaRun| and then you can select the URL in the resulting browser window that should appear.

PsychoPy can also connect to a range of other online systems as well, however, some of which are helpful in recruiting participants. Below we describe the general approach before describing the specifics for some common systems:


.. toctree::
    :maxdepth: 1

    sonaIntegration
    prolificIntegration
    mturkIntegration
    qualtricsIntegration

The general principle 
~~~~~~~~~~~~~~~~~~~~~~~

All the systems below use the same general principle to connect the different services:

#. the recruiting system needs the URL of your study to send participants there. It probably needs to add the participant ID to that URL so that your study can store that information and (potentially) send it back to the recruiting system
#. at the end of the study  the participant should be redirected back to the recruiting system so they can be credited with completing your task

Step 1. is obviously fairly easy if you know how to use the recruiting system. There will be a place somewhere in that system for you to enter the URL of the study being run. The key part is how to provide and store the participant/session ID, as described below.

Passing in a participant/session ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PsychoPy experiments bring up a dialog box at the start of the study to collect information about a run, which usually includes information about the participant. You can adjust the fields of that box in the Experiment Settings dialog box |experimentSettingsBtn| but usually there is a `participant` field (and we recommend you keep that!)

However, any variables can be passed to the experiment using the URL instead of the dialog box, and this is how you would typically pass the participant ID to your study. This is done by using "Query strings" which are a common part of online web addresses.

If your experiment has the address::

    https://run.pavlovia.org/yourUsername/yourStudyName/index.html

then this URL will run the same study but with the `participant` variable set to be `10101010`::

    https://run.pavlovia.org/yourUsername/yourStudyName/index.html?participant=10101010

and if you want two variables to be set then you can use `?` for the first and `&` for each subsequent. For instance this would set a `participant` as well as a `group` variable::

    https://run.pavlovia.org/yourUsername/yourStudyName/index.html?participant=10101010&group=A

If you want to use that variable within your study you can do so using `expInfo`. For instance you could set a thank you message with this JavaScript code in your study::

    msg = "Thanks, you're done. Your ID is " + expInfo['participant'];


Redirecting at the end of the study
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is really simple. In the Experiment Settings dialog again |experimentSettingsBtn| you can select the `Online` tab and that has a setting to provide a link for completed and failed-to-complete participants:

.. image:: /images/expSettingsURLs.png
    :scale: 50%
    :alt: Experiment Settings with completion links
