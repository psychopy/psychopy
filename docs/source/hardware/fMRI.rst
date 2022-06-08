.. _fmri:

Communicating with fMRI
=================================================

Due to the haemodynamic response being comparatively sluggish relative to scalp voltage changes, fMRI studies don't typically require sub-millisecond timing precision *within* a trial like EEG studies do.

However it **is** important that an fMRI study has consistent timing *across* trials so that the scanner sequence remains in sync with an experiment.

Step one: Know your Scanner!
-------------------------------------------------------------

Rather than programming your PsychoPy experiment to send triggers *to* some hardware in the same way as EEG, with fMRI you would want to set up your experiment so that it waits until it has detected when the scanner has sent out a trigger before moving on to present trials.

Before doing anything else, it's important that you know **how** the scanner you'll be using will emit these triggers, and whether these are converted to some other signal such as characters on a serial port or a simulated keypress. In general, there are at least 3 ways a scanner might send a trigger to your experiment:

1. Emmulate a keypress.
2. Via parallel port
3. Via serial port


Step two: Create a Routine to wait for scanner triggers
-------------------------------------------------------------

A Routine to detect fMRI triggers is really simple to set up. Regardless of the method your scanner uses to send the triggers, you'll just need a Routine that waits until it's detected the trigger before moving on. Create a new Routine and insert a Text component that says 'Waiting for Scanner'.

* **If your scanner emulates key presses:** *This is the simplest of all communication methods!*
    * Insert a Keyboard component to your 'Waiting for Scanner' Routine. In 'allowed keys' use the key that the scanner will send e.g. if the scanner sends '5' allowed keys will be '5'.
    * Now, when the keypress is detected, the 'Waiting for Scanner' screen will end. Although, be careful! PsychoPy doesn't know the difference between the emulated key presses sent from the scanner and key presses made by a human being! So take care not to type on the keyboard connected to the PsychoPy computer whilst your experiment runs to avoid your key presses being mistaken for triggers.

* **If your scanner communicates via a Parallel Port:**
    * Insert a code component to your 'Waiting for Scanner' Routine
    * In the `Begin Experiment` tab of the code component, add the following code to set up the Parallel Port::

        from psychopy.hardware.parallel import ParallelPort
        triggers = ParallelPort(address = 0x0378) #Change this address to match the address of the Parallel Port that the device is connected to
        pinNumber = 4 #Change to match the pin that is receiving the pulse value sent by your scanner. Set this to None to scan all pins

    * In the `Each Frame` tab of the same code component, add the following code to check for triggers::

        if frameN > 1: #To allow the 'Waiting for Scanner' screen to display
            trig = triggers.waitTriggers(triggers = [pinNumber], direction = 1, maxWait = 30)
            if trig is not None:
                continueRoutine = False #A trigger was detected, so move on

    * The 'Waiting for Scanner' message will now remain on the screen until the trigger is received from the scanner.

* **If your scanner communicates via a Serial Port:**
    * Insert a code component to your 'Waiting for Scanner' Routine
    * In the `Begin Experiment` tab of the code component, add the following code to set up the Serial Port::

        from psychopy.hardware.serial import SerialPort
        triggers = SerialPort('COM3', baudrate = 9600) #Change to match the address of your Serial Port
        trigger = '1' #Change to match the expected character sent from your scanner, or set to None for any character

    * In the `Each Frame` tab of the same code component, add the following code to check for triggers::

        if thisTrigger in self.read(self.inWaiting()):
            continueRoutine = False #Our trigger was detected, so move on

    * The 'Waiting for Scanner' message will now remain on the screen until the trigger is received from the scanner.


Timing in fMRI
-------------------------------------------------------------

In fMRI studies, it's important that the scanner runs remain in sync with the experiment, especially if you are only waiting for the scanner to send a trigger once at the start of the experiment.

PsychoPy implements a feature called non-slip timing to help with this (you can find out more about what this is and why it's important `here <https://www.psychopy.org/general/timing/nonSlipTiming.html>`_.

If you set your trial Routines to have a definite end-point (e.g. all components within a trial Routine will end after 5 seconds), you'll notice that the colour of the Routine in your Flow changes from blue to green. This is your indication that the Routine is making use of non-slip timing.

If you can't set your Routines to have a fixed duration (for example if a trial ends when a participant makes a response), it's a good idea to insert a 'Waiting for Scanner' Routine at the start of every trial so that you know that each trial has been synced with your scanner's trigger.


If there is a problem - We want to know!
-------------------------------------------------------------
If you have followed the steps above and are having an issue with triggers, please post details of this on the `PsychoPy Forum <https://discourse.psychopy.org/>`_.

We are constantly looking to update our documentation so that it's easy for you to use PsychoPy in the way that you want to. Posting in our forum allows us to see what issues users are having, offer solutions, and to update our documentation to hopefully prevent those issues from occurring again!