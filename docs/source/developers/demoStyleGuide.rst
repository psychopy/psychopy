.. _demostyleguide:

Style-guide for coder demos
===========================

**OpenHatchers:** Welcome! Each coder demo is intended to illustrate a key PsychoPy feature (or two), especially in ways that show usage in practice, and go beyond the description in the API. The aim is not to illustrate every aspect, but to get people up to speed quickly, so they understand how basic usage works, and could then play around with advanced features.

As a newcomer to PsychoPy, you are in a great position to judge whether the comments and documentation are clear enough or not. If something is not clear, you may need to ask a PsychoPy contributor for a description.

Here are some style guidelines, written for the OpenHatch event(s) but hopefully useful after that too. These are intended specifically for the coder demos, not for the internal code-base (although they are generally quite close).

The idea is to have clean code that looks and works the same way across demos, while leaving the functioning mostly untouched. Some small changes to function might be needed (e.g., to enable the use of 'escape' to quit), but typically only minor changes like this.

- Generally, when you run the demo, does it look good and help you understand the feature? Where might there be room for improvement? 

- Standardize the top stuff to have shbang, encoding, and a comment::

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    """Demo name, purpose, description (1-2 sentences, although some demos need more explanation). 
    """

- Follow PEP-8 mostly, some exceptions:

  - current PsychoPy convention is to use camelCase for variable names, so don't convert those to underscores

  - 80 char columns can spill over a little. Try to keep things within 80 chars most of the time.

  - do allow multiple imports on one line, if they are thematically related (e.g., `import os, sys, glob`)

- Check all imports:

  - remove any unnecessary ones
  - add `from __future__ import division`, even if not needed (and make sure that doing so does not break the demo!)

- Fix any typos in comments; convert any lingering British spellings to US, e.g., change `colour` to `color`

- Use `core.time()`, not `time.time()`. If needed, you can do `from psychopy import core`.

- Prefer `if <boolean>:` as a construct instead of `if <boolean> == True:`. (There might not be any to change).

- For readability (especially for people new to python), opt for slightly more verbose but easier-to-understand code instead of clever or terse formulations. For example, prefer `for` loops over list comprehensions. Some demos do use numpy arrays, but only when vectors are needed for speed, thats fine (in fact, its part of the demo).

- Standardize variable names:

  - use `win` for the `visual.Window()`, and so `win.flip()`

- Provide a consistent way for a user to exit a demo using the keyboard, ideally enable this on every visual frame: use `if len(event.getKeys(['escape']): core.quit()`. **Note**: if there is a previous `event.getKeys()` call, it can slurp up the `'escape'` keys. So check for 'escape' first.

- Provide a consistent time-out, if there's no user response and a timeout is appropriate for the demo: Automatically quit after 10 seconds::

    demoClock = core.clock()  # set to 0.000s at this point
    ...
    if demoClock.getTime() > 10.:
        core.quit()

- Most demos are not full screen. For any that are full-screen, see if it can work without being full screen. If it has to be full-screen, add some text to say that pressing 'escape' will quit.

- If logging info to the console helps better understanding the demo, here's how to do it::

    from psychopy import logging
    ...
    logging.console.setLevel(logging.INFO)  # or logging.DEBUG for even more stuff

- End a script with `win.close()` (if it used a visual.Window) and then `core.quit()` even though its not strictly necessary

