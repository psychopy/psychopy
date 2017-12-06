.. _troubleshooting:

Troubleshooting
=====================================

Regrettably, PsychoPy is not bug-free. Running on all possible hardware and all platforms is a big ask. That said, a huge number of bugs have been resolved by the fact that there are literally 1000s of people using the software that have :ref:`contributed either bug reports and/or fixes <contribute>`.

Below are some of the more common problems and their workarounds, as well as advice on how to get further help.

.. _notStarting:

The application doesn't start
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may find that you try to launch the PsychoPy application, the splash screen appears and then goes away and nothing more happens. What this means is that an error has occurred during startup itself. 

Commonly, the problem is that a preferences file is somehow corrupt. To fix that see :ref:`cleanPrefs`, below. 

If resetting the preferences files doesn't help then we need to get to an error message in order to work out why the application isn't starting. The way to get that message depends on the platform (see below).

*Windows users* (starting from the Command Prompt):
    
    #. Did you get an error message that "This application failed to start because the application configuration is incorrect. Reinstalling the application may fix the problem"? If so that indicates you need to `update your .NET installation to SP1 <http://www.microsoft.com/download/en/details.aspx?id=33>`_ .

    #. open a DOS Command Prompt (terminal): 
        #. go to the Windows Start menu
        #. select Run... and type in cmd <Return>
    #. paste the following into that window (Ctrl-V doesn't work but you can right-click and select Paste). Replace VERSION with your version number (e.g. 1.61.03)::
    
        "C:\Program Files\PsychoPy2\python.exe" "C:\Program Files\PsychoPy2\Lib\site-packages\PsychoPy-VERSION-py2.6.egg\psychopy\app\psychopyApp.py"
    #. when you hit <return> you will hopefully get a moderately useful error message that you can :ref:`contribForum`
    
*Mac users*:   
    #. open the Console app (open spotlight and type console)
    #. if there are a huge number of messages there you might find it easiest to clear them (the brush icon) and then start PsychoPy again to generate a new set of messages

I run a Builder experiment and nothing happens
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
An error message may have appeared in a dialog box that is hidden (look to see if you have other open windows somewhere).

An error message may have been generated that was sent to output of the Coder view:
    #. go to the Coder view (from the Builder>View menu if not visible)
    #. if there is no Output panel at the bottom of the window, go to the View menu and select Output
    #. try running your experiment again and see if an error message appears in this Output view
    
    If you still don't get an error message but the application still doesn't start then manually turn off the viewing of the Output (as below) and try the above again.
    
Manually turn off the viewing of output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Very occasionally an error will occur that crashes the application *after* the application has opened the Coder Output window. In this case the error message is still not sent to the console or command prompt. 

To turn off the Output view so that error messages are sent to the command prompt/terminal on startup, open your appData.cfg file (see :ref:`cleanPrefs`), find the entry::

    [coder]
    showOutput = True
    
and set it to `showOutput = False` (note the capital 'F').

.. _useSource:

Use the source (Luke?)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PsychoPy comes with all the source code included. You may not think you're much of a programmer, but have a go at reading the code. You might find you understand more of it than you think!

To have a look at the source code do one of the following:
    - when you get an error message in the :ref:`coder` click on the hyperlinked error lines to see the relevant code
    - on Windows
        - go to `Program Files\\PsychoPy2\\Lib\\site-packages\\Psychopy`
        - have a look at some of the files there
    - on Mac
        - right click the PsychoPy app and select `Show Package Contents`
        - navigate to `Contents/Resources/lib/python2.6/psychopy`
        
.. _cleanPrefs:

Cleaning preferences and app data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Every time you shut down PsychoPy (by normal means) your current preferences and the state of the application (the location and state of the windows) are saved to disk. If PsychoPy is crashing during startup you may need to edit those files or delete them completely. 

On macOS and Linux the files are::
    
    ~/.psychopy2/appData.cfg
    ~/.psychopy2/userPrefs.cfg

On Windows they are::

    ${DOCS AND SETTINGS}\{USER}\Application Data\psychopy2\appData.cfg
    ${DOCS AND SETTINGS}\{USER}\Application Data\psychopy2\userPrefs.cfg

The files are simple text, which you should be able to edit in any text editor. Particular changes that you might need to make:

If the problem is that you have a corrupt experiment file or script that is trying and failing to load on startup, you could simply delete the `appData.cfg` file. Please *also* :ref:`contribForum` a copy of the file that isn't working so that the underlying cause of the problem can be investigated (google first to see if it's a known issue).
