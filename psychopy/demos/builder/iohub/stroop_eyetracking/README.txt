Stroop - with ioHub Eye Tracking Device via Custom Code Component.
------------------------------------------------------------------

This is a lot like the original Stroop task provided in the PsychoPy demos. 

We just added a Code Component to add ioHub eye tracking features:
    1) check that fixation was maintained throughout the trial. 
    2) calculate a moving window average for pupil size
    3) During a trial, display a gaze cursor for eye position if the 'g' key is pressed.
    4) If displayed, the gaze cursor is scaled based on the latest pupil size calculation.
    
To enable the eye tracking functionality in the demo, you need to add the name of an eye-tracker config file during the experiment settings dialog. The default is for the SMI iView system. If using another eye tracker type, replace the default text with the name of the appropriate ET config yaml file.

Please edit the config file to set the display parameters and eye tracking parameters so they are valid for your setup.

