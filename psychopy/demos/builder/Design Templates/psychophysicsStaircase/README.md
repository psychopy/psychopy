# Detection threshold with a staircase

## The experiment: 

This experiment presents a Gabor (a sinusoid in a Gaussian window) with an orientation of your choosing. On each trial the subject reports whether or not they saw the stimulus with the up/down cursor keys. If they did see it 3 times in a row then the stimulus reduces in contrast, if they fail to see it, the stimulus immediately increases in contrast.

## Analysing your data:

After the experiment a data/ folder will have been created for you, and it will contain an excel file with your data.

For a staircase the data file contains a number of things that could be used in the analysis; the intensity of the stimulus at each of the reversal points, the intensity on every trial and the response (correct or incorrect) on every trial too.
    
Commonly people analyse staircase data by taking the average of the last few (e.g. 4) reversal intensities. A more advanced analysis is provided as a Coder demo called JND_staircase analysis. This collapses data across all the levels presented during the run(s) and fits a psychometric curve to this
averaged data.

## Notes: 
The current value of the staircase can be found using the variable name 'level' or, equivalently, 'thisXXXX' where XXXX is the singular name of the loop (e.g. if you have a staircase loop called trials you could access thisTrial).

For this demo you can see the use of 'level' by looking at the advanced
properties>color of the gabor stimulus.
