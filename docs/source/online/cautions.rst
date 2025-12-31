.. _onlineCaveats:

Caveats and cautions
--------------------------
.. note::
   For guidance on writing code components that translate well to PsychoJS, see the :doc:`Known limitations and best practices for code components <known-limitations>` page. 


The first caution to be aware of is that while |PsychoPy| has existed since 2002, benefiting from contributions by over 150 GitHub contributors to make it feature-rich and streamlined, |PsychoJS| has only existed since 2016. It has relied mainly on a small internal team, so sometimes parity issues with the Python version occur. As a result, some features may behave differently online or have rough edges. Use PsychoJS carefully and always check that your study behaves as expected.

For an in-depth examination of the pros and cons of running studies online (including a consideration of timing issues), see `The timing mega-study (Bridges et al., 2020) <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7512138/>`_.

Differences between |PsychoPy| and PsychoJS studies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `PsychoJS`_ library looks much like its PsychoPy (Python) equivalent; it has classes like `Window` and `ImageStim` and these have the same attributes. So, from that aspect, things are relatively similar and if you already know your way around a PsychoPy script then reading PsychoJS code should be fairly intuitive.

Obviously there are some syntax changes that you'd need to understand (e.g. JavaScript requires semi-colons between lines and uses `{}` to indicate code blocks). A further issue is that the translation is usually not as simple as a line-by-line conversion

There are a few key differences that you need to understand moving from Python code to the equivalent PsychoJS script.

- Builder does not convert your Python code into JavaScript. It writes the JavaScript from scratch from the experiment logic. If you use code in a Builder Component then that code will need to be valid JavaScript code. We hope, in the future, to perform rudimentary automated conversion. Even then, that will only convert the syntax but will not be able to find equivalent function names
- Resources for your study (images, conditions files etc.) must be in the `resources` folder next to the html file that |PsychoPy| outputs. In most cases |PsychoPy| can find these and include them automatically but if your study uses code components then the resource files needed will need to be specified.

Most of the issues below affect your study if you have additional code components inserted into the study and do not affect pure Builder-based designs.


.. _onlineTiming:

Timing expectations
~~~~~~~~~~~~~~~~~~~~~~~

In general timing of web-based experiments will be poorer than locally-run studies. That said, we think PsychoJS will have timing about as good as it can be! What are the specific considerations?

**Variable internet connection:** Surprisingly no, this isn't one to worry about! PsychoJS will make sure that the script and all the recourses for your study (image files etc) are downloaded to the computer beforehand. On a slow internet connection it may take longer for your study to start but the performance won't be limited by that while it runs. Happy days!

**Visual stimuli:** PsychoJS is using WebGL (high performance web rendering using advanced graphics card features) and we have confirmed that PsychoJS is able to run with frame-precise timing. That means, if you ask for a stimulus to last for, say, 6 frames then you will get exactly 100 ms of stimulus presentation.

**Response timing:** Again this won't be affected by your internet connection (because the keypresses are being time-stamped locally, at your computer, not by the web server). The major problem, as with any software, is that keyboards have long and variable latencies (10-30 ms typically). On a local lab-based setup you can get around this by using custom hardware (a button box) but this obviously isn't possible when your user is anywhere in the world!

.. _schedulers:

Schedulers
~~~~~~~~~~~~~~~

A Python script runs essentially in sequence; when one line of code is called the script waits for that line to finish and then the next lines begins. JavaScript is designed to be asynchronous; all parts of your web page should load at once.

As a result, PsychoJS needed something to control the running order of the different parts of the script (e.g. the trials need to occur one after the other, waiting for the previous one to finish). To do this PsychoJS adds the concept of the `Scheduler`. For instance, you could think of the Flow in PsychoPy as being a Schedule with various items being added to it. Some of those items, such as trial loops also schedule further events (the individual trials to be run) and these can even be nested: the Flow could schedule some blocks, which could schedule a trials loop, which would schedule each individual trial.

If you export a script from one of your Builder experiments you can examine this to see how it works.

.. _functions:

Functions
~~~~~~~~~~~~~~~

Some people will be delighted to see that in PsychoJS scripts output by Builder there are functions specifying what should happen at different parts of the experiment (a function to begin the Routine, a function for each frame of the Routine etc.). The essence of the `PsychoJS`_ script is that you have any number of these functions and then add them to your scheduler to control the flow of the experiment.

