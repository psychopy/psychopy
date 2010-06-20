.. _code:

Code
-------------------------------

The `Code Component` can be used to insert short pieces of python code into your experiments. This might be create a variable that you want for another :ref:`Component <components>`, to manipulate images before displaying them, to interact with hardware for which there isn't yet a pre-packaged component in `PsychoPy` (e.g. writing code to interact with the serial/parallel ports). See `codeUses`_ below.

Be aware that the code for each of the components in your :ref:`Routine <routines>` are executed in the order they appear on the `Routine` display (from top to bottom). If you want your `Code Component` to alter a variable to be used by another component immediately, then it needs to be above that component in the view. You may want the code not to take effect until next frame however, in which case put it at the bottom of the `Routine`. You can move `Components` up and down the `Routine` by right-clicking on their icons.

Within your code you can use other variables and modules from the script. For example, all routines have a stopwatch-style :class:`~psychopy.core.Clock` associated with them, which gets reset at the beginning of that repeat of the routine. So if you have a `Routine` called trial, there will be a :class:`~psychopy.core.Clock` called trialClock and so you can get the time (in sec) from the beginning of the trial by using::
	currentT = trialClock.getTime()

To see what other variables you might want to use, and also what terms you need to avoid in your chunks of code, compile your script before inserting the code object and take a look at the contents of that script.

Parameters
~~~~~~~~~~~~~~

The parameters of the `Code Component` simply specify the code that will get executed at 5 different points within the experiment. You can use as many or as few of these as you need for any `Code Component`:

    Begin Experiment:
        Things that need to be done just once, like importing a supporting module, initialising a variable for later use.
        
    Begin Routine:
        Certain things might need to be done just once at the start of a `Routine` e.g. at the beginning of each trial you might decide which side a stimulus will appear
        
    Each Frame:
        Things that need to updated constantly, throughout the experiment. Note that these will be exectued exactly once per video frame (on the order of every 10ms)
        
    End Routine:
        At the end of the `Routine` (eg. the trial) you may need to do additional things, like checking if the participant got the right answer
        
    End Experiment:
        Use this for things like saving data to disk, presenting a graph(?), resetting hardware to its original state etc.


.. _codeUses:

Example code uses
~~~~~~~~~~~~~~~~~~~~~~~

Set a random location for your target stimulus
-------------------------------------------------
There are many ways to do this, but you could add the following to the `Begin Routine` section of a `Code Component` at the top of your `Routine`. Then set your stimulus position to be `$targetPos` and set the correct answer field of a :ref:`keyboard` to be `$corrAns` (set both of these to update on every repeat of the Routine).::
	
	if random()>0.5:
	    targetPos=[-2.0, 0.0]#on the left
	    corrAns='left'
	else:
	    targetPos=[+2.0, 0.0]#on the right
	    corrAns='right'

Create a patch of noise 
-------------------------------------------------
To do. (but see the related `Coder` demo)

Send a feedback message at the end of the experiment
-------------------------------------------------
Create a `Code Component` with this in the `Begin Experiment` field::
	
	expClock = core.Clock()
	
and with this in the `End Experiment` field::
	
	print "Thanks for participating - that took %.2f minutes in total" %(expClock.getTime()/60.0)