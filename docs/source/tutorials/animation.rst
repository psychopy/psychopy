Animation
=====================================

General question: How can I animate something?

Conceptually, animation just means that you vary some aspect of the stimulus over time. So the key idea is to draw something slightly different on each frame. This is how movies work, and the same principle can be used to create scrolling text, or fade-in / fade-out effects, and the like.

(copied & pasted from the email list; see the list for people's names and a working script.)

Scrolling text
=====================================

Key idea: Vary the **position** of the stimulus across frames.

Question: How can I produce scrolling text (like html's <marquee behavior = "scroll" > directive)?

Answer: PsychoPy has animation capabilities built-in (it can even produce and export movies itself (e.g. if you want to show your stimuli in presentations)). But here you just want to animate stimuli directly.

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


Fade-in / fade-out effects
=====================================

Key idea: vary the **opacity** of the stimulus over frames.

Question: I'd like to present an image with the image appearing progressively and disappearing progressively too. How to do that?

Answer: The Patch stimulus has an opacity field.  Set the button next to it to be "set every frame" so that its value can be changed progressively, and enter an equation in the box that does what you want.

e.g. if your screen refresh rate is 60 Hz, then entering:

  frameN/120

would cycle the opacity linearly from 0 to 1.0 over 2s (it will then continue incrementing but it doesn't seem to matter if the value exceeds 1.0).

Using a code component might allow you to do more sophisticated things (e.g. fade in for a while, hold it, then fade out). Or more simply, you just create multiple successive Patch stimulus components, each with a different equation or value in the opacity field depending on their place in the timeline.


Typing effects
==============
Key idea: vary the **onset/offset** of stimulus

Question: I'd like to present my text using a typing effect.

Answer: Please click here to watch youtube tutorial `Typing effect without code <https://www.youtube.com/watch?v=Kcr3--LTvBk>`_