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

#. open a Command Prompt (terminal):
    #. go to the Windows Start menu
    #. select Run... and type in cmd <Return>
#. paste the following into that window (Ctrl-V doesn't work in Cmd.exe but you can right-click and select Paste)::

        "C:\Program Files\PsychoPy2\python.exe" -m psychopy.app.psychopyApp

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
        - go to `<location of PsychoPy app>\\Lib\\site-packages\\psychopy`
        - have a look at some of the files there
    - on Mac
        - right click the PsychoPy app and select `Show Package Contents`
        - navigate to `Contents/Resources/lib/pythonX.X/psychopy`
        
.. _cleanPrefs:

Cleaning preferences and app data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Every time you shut down PsychoPy (by normal means) your current preferences and the state of the application (the location and state of the windows) are saved to disk. If PsychoPy is crashing during startup you may need to edit those files or delete them completely. 

The exact location of those files varies by machine but on windows it will be something like `%APPDATA%\psychopy3` and on Linux/MacOS
it will be something like `~/.psychopy3`. You can find it running this in the commandline (if you have multiple Python installations then make sure you change `python` to the appropriate one for PsychoPy::

    python -c "from psychopy import prefs; print(prefs.paths['userPrefsDir'])"

Within that folder you will find `userPrefs.cfg` and `appData.cfg`.
The files are simple text, which you should be able to edit in any text editor.

If the problem is that you have a corrupt experiment file or script that is trying
and failing to load on startup, you could simply delete the `appData.cfg` file.
Please *also* :ref:`contribForum` a copy of the file that isn't working so that
the underlying cause of the problem can be investigated (google first to see if
it's a known issue).


.. _gammaRampFail:

Errors with getting/setting the Gamma ramp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two common causes for errors getting/setting gamma ramps depending on
whether you're running Windows or Linux (we haven't seen these problems
on Mac).

MS Windows bug in release 1903
`````````````````````````````````````

In Windows release 1903 Microsoft added a `bug that prevents getting/setting the gamma ramp
<https://docs.microsoft.com/en-us/windows/release-information/status-windows-10-1903#226msgdesc>`_. This only occurs in certain scenarios, like when the screen orientation is in portrait, or when it is extended onto a second monitor, but it does affect **all versions of PsychoPy**.

For the Windows bug the workarounds are as follows:

**If you don't need gamma correction** then, as of PsychoPy 3.2.4, you can go
to the preferences and set the `defaultGammaFailPolicy` to be be 'warn'
(rather than 'abort') and then your experiment will still at least run,
just without gamma correction.

**If you do need gamma correction** then there isn't much that the PsychoPy
team can do until Microsoft fixes the underlying bug. You'll need to do one
of:

- Not using Window 1903 (e.g. revert the update) until a fix is listed on the `status of the gamma bug <https://docs.microsoft.com/en-us/windows/release-information/status-windows-10-1903#226msgdesc>`_
- Altering your monitor settings in Windows (e.g. turning off extended desktop) until it works . Unfortunately that might mean you can't use dual independent displays for vision science studies until Microsoft fix it.

Linux missing xorg.conf
`````````````````````````````

On Linux some systems appear to be missing a configuration file and adding
this back in and restarting should fix things.

Create the following file  (including the folders as needed):

`/etc/X11/xorg.conf.d/20-intel.conf`

and put the following text inside (assuming you have an intel card, which
is where we've typically seen the issue crop up)::

    Section "Device"
        Identifier "Intel Graphics"
        Driver "intel"
    EndSection

For further information on the discussion of this (Linux) issue see
    https://github.com/psychopy/psychopy/issues/2061

