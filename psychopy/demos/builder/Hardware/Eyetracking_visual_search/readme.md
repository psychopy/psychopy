# Eyetracking: Visual Search

This experiment shows how you can use the eyetracking components in Builder to create a commonly used visual search paradigm. 

### Calibration

First the experiment runs a Calibration routine - this is a "standalone routine", so like a routine it sits directly in the experiment flow, but rather than containing components like other routines, it has parameters of its own like a component would.

### Instructions

Participants are then presented with an instructions screen, which they can dismiss by looking at a button for longer than 500ms. This means they can progress the experiment hands free!

From here on in, a Polygon component is included whose `pos` is equal to the participant's eye position, meaning it functions as a "gaze cursor"

### Fixation & Trial

Before each trial, a fixation point is then presented in the centre of the screen, until participants have fixated on it for more than 1000ms. This ensures that their eyes always start in the same position.

The trials themselves consist of between 0 and 7 distractors around a target - in some conditions, the target will be red and the distractors black, in others, the reverse. Each trial ends when participants look at the target for longer than 300ms.
