.. include:: ../global.rst

.. _usingPavlovia:

Using Pavlovia.org
-----------------------------------

Pavlovia *n.* where behavior is studied

Pavlovia.org is a site created by the PsychoPy team to make it easy to:

- run studies online
- host your experiments securely and easily without knowing about server technologies
- share studies with other scientists with collaborators of publicly (and find public studies shared by others)
- raise awareness of your study
- version control your work (using Git)

Most of the main tasks you will perform with `Pavlovia`_ can be carried out either in the PsychoPy application or on the `Pavlovia`_ website. Synchronizing your files can also be done with any Git client if you prefer.

Creating an account on Pavlovia
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create and log in to your account on `Pavlovia`_, you will need an active internet connection. If you have not created your account, you can either 1) go to `Pavlovia`_ and create your account, or 2) click the login button highlighted in Figure 1, and create an account through the dialog box. Once you have an account on `Pavlovia`_, check to see that you are logged in via Builder by clicking button (4) highlighted below, in Figure 1.

.. figure:: /images/builderViewIndexed.png
    :align: center
    :alt: alternate text
    :figclass: align-center

*Figure 1*. PsychoPy 3 Builder icons for building and running online studies

.. _pavloviaUpload:

Creating projects and uploading files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creating your project repository is your first step to running your experiment from `Pavlovia`_. To create your project, first make sure that you have an internet connection and are logged in to `Pavlovia`_. Once you are logged in create your project repository by syncing your project with the server using button (1) in Figure 1.

A dialog box will appear, informing you that your .psyexp file does not belong to an existing project. Click “Create a project” if you wish to create a project, or click “Cancel” if you wish to return to your experiment in Builder. See Figure 2.

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
| **Local folder**: The (local) project path on your computer. Use the Browse button to find your local directory, if required.
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

From the “Explore” page, you can filter projects by setting the filter buttons to a) Public or Private, B) Active or Inactive, and C) sort by number of forks, name, date and number of stars. The default sorting method is Stars. You can also search for projects using the search tool using key words describing your area of interest, e.g., Stroop, or attention.

.. _pavloviaActivate:

When you have found your project, you have several options (see Figure 6).

|  1) Run your task from the `Pavlovia`_ server
|  2) Activate or deactivate your experiment
|  3) view your project code and resources on the `Pavlovia repository via Gitlab <https://www.gitlab.pavlovia.org>`_ repository.

.. figure:: /images/projThumb.png
    :align: center
    :alt: alternate text
    :figclass: align-center

*Figure 6*. Projects on `Pavlovia`_

Running your experiment on Pavlovia.org from Builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you wish to run your experiment online, in a web-browser, you have two options. You can run your experiment directly from pavlovia.org, as described above, or you can run your experiment directly from Builder. (There is also the option to send your experiment URL – more on that later in Recruitment Pools).

To run your experiment on `Pavlovia`_ via Builder, you must first ensure you have a valid internet connection, are logged in, and have created a repository for your project on `Pavlovia`_. Once you have completed these steps, simply click button (2) in the Builder frame, as shown in Figure 1 above.

Searching for experiments from Builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you wish to search for your own existing projects on `Pavlovia`_, or other users public projects, you can do this via the Builder interface. To search for a project, click button (3) on the Builder Frame in Figure 1. Following this, a search dialog will appear, see Figure 7. The search dialog presents several options that allow users to search, fork and synchronize projects.

.. figure:: /images/searchDlgAnnot.png
    :align: center
    :alt: alternate text
    :figclass: align-center

*Figure 7*. The search dialog in Builder

**To search for a project** (see Fig 7, Box A), type in search terms in the text box and click the “Search” button to find related projects on Pavlovia. Use the search filters (e.g., “My group”, “Public” etc) above the text box to filter the search output. The output of your search will be listed in the search panel below the search button, where you can select your project of interest.

**To fork and sync a project** is to take your own copy of a project from `Pavlovia`_ (*fork*) and copy a version to your local desktop or laptop computer (*sync*). To fork a project, select the local folder to download the project using the “Browse” button, and then click “Sync” when you are ready - (see Fig 7, Box B). You should now have a local copy of the project from `Pavlovia`_ ready to run in PsychoPy!

Now you can run your synced project online from `Pavlovia`_!


