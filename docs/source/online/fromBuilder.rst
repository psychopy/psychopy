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

If some critical part of your study is not yet support then get in touch. If your department has a small amount of money we may be able to put it in place for you. Gradually, with people chipping in, we'll make this thing complete (and completely amazing)! :-)

.. _onlineExpSettings:

Check your experiment settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In your Experiment Settings there is an "Online" tab to control the settings.

**Output path** is the location the files will be saved to (relative to the current experiment file). You might set this to `html` to save your web files to `html` folder right next to your `psyexp` file.

**JS libs** sets whether you the necessary dependencies are packaged along with the experiment online or whether they point to a remote version. If 'packaged' this will be handled for you automatically by PsychoPy (they will be added to your output path as mentioned above) and this has the advantage that the version being used will be the same always (updates to the lib can't break your experiment). The advantage of not packaging is the opposite; the JavaScript libs will always be the most recent but that means they can change without you knowing.

**OSF user ID:** allows you to choose the username (an email address) for Open Science Framework. It needs to be a user that has logged in from this computer (see the PsychoPy `Projects` menu) and has set PsychoPy to remember their login. Otherwise data could not be synced with the project for you.

**OSF Project ID:** allows you to specify the project on OSF that the experiment should sync with.

**Email address:** this doesn't currently do anything but it will be used to send you error reports if something goes wrong.

.. _onlineExportHTML:

Export the HTML files
~~~~~~~~~~~~~~~~~~~~~~~~~

Once you've checked your settings you can simply go to `>File>Export HTML` from the Builder view with your experiment open.

This will allow you to update/check the folder that the files will be saved to (based on the settings above). When you press OK the folder will be created with a number of files inside. It should be extremely quick to do this unless you have very many stimulus files.

You will find the following inside:

  - index.html: is the main experiment file
  - resources: contains all the additional files (conditions files and stimuli etc. exactly as you had specified them)
  - server.php: this is a special file that allows the html file to "talk" to the web server to save data into your 'data' folder and push files to OSF.io if you had set that to occur. Don't worry that your email address (if set) and the 'key' to the OSF project is included in this file. Web users (e.g. participants) cannot read the contents of this file like they can read the contents of an html file. The only people with access to it are those that have direct file access to the server (e.g. your web server admin team)
  - js and php folders: if you selected "packaged" as the setting for the "JS libs" then these will also appear in this folder.

.. _onlineUploadServer:

Upload your files to a web server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For this you need access to some web server. Most departments have the ability to provide a web page so hopefully you have a local contact that can help you with this. Does the server need anything special? No, not really. It needs to support PHP but nearly all web servers do that!

You need to copy the entire folder that you created above (including the `js` and `resources` subfolders) to your web server with any name you like. For example, if I have the stroop experiment on my computer but I called the output folder `html` then I would move that entire html folder to my web server (e.g. containing www.psychopy.org) but I would rename the folder to `stroop`.

In order to save data you also need to make sure that the permissions of the folder on the server are correct. The web server user (usually called 'www') needs to have write access to the folder or it won't be able to create your data folder and the CSV files when the experiment is run. You may need to talk to your web admin team for this (and feel free to suggest some more explicit instructions for this section of the docs!)

In the future we may provide server options at psychopy.org, but we would need to charge for that and we aren't currently sure if people want/need such a service.

.. _onlineDebugging:

Debug your online experiments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is going to be trickier for now than the PsychoPy/Python scripts. The starting point is that, as in Python, you need to be able to see the error messages (if there are any) being generated. To do this your browser you can hopefully show you the javascript "console" and you can see various logging messages and error messages there. If it doesn't make any sense to you then you could try sending it to the PsychoPy forum in the `Online` category.

.. _onlineParticipants:

Getting participants
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
