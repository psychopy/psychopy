# Measuring detection threshold using 2AFC task with interleaved adaptive staircases

## The experiment
Measure your detection thresholds for two different spatial frequencies of grating. See notes about the staircases below. It's 160 trials long (4 staircases of 40 reps each) so it will take. Respond as quickly as you can and it will be over in about 5 mins!

## Notes
1. This has been set up to use the 'testMonitor' with units of degrees. To make this work YOU NEED TO GO TO MONITOR CENTRE and set up the dimension and distance for testMonitor. You can see in the Experiment Settings that the default units for the experiment are then set to be 'deg' (which means spatial frequency is going to be in c/deg).
2. To decide whether the stimulus appears on the left or right a Code Component called `setSide`has been used to determine which is the correct key to press and the position of the grating.
3. The fixation point goes off between trials to alert the subject that the next trial is occurring
4. Right now the experiment uses seconds for timing (for simplicity) but to be precise N frames would be better, particularly for the grating stimulus duration.
5. This experiment obviously isn't using any precise way to control contrast (like a CRS Bits# box with a CRT screen), so the estimates of your 

## The staircases
The experiment uses 4 adaptive staircases with interleaved trials. The set up of the stairs can be seen in the excel file in this folder: there a 2 spatial frequencies and for each there are two staircases, one starting at a very low contrast and another starting at a high contrast. The step size for the staircase is changing each time the staircase reverses in its direction, as determined by the stepSize column in the conditions file.
