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


.. _onlineSyncPavlovia:

Sync your files with Pavlovia.org
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Technically you could upload your html folder to any server but by far the easiest way to get your study running is to synchronise with Pavlovia.org. Pavlovia:

  - allows really easy to synchronize from within PsychoPy
  - is secure, using encrypted communication at all times
  - is reliable, fast and automatically backed-up
  - allows version control via `Git` (your experiment will be stored in a git repository locally and pushed/pulled with the server)

All you need to do to get your files online is press the sync button. Depending on which steps you've already completed PsychoPy will then walk you though:

  #. register/login to the Pavlovia site
  #. create a project to sync with and choose the local folder as the root of that project
  #. sync the files

    - each time you add/change files locally PsychoPy will ask you to give a title and description for that set of changes (a `git commit` in the underlying version control)
    - each time participants run online, if you're using `csv` files for storage, then the new file(s) will also be added to the repository on Pavlovia
    - when you press sync a two-way sync will occur
    - this can be used to sync easily with any other machine or collaborator

Merges and conflicts:

- if changes are made concurrently these will typically be merged by git
- if two people change the *same file* then changes will still be combined if possible (e.g. you each make a change to a different parameter in the PsychoPy experiment)
- if 2 they strictly conflict (you both change the same parameter to a different value) then a merge conflict in git will result. Currently we aren't providing a way to resolve these and you will need to find out enough about git to handle it locally

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

Note that the window won't disappear when the study finishes the way it does locally, so remember to provide a final screen that says something like "Thank you. The experiment has now finished"


.. _fetchingData:

Fetching your data
~~~~~~~~~~~~~~~~~~~~~~~

The data are saved in a data folder next to the html file. You should see csv files there that are similar to your PsychoPy standard output files. (There won't be any psydat files though - that isn't possible from JavaScript).

You could just download the data folder or, if you've set it up to sync with an OSF project then you could simply sync your PsychoPy project with OSF (from the projects menu) and your data will be fetched to your local computer! :-)

Sync with OSF
~~~~~~~~~~~~~~~~~~~~~~~

This option is on the way. It does already work from the PsychoJS perspective. We need to make sure the Builder code is correct and write the docs!
