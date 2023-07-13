.. _useVersion:

How do I run experiments written with older versions of |PsychoPy|?
-------------------------------------------------------------------

If you perform experiments on computers shared by different research groups (e. g. at a shared experimental facility), it's possible that their experiments and yours are written using different versions of |PsychoPy|. Or maybe you yourself have some older and some newer experiments. In such a situation, it's important to ensure that the right version of |PsychoPy| is used for the right experiment.

In `PsychoPy standalone <https://www.psychopy.org/download.html>`_, there is an easy-to-use system for controlling what version of |PsychoPy| is used.

Version control using Builder View
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Open up the |PsychoPy| experiment file (a '.psyexp' file) that contains the experiment you want to use.
2. Go to experiment settings by clicking the icon with a cogwheel. 
3. Under the "Basic" settings tab, there is an option named "Use PsychoPy version". Set it to the PsychoPy version you want to emulate.
4. Click "OK" to save the settings. 
5. Run the experiment by clicking the green 'run' button.

Version control using Coder View
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Open up the |PsychoPy| script file (a '.py' file) that contains the experiment you want to use.
2. Add :code:`import psychopy` at the top of your script, **above** all other import statements.
3. Add the function call :code:`psychopy.useVersion('<version_no>')` directly below :code:`import psychopy`, but still **above** the other import statements. Here's an example:
::

    import psychopy
    psychopy.useVersion('2021.1.0')
    from psychopy import visual, core, event
    # the rest of your script follows

4. Run the script.

NOTE: Internet connection needed (the first time)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You need to have a working internet connection the first time that you run an experiment using a particular version (e. g. 1.90.2) on a computer, so that |PsychoPy| can download some info about the version for you. Once you've used a version once, your computer has saved the information it needs for emulating it. This means that after the first time, you don't need an internet connection if you run the same or another experiment using that version (e. g. 1.90.2).

Compatibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Using either of the above methods, you should often only need the latest version of |PsychoPy| standalone to run older experiments. However, if you have an experiment designed with a very old version of |PsychoPy| (say, version 1.77.01) you might have to install an older version of standalone |PsychoPy|. Since these things change over time, you probably want to search for help in the `PsychoPy forums <https://discourse.psychopy.org/>`_.
