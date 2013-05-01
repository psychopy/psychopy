"""
ioHub
.. file: ioHub/examples/psychopyIntegrationTest/run.py

-------------------------------------------------------------------------------

psychopyIntegrationTest
+++++++++++++++++++++++

Overview:
---------

This script demonstrates and tests the current integration points between ioHub 
and  PsychoPy. Namely:
    #. Integrated logging capabilities.
    #. Shared default time base between psychopy process and ioHub process.

The different ways to add log entries into a psychopy log file and ioHub dataStore
are demonstrated.Testing that the psychopy default time base and iohub 
process default time base are aligned is also shown.

If you would like to retrieve the log file entries that were logged to the
ioDataStore on the ioHub Process, run the saveDataStoreLog.py script
that is in the iohub/examples/dataStore folder
and select the .hdf5 file you want to save the log entries for.
 
To Run:
-------

1. Ensure you have followed the ioHub installation instructions 
   in the ioHUb documentation.
2. Open a command prompt to the directory containing this file.
3. Start the test program by running:
   python.exe run.py

"""
from psychopy import core, visual, logging
from psychopy.iohub import Computer, quickStartHubServer,EventConstants, FullScreenWindow


# When you would like to use the psychopy logging module, you create a logFile
# and, providing the log file name to use, whether you want to over-write a
# file that already exists with the same name (filemode='w'), or whether you 
# want to open an existing file of the same name and append data to it (filemode='a').
# Finally, you specify the minimum log entry level that the log file will
# record. Logging levels are identical to the default set specified by psychopy.
# 
# Custom log levels are not currrently supported by the ioHub - PsychoPy logging
# integration.
#
# See the PsychoPy documentation for more information about create LogFile's. 
logging.LogFile('./lastRun.log',filemode='w',level=logging.DEBUG)


# Create and start the ioHub Server Process, enabling the 
# the default ioHub devices: Keyboard, Mouse, Experiment, and Display.
#
# If you want to use the ioDataStore, an experiment_code and session_code
# must be provided. If you do not want to use the ioDataSTore, remove these two kwargs,
# or set them to None. 
# 
# When specifying experiment code, it should not change within runs of the same
# experiment. Session code must be unique from experiment run to experiment run
# or an error will occur and the experiment will be aborted.
#
# If you would like to use a psychopy monitor config file, provide it's name 
# in the psychopy_monitor_name kwarg, otherwise remove the arg or set it to None.
# If psychopy_monitor_name is not specified or is None, a default psychopy monitor
# config is used.
#
# All args to quickStartHubServer **must be** kwargs
#
# The function returns an instance of the ioHubClientConnection class (see docs
# for full details), but it is basically your experiment interface to the ioHub
# device and event framework.
import random
io=quickStartHubServer(experiment_code="exp_code",
                       session_code="s%d"%(random.randint(1,100000)))
        
# By default, keyboard, mouse, experiment, and display devices are created 
# by the quickStartHubServer fucntion. 
#
# If you would like other devices added, specify each my adding a kwarg to the 
# quickStartHubServer function, where the kwarg is the ioHub Device class name,
# and the kwarg value is the device configuration dictionary for the device.
#
# Any device configuration properties not specified in the device configuration 
# use the device's default value for the configuration property.  See the 
# ioHub Device and Device Event documentation for details.  
mouse=io.devices.mouse
display=io.devices.display
keyboard=io.devices.keyboard
experiment=io.devices.experiment

# Currently ioHub supports mapping event positions to a single full screen
# psychopy window. Therefore, it is most convient to create this window using
# the FullScreenWindow utility function, which returns a psychopy window using
# the configuration settings specified by the ioHub Display device that is the only
# parameter required by the fucntion. 
# If you provided a valid psychopy_monitor_name when creating the ioHub connection,
# and did not provide Display device config. settings, then the psychopy monitor
# config named psychopy_monitor_name is read and the monitor size and eye to monitor
# distance are used in the ioHub Display device.
#
# Otherwise the settings provided for the iohub Display device are used and the psychopy 
# monitor config is updated with these display settings and eye to monitor distance. 
psychoWindow =  FullScreenWindow(display)

# Hide the 'system mouse cursor' so we can display a cool gaussian mask for a mouse cursor.
mouse.setSystemCursorVisibility(False)

