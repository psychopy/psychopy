.. include:: ../global.rst

.. _onlineFromBuilder:

Creating online experiments from Builder
-------------------------------------

Export the HTML files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To generate an online experiment you can either go to `>File>Export HTML` from the Builder view with your experiment open OR press 'sync' from the globe icons (see Figure 1, button 2).

Both of these will generate all the necessary files (HTML and JS) that you need for your study, however sync will also create a project on pavlovia.org

.. figure:: /images/builderViewIndexed.png
    :align: center
    :alt: alternate text
    :figclass: align-center
*Figure 1*. Buttons for running an online study from the PsychoPy Builder.

Synchronizing for the first time
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The first time you sync your experiment, a dialog box will appear. The dialog box informs you that your .psyexp file does not belong to an existing project. Click “Create a project” if you wish to create a project, or click “Cancel” if you wish to return to your experiment in Builder. See Figure 2.

.. figure:: /images/createProjDlg.png
    :align: center
    :alt: alternate text
    :figclass: align-center

*Figure 2*. The dialog that appears when an online project does not exist.

If you clicked the “Create a project” button, another window will appear. This window is designed to collect important metadata about your project, see Figure 3 below.

.. figure:: /images/projDlg.png
    :align: center
    :alt: alternate text
    :figclass: align-center

*Figure 3*. Dialog for creating your project on Pavlovia.org

Use this window to add information to store your project on Pavlovia:

| **Name**: This is the name of your project on Pavlovia
| **Group/Owner**: The user or group to upload the project
| **Local folder**: The (local) project path on your computer. Use the Browse button to find your local directory, if required. **Every file in the local folder will be uploaded to pavlovia, so be sure you've only got files in there that are required by your experiment.**
| **Description**: Describe your experiment – similar to the readme files used for describing PsychoPy experiments.
| **Tags (comma separated)**: The tag will be used to filter and search for experiments by key words.
| **Public**: Tick this box if you would like to make your repository public, for anyone to see.

When you have completed all fields in the Project window, click “Create project on Pavlovia” button to push your experiment up to the online repository. Click “Cancel” if you wish to return to your experiment in Builder.

Viewing your experiment files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
After you have uploaded your project to `Pavlovia`_ via Builder, you can go and have a look at your project online. To view your project, go to `Pavlovia`_. From the `Pavlovia`_ home page, you can explore your own existing projects, or other users public projects that have been made available to all users. To find your study, click the Explore tab on the home page (see Figure 4)

.. figure:: /images/pavlovHome.png
    :align: center
    :alt: alternate text
    :figclass: align-center

*Figure 4*. The `Pavlovia`_ home page

When exploring studies online, you are presented with a series of thumbnail images for all of the projects on `Pavlovia`_. See Figure 5.

.. figure:: /images/explorePav.png
    :align: center
    :alt: alternate text
    :figclass: align-center

*Figure 5*. Exploring projects on `Pavlovia`_

When you have found your project, you have several options (see Figure 6).

|  1) Run your task from the `Pavlovia`_ server
|  2) Activate or deactivate your experiment
|  3) view your project code and resources on the `Pavlovia repository via Gitlab <https://www.gitlab.pavlovia.org>`_ repository.

.. figure:: /images/projThumb.png
    :align: center
    :alt: alternate text
    :figclass: align-center

*Figure 6*. Projects on `Pavlovia`_

Once your experiment is online you will see your experiment in your `Pavlovia Dashboard <https://pavlovia.org/dashboard>`_ in the Experiments tab. After clicking your experiment you can set its status to "Pilotting" or "Running". Read more about the `Experiment page here <https://pavlovia.org/docs/experiments/experiment-page>`_.

Running your experiment on Pavlovia.org from Builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you wish to run your experiment online, in a web-browser, you have two options. You can run your experiment directly from pavlovia.org, as described above, or you can run your experiment directly from Builder. (There is also the option to send your experiment URL – more on that later in Recruitment Pools).

To run your experiment on `Pavlovia`_ via Builder, you must first ensure you have a valid internet connection, are logged in, and have created a repository for your project on `Pavlovia`_. Once you have completed these steps, simply click button 1 in Figure 1.


Fetching your data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The data are saved in a data folder next to the html file. You should see csv files there that are similar to your PsychoPy standard output files. There won't be any psydat files though. You could just download the data folder or, if you've set it up to sync with an OSF project then you could simply sync your PsychoPy project with OSF (from the projects menu) and your data will be fetched to your local computer! :-)

Alternatively, you can specify storing the data into a database. You can specify so via the experiment page and later download the data as a ZIP file.

