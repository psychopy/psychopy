.. _onlineFromBuilder:

Creating online studies from Builder
-------------------------------------

PsychoPy can't export all possible experiments to PsychoJS scripts yet. "Standard" studies using images, text and keyboards will work. Studies with other stimuli, or that use code components, probably won't.

These are the steps you need to follow to get up and running online:

  - :ref:`onlineCheckSupported`
  - :ref:`onlineExpSettings`
  - :ref:`onlineExportHTML`
  - :ref:`onlineUploadServer`
  - :ref:`onlineDebugging`
  - :ref:`onlineParticipants`
  - :ref:`fetchingData`


.. _onlineCheckSupported:

Check if your study is fully supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Keep checking the :ref:`onlineStatus` to see what is supported. You might want to sign up to the `PsychoPy forum <http://discourse.psychopy.org>`_ and turn on "watching" for the `Online Studies <http://discourse.psychopy.org/c/online>`_ category to get updates. That way you'll know if we update/improve something and you'll see if other people are having issues.

.. _onlineExpSettings:

Check your experiment settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In your Experiment Settings there is an "Online" tab to control the settings.

Path: When you upload your study to Pavlovia it will expect to find an 'html' folder in the root of the repository, so you want to set this up with that in mind. By default the output path will be for a folder called html next to the experiment file. So if that is in the root of the folder you sync online then you'll be good to go! Usually you would have a folder structure something like this and :ref:`sync that entire folder with pavlovia.org <pavloviaSync>`:

.. figure:: /images/foldersStimHTML.png
  :alt: Folder structure with the experiment (`blockedTrials.psyexp`), a `stims` folder in which the stimuli are stored, some conditions files and an `html` folder containing the code for the study to run online.

.. _onlineExportHTML:

Export the HTML files
~~~~~~~~~~~~~~~~~~~~~~~~~

Once you've checked your settings you can simply go to `>File>Export HTML` from the Builder view with your experiment open.

That will generate all the necessary files (HTML and JS) that you need for your study


.. _onlineUploadServer:

Uploading files to your own server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We really don't recommend this and can only provide limited help if you go this route. If you do want to use your own server:

  - You will need some way to save the data. PsychoJS can output to either:

    - `csv` files in `../data` (i.e. a folder called `data` next to the html folder). You'll need this to have permissions so that the web server can write to it
    - a relational database

  - You should make sure your server is using https to encrypt the data you collect from your participants, in keeping with GDPR legislation
  - You will need to install the server-side script
  - You will need to adapt PsychoPy Builder's output scripts (`index.html` and the `<experimentName>.js`) so that the references to `lib/` and `lib/vendors` are pointing to valid library locations (which you will either need to create, or point to original online sources)

.. _onlineDebugging:

Debug your online experiments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is going to be trickier for now than the PsychoPy/Python scripts. The starting point is that, as in Python, you need to be able to see the error messages (if there are any) being generated. To do this your browser you can hopefully show you the javascript "console" and you can see various logging messages and error messages there. If it doesn't make any sense to you then you could try sending it to the PsychoPy forum in the `Online` category.

.. _activateRecruitment:

Activate on Pavlovia
~~~~~~~~~~~~~~~~~~~~~~~

This is needed

.. _onlineParticipants:

Recruiting participants
~~~~~~~~~~~~~~~~~~~~~~~

Once you've uploaded your folder with the correct permissions you can simply provide that as a URL/link to your prospective participants. When they go to this link they'll see the info dialog box (with the same settings as the one you use in your standard PsychoPy study locally, but a little prettier). That dialog box may show a progress bar while the resources (e.g. image files) are downloading to the local computer. When they've finished downloading the 'OK' button will be available and the participant can carry on to your study.

Alternatively you may well want to recruit participants using an online service such as `Prolific Academic`_


.. _fetchingData:

Fetching your data
~~~~~~~~~~~~~~~~~~~~~~~

The data are saved in a data folder next to the html file. You should see csv files there that are similar to your PsychoPy standard output files. (There won't be any psydat files though - that isn't possible from JavaScript).

You could just download the data folder or, if you've set it up to sync with an OSF project then you could simply sync your PsychoPy project with OSF (from the projects menu) and your data will be fetched to your local computer! :-)