# Currently each stimulus created needs to have the Display's corrdinate type
# bassed to it explicitedly. (This will be fixed in a future release). The default
# coordinate type is 'pix', you can change this to one of the following supported
# corrdinate types by specifying the type you want to use in the Display config dict
# passed to quickStartHubServer.
coord_type=display.getCoordinateType()

grating = visual.PatchStim(psychoWindow, mask="circle",units=coord_type, 
                                        size=150,pos=[0,0], sf=.075)

# To add an entry to the psychopy log file you created, and **not** have it also
# sent to the ioHub and stored in the ioDataStore, then just use the psychopy
# logging module as normal, and as described in the psychopy documentation.
# i.e.
logging.log("Visual Stim Resources Created.",'DEBUG',Computer.currentSec())
# or
logging.debug("Visual Stim Resources Created take 2.",Computer.currentSec())
# or
logging.log("Visual Stim Resources Created take 3.",'DEBUG')

# To use the ioHub-PsychoPy logging integration then instead of using the logging 
# module of psychopy to create log entries, use the ioHub experiment object
# that was turned into a local variable above by using:
#
#       experiment=io.devices.experiment
#
# i.e.
experiment.log("Visual Stims Created (Logged via ioHub-PsychoPy Logging Integration).",'DEBUG',Computer.currentSec())
# or
experiment.debug("Visual Stims Created (via ioHub-PsychoPy Logging) take 2.",Computer.currentSec())
# or
experiment.log("Visual Stims Created (via ioHub-PsychoPy Logging) take 3.",'DEBUG')
# or (when using experiment.log, if no log level is gen, it defaults to DEBUG)
experiment.log("Visual Stims Created (via ioHub-PsychoPy Logging) take 4.")
# This will send an Experiment Device LogEvent to the ioHub Server, where it 
# will be stored in the ioDataStore experiment.log table.

# To have the log entry enteried into the local log file you created, you must
# explicitly tell ioHub to do so by retrieving the experiment events from ioHub.
# Like this:
experiment.getEvents()
# or like this, which gets all device events:
io.getEvents()

# If you do not ask the ioHub for the experiment events before clearing events
# from the experiment event buffer, then any LogEvents in the buffer will not be 
# saved locally to the log file. The log entries has still been saved to the
# ioDataStore however (if enabled).
#
# Note that the ioHub itself generates LogEvents, generally for debugging purposes.
# Therefore, if you would like your log file to contain an log entries created
# by the ioHub process, ensure you call experiment.getEvents() occatioanally, 
# you have not made any experiment.log calles in your script.
#
# You do not 'need' to do anything with the events returned, you just need to
# request them from the ioHub event framework. This make sense when calling
# experiment.getEvents(), since nothing will be returned to you unless you have also
# been sending Experiment MessageEvents. 
# If you use the io.getEvents() method, then *all* events from *all* monitored 
# devices are returned, so you may want to assign the result of the call to a
# variable, which will be a list of ioHub device events, if any new events 
# occurred since the last call to io.getEvents or io.clearEvents():
new_events=io.getEvents()
# new_events will almost certainly be empty here, since we just called 
# io.getEvents() in the previous line 

# An important point to note is that the ioHub event framework has two levels
# of event buffers:
# #. The Global Event Buffer: This buffer is what is accessed when 
#    io.getEvents() is called. It returns all new events the ioHub has received 
#    since the last call to io.getEvents or io.clearEvents(). Events for *all*
#    devices that are being monitored are returned, sorted in chronological order.
#    Note that the sorting is done only for events that are currently available,
#    so it is possible that the next call to io.getEvents() may return a couple
#    events at the start of the event list that may be *earlier* in time than those
#    at the end of the previous event list returned.
#
# #. Device Event Buffers: Each ioHub Device that is being monitored has a device
#    level event buffer that can be accessed if events only from a particular device
#    are wanted. For example:
keyboard.getEvents()
# returns any new Keyboard device events only, and by default clears the keyboard
# event buffer so the next time keyboard.getEvents() is called, only new keyboard
# events are returned.
#
# When io.clearEvents() is called, by default it only clears any unread events
# from the *global* event buffer. Device level event buffers are not effected. 
# if you call it as follows:
io.clearEvents('all')
# then events from both buffer levels are cleared.
#
# Similarly, when you call keyboard.getEvents(), by default only the keybaord 
# events from the keybaord event buffer are removed; keyboard events in the 
# global event buffer are not touched. the same goes for calling a device level clear:
keyboard.clearEvents()

