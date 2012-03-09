Scrolling text
=====================================

Question: How can I animate something to produce scrolling text (like html's <marquee behavior = "scroll" > directive)?

(copied & pasted from the email list)

PsychoPy has animation capabilities built-in (it can even produce and export movies itself (e.g. if you want to show your stimuli in presentations)). But here you just want to animate stimuli directly.

e.g. create a text stimulus.  In the 'pos' (position) field, type:

  [frameN, 0]

and select "set every frame" in the popup button next to that field.

Push the Run button and your text will move from left to right, at one pixel per screen refresh, but stay at a fixed y-coordinate.  In essence, you can enter an arbitrary formula in the position field and the stimulus will be-redrawn at a new position on each frame. frameN here refers to the number of frames shown so far, and you can extend the formula to produce what you need.

You might find performance issues (jittering motion) if you try to render a lot of text in one go, in which case you may have to switch to using images of text.

I wanted my text to scroll from right to left.  So if you keep your eyes in the middle of the screen
the next word to read would come from the right (as if you were actually reading text).  The original formula posted above scrolls the
other way.  So, you have to put a negative sign in front of the formula for it to scroll the other way.  You have to change the units to pixel.  Also, you have to make sure you have an end time set, otherwise it just flickers.  I also set my letter height to 100
pixels.  The other problem I had was that I wanted the text to start blank and scroll into the screen.  So, I wrote

  [2000-frameN, 0]

and this worked really well.
