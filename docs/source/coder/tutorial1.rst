Tutorial 1: Generating your first stimulus
=============================================


A tutorial to get you going with your first stimulus display.

Know your monitor
------------------------
|PsychoPy| has been designed to handle your screen calibrations for you. It is also designed to operate (if possible) in the final experimental units that you like to use e.g. degrees of visual angle.

In order to do this |PsychoPy| needs to know a little about your monitor. There is a GUI to help with this (select MonitorCenter from the tools menu of |PsychoPy|IDE or run ...site-packages/monitors/MonitorCenter.py).

In the MonitorCenter window you can create a new monitor name, insert values that describe your monitor and run calibrations like gamma corrections. For now you can just stick to the [`testMonitor`] but give it correct values for your screen size in number of pixels and width in cm.

Now, when you create a window on your monitor you can give it the name 'testMonitor' and stimuli will know how they should be scaled appropriately.

Your first stimulus
------------------------

Building stimuli is extremely easy. All you need to do is create a
:class:`~psychopy.visual.Window`, then some stimuli. Draw those stimuli, then update the window. |PsychoPy| has various other useful commands to help with timing too. Here's an example. Type it into a coder window, save it somewhere and press run.

.. code-block:: python
    :linenos:

    from psychopy import visual, core  # import some libraries from PsychoPy
    from psychopy.hardware import keyboard

    #create a window
    mywin = visual.Window([800,600], monitor="testMonitor", units="deg")

    #create some stimuli
    grating = visual.GratingStim(win=mywin, mask="circle", size=3, pos=[-4,0], sf=3)
    fixation = visual.GratingStim(win=mywin, size=0.5, pos=[0,0], sf=0, rgb=-1)

    #create a keyboard component
    kb = keyboard.Keyboard()

    #draw the stimuli and update the window
    grating.draw()
    fixation.draw()
    mywin.update()

    #pause, so you get a chance to see it!
    core.wait(5.0)

.. note:: **For those new to Python.** Did you notice that the grating and the fixation stimuli both call :mod:`~psychopy.visual.GratingStim` but have different arguments? One of the nice features about python is that you can select which arguments to set. GratingStim has over 15 arguments that can be set, but the others just take on default values if they aren't needed.

That's a bit easy though. Let's make the stimulus move, at least! To do that we need to create a loop where we change the phase (or orientation, or position...) of the stimulus and then redraw. Add this code in place of the drawing code above:


.. code-block:: python

    for frameN in range(200):
        grating.setPhase(0.05, '+')  # advance phase by 0.05 of a cycle
        grating.draw()
        fixation.draw()
        mywin.update()


That ran for 200 frames (and then waited 5 seconds as well). Maybe it would be nicer to keep updating until the user hits a key instead. That's easy to add too. In the first line add :mod:`~psychopy.event` to the list of modules you'll import. Then replace the line:

.. code-block:: python

    for frameN in range(200):

with the line:

.. literalinclude:: tutorial1.py
   :lines: 15

Then, within the loop (make sure it has the same indentation as the other lines) add the lines:

.. literalinclude:: tutorial1.py
   :lines: 21-23

the first line counts how many keys have been pressed since the last frame. If more than zero are found then we break out of the never-ending loop. The second line clears the event buffer and should always be called after you've collected the events you want (otherwise it gets full of events that we don't care about like the mouse moving around etc...).

Your `finished script <https://raw.githubusercontent.com/psychopy/psychopy/master/docs/source/coder/tutorial1.py>`_ should look something like this:

.. literalinclude:: tutorial1.py
    :linenos:

There are several more simple scripts like this in the demos menu of the Coder and Builder views and many more to download. If you're feeling like something bigger then go to
:doc:`tutorial2` which will show you how to build an actual experiment.