# Draw the stim resources to the back buffer.
grating.draw()

# Tell the video card to upodate the display with the graphics just drawn. 
# This method does not return until the start of the retrace that the graphics
# update is occurring on, the time of which is returned by the method; here called
# first_flip_time. 
first_flip_time=psychoWindow.flip()

# The ioHub and PsychoPy share a common time base unless you have changed what the
# default psychopy.core or psychopy.logging time base is generated from). Therefore
# it is usually not a good idea to mess with the default timers and clocks 
# psychopy sets up.
#
# We can show that ioHub and psychopy share the same time base as follows:
current_iohub_time=Computer.currentSec()

print "First Flip Time was %.3f, Current ioHub Time is %.3f"%(first_flip_time,current_iohub_time)    
print "current_iohub_time - first_flip_time = %.3f (usec.nsec) "%((current_iohub_time-first_flip_time)*1000000)
print "The time difference is less than 50 usec (0.05 msec): ", current_iohub_time-first_flip_time < 0.00005


QUIT_EXP=False
# Loop until we get a keyboard event with the space, Enter (Return), 
# or Escape key is pressed.
while QUIT_EXP is False:

    # for each loop, update the grating phase
    # advance phase by 0.05 of a cycle
    grating.setPhase(0.05, '+')

    #draw all the stim
    grating.draw()

    # flip the psychopy window buffers, so the 
    # stim changes you just made get displayed.
    flip_time=psychoWindow.flip()
    iohub_time=Computer.getTime()

    # Send a debug LogEvent to the ioHub
    experiment.debug("Flip Completed. iohub_current-psychopy_flip time = %.3f msec.usec"%((iohub_time-flip_time)*1000.0),flip_time)
   
    # For each new keyboard char event, check if it matches one
    # of the end example keys.
    for k in keyboard.getEvents(EventConstants.KEYBOARD_PRESS):
        if k.key in [' ','RETURN','ESCAPE']:
            print 'Quit key pressed: ',k.key
            QUIT_EXP=True
    
    # Ask for experiment events from iohub so that LogEvents are saved 
    # locally as well.
    experiment.getEvents()

    # Clear all events from the iohub system so our buffers do not fill up with
    # events we may not be accessing (for example mouse events in this example)
    io.clearEvents('all')

# Experiment Exit key was been pressed, so end the experiment, closing the psychopy
# window: 
psychoWindow.close()

# Register a log message that the experiment ended.
# If using experiment.log, the time field is optional.
# If it is not provided, the current time is used.
experiment.log("Experiment End","EXP")

# Do a final ask for experiment events from iohub so that LogEvents are saved 
# locally as well. (like the one we just sent above)
experiment.getEvents()
    
# Print out the time between when the stimulus screen was first show
# to the time stamp of the key event that caused the experiment to end.  
# This illustrates that when calculating RT's, you want to use the time stamp
# of the reaction event itself, not the time that psychopy received or processed
# the event.
#
# The *accuracy* of this depends on how accurate the device events being used
# can be time stamped. Keyboard and Mouse devices have delays that are not
# known unless a specific device model has been tested, so the accuracy of these
# events timing is not great. 
#
# If the device being monitored was a high speed eye
# tracker event, then in general the event time accuracy will be very good, as the 
# event time has been adjusted for the calculated delay between the eye tracker 
# event time stamp and the time the iohub received the event. 
print "You played around with the mouse cursor for %.6f seconds."%(k.time-first_flip_time)
print ''

# As a final example of using the ioHub API, and the timing you should expect
# here we will use the io.wait method and have it pause the script execution for 
# 1.5 seconds. 
# 
# The io.wait method returns the actual amount of time that has 
# elapsed between when the method was entered and just before the method 
# returns.
# You can use this to determine of 'off' the wait period was from the 
# requested wait time. It should be sub msec in general (at least when 
# tested on Windows with an i7 CPU). Please let us know if you find differently.
requested_delay=1.5
actual_delay=io.wait(requested_delay)

print "Delay requested %.6f, actual delay %.6f, Diff: %.6f"%(requested_delay,
                                                             actual_delay,
                                                             actual_delay-requested_delay)

# Close neccessary files / objects:
#
# Be sure to shut down the ioHub Server:
io.quit()
# And the psychopy system:
core.quit()