In fact, many experienced programmers might feel that this is the "right" thing to do and that we should change the structure of the Python scripts to match this. The key difference that makes it easy in the JavaScript, but not in the Python version, is that variables in JS are inherently `global`. When a stimulus is created during the Routine's initialization function it will still be visible to the each-frame function. In the PsychoPy Python script we would have to use an awful lot of `global` statements and users would probably have a lot of confusing problems. So, no, we aren't about to change it unless you have a good solution to that issue.

.. _PsychoJS: https://github.com/psychopy/psychojs

.. _supportedBrowsers:

Supported browsers
~~~~~~~~~~~~~~~~~~~~~~~

We'd recommend running on an updated browser but pretty much any modern browser (released since roughly 2011) should be able to run these studies. It needs to support HTML5/canvas and ideally it would support WebGL (if not Canvas then will used but that is less efficient).

Specifically, these support Canvas (minimum requirement):

- Firefox 10+ (released 2012)
- Chrome 11+ (2011)
- Safari 2.0+ (2005)
- Opera 12+ (2011)
- Internet Explorer 9+ (released in 2011) but we really recommend you avoid it!

Browsers supporting WebGL (hardware-accelerated graphics in the browser):

- Firefox 15+ (2012)
- Chrome 11+ (2011)
- Safari 5.1+ (2011/12?)
- Opera 19+
- Microsoft Edge
- IE 11+ (2013)

.. _onlineContextDifferences:


Online vs. in-lab testing
~~~~~~~~~~~~~~~~~~~~~~~~~~

When moving experiments online, there are several key differences compared to controlled lab settings. Participants may be using a wide range of devices with different screen sizes, resolutions, and frame rates. It is important to account for these variations when designing stimuli and interpreting results.

Stimuli size and scaling
^^^^^^^^^^^^^^^^^^^^^^

- **Device variability:** In the lab, you present on a known monitor with fixed dimensions, and you can configure your experiment accordingly. Online, participants may use anything from widescreen monitors to small touchscreens. Frame rates can also vary, so timing of visual stimuli (if using frames rather than seconds for duration/start/stop times) may differ slightly between users.

- **Units:** We recommend using **height units** (the default) for stimuli, as this scales appropriately across most devices.  

- **Physical size control:** If your study requires stimuli to be a consistent physical size across participants, you need to determine pixels per cm on the participant’s screen. A common approach is **screen scaling**, where the participant resizes an on-screen object (e.g., a credit card) to match a real-world reference. Example code for PsychoPy: `screenscale <https://gitlab.pavlovia.org/Wake/screenscale>`_  
  Original paper describing the method: `Li et al., 2020 <https://www.nature.com/articles/s41598-019-57204-1>`_

- **Visual angle units:** To use degrees of visual angle, you also need **viewing distance**. This can be measured:
  
  - **Statically:** Using a one-time measurement such as a blind spot test. Example experiment: `Blind Spot Test <https://run.pavlovia.org/vespr/blind-spot/>`_
  - **Dynamically:** Using external tools to track head position. One recommended tool is **EasyEyes**: `Paper <https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2023.1255465/full>`_, full documentation: `EasyEyes App <https://easyeyes.app/home>`_

By incorporating these methods, you can better approximate the control offered in lab experiments while still taking advantage of online testing.

Audio presentation considerations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When running experiments online, participants may be in a variety of environments with different background noise levels and audio equipment. A few considerations:

- **Headphones:** Encourage participants to use headphones to ensure they hear the stimuli clearly. Note that **Bluetooth headphones** can introduce additional latency, which may affect timing-sensitive tasks.

- **Headphone checks:** You can implement a headphone screening procedure to verify that participants are using headphones and that audio channels are functioning correctly. Community examples include:  
  - `Headphones Check Experiment <https://run.pavlovia.org/sijiazhao/headphones-check/>`_  

- **Methods:** These checks use auditory illusions and techniques such as Huggins pitch, anti-phase tones, and binaural beats to detect headphone usage.The methods and validation are described in Milne et al., 2021:  
  `Behaviour Research Methods <https://link.springer.com/epdf/10.3758/s13428-020-01514-0?sharing_token=QXGlAgoPwa1XQcN1zBxsPZAH0g46feNdnc402WrhzyqXFZRgxM1a4isvxnyRsbzcmQHrqJevtPM8JC-73_63kcc5oq24ZEzDIkOgc_XJBJ6EL9b4W3aTktmVtQL2A-n5VBhjk1Bj9GcUJPgkIN5WWvGEbfIBTqs9_qCN00eeo0w%3D>`_
