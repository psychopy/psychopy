# Eyetracking

This demo shows off the eyetracking capabilities of Builder, thanks to the ioHub backend. By default, this demo uses `MouseGaze`, which means that you can use your mouse to simulate eye movement without having any eyetracker connected. To use a real eyetracker, go to the Eyetracking tab in Experiment Settings and choose the appropriate tracker.

The ROI component is designed to make eye-driven experiment control super easy - an ROI works much like a Polygon component, it has a size, position and vertices. However, by calling `roi.isLookedIn` you can test whether the participant is looking at this ROI, and by calling `roi.currentLookTime` you can see how long they have been looking for. ROI's are also, like Mouse or Keyboard components, able to end the routine.

In this demo, a circular ROI is positioned at random on the screen, with a Polygon component whose size, position and vertices are all the same as the ROI. If the participant looks at the ROI, the cursor (whose position is set each frame to be the current eye position) will turn green and begin a countdown. If they keep looking at it for 5s, the routine will end and the experiment will move on.