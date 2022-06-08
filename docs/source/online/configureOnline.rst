.. _configureOnline:

Configure the online settings of your experiment
--------------------------------------------------

For the most part, making a study to go online is identical to making a study to run locally. However, if you are making a study to run online, you *cannot code your experiment in pure python*. This is because your experiment needs to be created in a programming language that can be interpreted by your browser, and most browsers don't understand python, they understand JavaScript. If you make your experiment in Builder view, this GUI will write both a python and JavaScript version of your experiment. So it can be run online - without needing to learn JavaScript! So, to get started, we highly recommend you familiarize yourself with the Builder components of |PsychoPy| Builder.

So, you've made your study in Builder. To run the study online you want to start by configuring your online settings, these can be accessed through Experiment Settings:

.. figure:: /images/online_tab.png
    
    The "Online" tab of Experiment settings.

This Online tab has the following parameters:

* **Output path**: Where the JavaScript version of your experiment (and accompanying html) will be written. *Recommended: leave blank*
* **Export HTML** - when will a new JavaScript file and html be exported. *Recommended - On Sync*
  * *On Sync* -  every time you sync to pavlovia.
  * *On Save* - every time you save the psyexp file. 
  * *Manually* - when you select the "compile to JS" icon.

* **Completed URL** - where will the participant be redirected once they complete the experiment? This is useful for if you are daisy chaining your experiment with recruitment websites
* **Incomplete URL** - where will the participant be redirected if they use the "esc" key to quit before the study completes.

.. note:: For completed and incomplete URLs, participants will only be redirected once their data has saved and they are presented with a green "Thank-You" message where they click "OK" - you might wish to emphasize this in your end of task instructions.

* **Additional Resources** - a list of resources used by the experiment, this can include conditions spreadsheets, images, sound files, movie files. Any resource added here will be loaded at the beginning of the study when it is loaded in the browser. It is highly recommended to add any resources that your study might need to the "Additional Resources" tab in your online settings. This can avoid "Unknown Resource" errors when running studies online. 

.. warning:: Be mindful of how many resources your experiment has. If you have very large resource files (e.g. long movies) or a large number of files (e.g. >500 images) this can result in it taking a very long time for resources to load at the beginning of your experiment. You might want to consider looking into the :ref:`resourceManager` component or the :ref:`static`.