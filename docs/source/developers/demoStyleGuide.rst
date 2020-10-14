.. _demostyleguide:

Style-guide for coder demos
===========================

Each coder demo is intended to illustrate a key PsychoPy feature (or two), especially in ways that show usage in practice, and go beyond the description in the API. The aim is not to illustrate every aspect, but to get people up to speed quickly, so they understand how basic usage works, and could then play around with advanced features.

As a newcomer to PsychoPy, you are in a great position to judge whether the comments and documentation are clear enough or not. If something is not clear, you may need to ask a PsychoPy contributor for a description; email psychopy-dev@googlegroups.com.

Here are some style guidelines, written for the OpenHatch event(s) but hopefully useful after that too. These are intended specifically for the coder demos, not for the internal code-base (although they are generally quite close).

The idea is to have clean code that looks and works the same way across demos, while leaving the functioning mostly untouched. Some small changes to function might be needed (e.g., to enable the use of 'escape' to quit), but typically only minor changes like this.

- Generally, when you run the demo, does it look good and help you understand the feature? Where might there be room for improvement? You can either leave notes in the code in a comment, or include them in a commit message.

- Standardize the top stuff to have 1) a shebang with python, 2) utf-8 encoding, and 3) a comment::

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-

    """Demo name, purpose, description (1-2 sentences, although some demos need more explanation).
    """

For the comment / description, it's a good idea to read and be informed by the relevant parts of the API (see http://psychopy.org/api/api.html), but there's no need to duplicate that text in your comment. If you are unsure, please post to the dev list psychopy-dev@googlegroups.com.

- Follow PEP-8 mostly, some exceptions:

  - current PsychoPy convention is to use camelCase for variable names, so don't convert those to underscores

  - 80 char columns can spill over a little. Try to keep things within 80 chars most of the time.

  - do allow multiple imports on one line if they are thematically related (e.g., `import os, sys, glob`).

  - inline comments are ok (because the code demos are intended to illustrate and explain usage in some detail, more so than typical code).

- Check all imports:

  - remove any unnecessary ones

  - replace `import time` with `from psychopy import core`. Use `core.getTime()` (= ms since the script started) or `core.getAbsTime()` (= seconds, unix-style) instead of `time.time()`, for all time-related functions or methods not just `time()`.

  - add `from __future__ import division`, even if not needed. And make sure that doing so does not break the demo!

- Fix any typos in comments; convert any lingering British spellings to US, e.g., change `colour` to `color`

- Prefer `if <boolean>:` as a construct instead of `if <boolean> == True:`. (There might not be any to change).

- If you have to choose, opt for more verbose but easier-to-understand code instead of clever or terse formulations. This is for readability, especially for people new to python. If you are unsure, please add a note to your commit message, or post a question to the dev list psychopy-dev@googlegroups.com.

- Standardize variable names:

  - use `win` for the `visual.Window()`, and so `win.flip()`

- Provide a consistent way for a user to exit a demo using the keyboard, ideally enable this on every visual frame: use `if len(event.getKeys(['escape']): core.quit()`. **Note**: if there is a previous `event.getKeys()` call, it can slurp up the `'escape'` keys. So check for 'escape' first.

- Time-out after 10 seconds, if there's no user response and a timeout is appropriate for the demo (and a longer time-out might be needed, e.g., for `ratingScale.py`)::

    demoClock = core.clock()  # is demoClock's time is 0.000s at this point
    ...
    if demoClock.getTime() > 10.:
        core.quit()

- Most demos are not full screen. For any that are full-screen, see if it can work without being full screen. If it has to be full-screen, add some text to say that pressing 'escape' will quit.

- If displaying log messages to the console seems to help understand the demo, here's how to do it::

    from psychopy import logging
    ...
    logging.console.setLevel(logging.INFO)  # or logging.DEBUG for even more stuff

- End a script with `win.close()` (assuming the script used a `visual.Window`), and then `core.quit()` even though it's not strictly necessary
