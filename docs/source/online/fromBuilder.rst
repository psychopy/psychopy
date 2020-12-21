.. _onlineFromBuilder:

Creating online studies from Builder
-------------------------------------

Export the HTML files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you've checked your settings you can either go to `>File>Export HTML` from the Builder view with your experiment open OR press 'sync' from the globe icons.

Both of these will generate all the necessary files (HTML and JS) that you need for your study, however sync will also create a project on pavlovia.org

When you sync an experiment with pavlovia.org for the first time, PsychoPy Builder asks you to specify a local folder. **Every file in the local folder will be uploaded to pavlovia, so be sure you've only got files in there that are required by your experiment.**


Activate on Pavlovia
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once your experiment is online you will see your experiment in your `Pavlovia Dashboard <https://pavlovia.org/dashboard>`_ in the Experiments tab. After clicking your experiment you can set its status to "Pilotting" or "Running". Read more about the `Experiment page here <https://pavlovia.org/docs/experiments/experiment-page>`_.



Fetching your data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The data are saved in a data folder next to the html file. You should see csv files there that are similar to your PsychoPy standard output files. There won't be any psydat files though. You could just download the data folder or, if you've set it up to sync with an OSF project then you could simply sync your PsychoPy project with OSF (from the projects menu) and your data will be fetched to your local computer! :-)

Alternatively, you can specify storing the data into a database. You can specify so via the experiment page and later download the data as a ZIP file.

