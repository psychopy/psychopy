.. include:: ../global.rst

.. _launch-and-collect-data:

Launch your study and collect data
==================================

**Goal:** Make your experiment available to participants on Pavlovia and
collect data safely.

Before you start
----------------

You should already have:

- A Pavlovia project synced with your latest experiment files
- Completed testing your experiment online
- Ensure that you are covered by a Pavlovia licence or that you have credits for your Pavlovia project.  
  See the `Pavlovia store <https://pavlovia.org/store>`_ to purchase credits, and refer to the `credits and license overview <https://pavlovia.org/docs/credit-license/overview>`_ for more information.


Setting your project status and data options
--------------------------------------------

Once your experiment is ready for participants:

1. Go to your Pavlovia project page.
2. Under **Project Status**, select **Running**. This makes the experiment accessible to participants who you share the link with.

.. figure:: /images/runningModePavlovia.png
    :name: runningModePavlovia
    :align: center
    :figclass: align-center
    :scale: 50

    How to generate a url to share with participants when your Pavlovia project is in running mode.

3. Configure your **Data saving mode**. Choose the option that best fits your study needs. Note that when chosing between CSV and DATABASE formats consider a) if you want an individual file for each participant (if yes choose csv) b) if you eventually want to make your Pavlovia project public, including the data files, if yes then choose CSV mode. If you may want to share your experiment files but keep your data private choose DATABASE mode:

   - **CSV** – Saves data in CSV format, one file per participant. This is simple and easy to import into Excel or Python for analysis.
   - **DATABASE** – Saves all participants’ data in a single database file. Each row corresponds to a trial per participant, and each column corresponds to a variable. This is convenient for larger studies or repeated analysis.
   - **Save incomplete results** – Decide whether to save data from participants who do not finish the experiment.  
     **Important:** This only applies if a participant exits the experiment by pressing the Esc key twice (first press exits full-screen mode, second press exits the experiment). Unexpected browser crashes or hard closes may still result in data loss.
   - **Save periodically (License-only feature)** – Saves data periodically during the experiment instead of only at the end. This reduces the risk of losing data if a participant exits early or if a technical error occurs.

.. figure:: /images/dataOptionsPavlovia.png
    :name: dataOptionsPavlovia
    :align: center
    :figclass: align-center
    :scale: 50

    Screenshot of data saving options on Pavlovia project page.

Sharing the experiment
----------------------

Once your experiment is running, you can share it with participants in several ways:

- **Copy the experiment URL** from your Pavlovia project page and distribute it directly.
- **Preset participant IDs** when sharing with specific participants by appending query parameters to the URL. For example:

  - Single participant ID:  
    `https://run.pavlovia.org/Consultancy/docs_test/?participant=myparticipantid`
  - Participant ID with a session number:  
    `https://run.pavlovia.org/Consultancy/docs_test/?participant=myparticipantid&session=1`

- **Use external recruitment platforms**: Pavlovia is compatible with platforms that allow providing a URL to participants, including Prolific, Sona Systems, and MTurk.
- **Integrate with survey tools**: You can connect your experiment with external survey platforms such as Qualtrics or REDCap, or you can use Pavlovia’s built-in survey functionality.

Using Third-Party Recruitment Platforms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you are using a third-party recruitment platform, ensure that you follow their guidelines for integrating external experiments. Most platforms allow you to provide a URL for participants to access your experiment. Make sure to test the full workflow, including participant recruitment and data collection, before launching your study.

.. toctree::
  :maxdepth: 1

  MTurk <mturkIntegration>
  Profilic <prolificIntegration>
  Qualtrics <qualtricsIntegration>
  SONA <sonaIntegration>

Monitoring and collecting data
------------------------------

- Data from participants is automatically stored in your Pavlovia repository.
- You can download the collected data from the **Download results** button on your project page.
- To check out a single data file you can select **View Code** and see the data folder in the repository.

Best practices
--------------

- Test a small batch of participants first to ensure everything is recording correctly.
- Avoid making changes to the experiment while participants are running it online; if changes are needed, stop the study, update files, and then resume.

Next step
---------

Be familiar with the caveats and cautions of online testing:

:doc:`cautions`


