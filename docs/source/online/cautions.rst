.. _onlineCaveats:

Caveats and cautions
--------------------------

The first caution to be aware of here is that PsychoJS was only written in 2016. It hasn't been widely battle-tested and almost certainly has some rough edges. Use it carefully and check your study does what you expect.

For an in-depth examination of the pros and cons of running studies online (including a consideration of timing issues) see `Woods et al (2015) https://peerj.com/articles/1058/`_

Differences between PsychoPy and PsychoJS studies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most of the issues below affect your study if you have additional code components inserted into the study and do not affect pure Builder-based designs.

- Builder does not convert your Python code into JavaScript. It writes the JavaScript from scratch from the experiment logic. If you use code in a Builder Component then that code will need to be valid JavaScript code. We hope, in the future, to perform rudimentary automated conversion. Even then, that will only convert the syntax but will not be able to find equivalent function names
- Resources for your study (images, conditions files etc.) must be in the `resources` folder next to the html file that PsychoPy outputs. In most cases PsychoPy can find these and include them automatically but if your study

.. _onlineTiming:

Timing expectations
~~~~~~~~~~~~~~~~~~~~~~~

In general timing of web-based experiments will be poorer than locally-run studies. That said, we think PsychoJS will have timing about as good as it can be! What are the specific considerations?

**Variable internet connection:** Surprisingly no, this isn't one to worry about! PsychoJS will make sure that the script and all the recourses for your study (image files etc) are downloaded to the computer beforehand. On a slow internet connection it may take longer for your study to start but the performance won't be limited by that while it runs. Happy days!

**Visual stimuli:** PsychoJS is using WebGL (high performance web rendering using advanced graphics card features) and we have confirmed that PsychoJS is able to run with frame-precise timing. That means, if you ask for a stimulus to last for, say, 6 frames then you will get exactly 100 ms of stimulus presentation.

**Response timing:** Again this won't be affected by your internet connection (because the keypresses are being time-stamped locally, at your computer, not by the web server). The major problem, as with any software, is that keyboards have long and variable latencies (10-30 ms typically). On a local lab-based setup you can get around this by using custom hardware (a button box) but this obviously isn't possible when your user is anywhere in the world!

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
