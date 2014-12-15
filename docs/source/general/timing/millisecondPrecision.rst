
Can PsychoPy deliver millisecond precision?
---------------------------------------------

The simple answer is 'yes', given some additional hardware. The clocks that PsychoPy uses do have sub-millisecond precision but your keyboard has a latency of 4-25ms depending on your platform and keyboard. You could buy a response pad (e.g. a `Cedrus Response Pad`_ ) and use PsychoPy's serial port commands to retrieve information about responses and timing with a precision of around 1ms.

.. _Cedrus Response Pad: http://www.cedrus.com/responsepads

Before conducting your experiment in which effects might be on the order of 1 ms, do consider that;
    - your screen has a temporal resolution of ~10 ms
    - your visual system has a similar upper limit (or you would notice the flickering screen)
    - human response times are typically in the range 200-400 ms and very variable
    - USB keyboard latencies are variable, in the range 20-30ms

That said, PsychoPy does aim to give you as high a temporal precision as possible, and is likely not to be the limiting factor of your experiment.

.. _monitorTiming:

Computer monitors 
---------------------------------------------

Monitors have fixed refresh rates, typically 60 Hz for a flat-panel display, higher for a CRT (85-100 Hz are common, up to 200 Hz is possible). For a refresh rate of 85 Hz there is a gap of 11.7 ms between frames and this limits the timing of stimulus presentation. You cannot have your stimulus appear for 100 ms, for instance; on an 85Hz monitor it can appear for either 94 ms (8 frames) or 105 ms (9 frames). There are further, less obvious, limitations however.

For ''CRT (cathode ray tube) screens'', the lines of pixels are drawn sequentially from the top to the bottom and once the bottom line has been drawn the screen is finished and the line returns to the top (the Vertical Blank Interval, VBI). Most of your frame interval is spent drawing the lines with 1-2ms being left for the VBI. This means that the pixels at the bottom are drawn '''up to 10 ms later''' than the pixels at the top of the screen. At what point are you going to say your stimulus 'appeared' to the participant? For flat panel displays, or (or LCD projectors) your image will be presented simultaneously all over the screen, but it takes up to 20 ms(!!) for your pixels to go all the way from black to white (manufacturers of these panels quote values of 3 ms for the fastest panels, but they certainly don't mean 3 ms white-to-black, I assume they mean 3 ms half-life).

.. figure:: ../../images/TopOfScreen.jpg

    Figure 1: photodiode trace at top of screen. The image above shows the luminance trace of a CRT recorded by a fast photo-sensitive diode at the top of the screen when a stimulus is requested (shown by the square wave). The square wave at the bottom is from a parallel port that indicates when the stimulus was flipped to the screen. Note that on a CRT the screen at any point is actually black for the majority of the time and just briefly bright. The visual system integrates over a large enough time window not to notice this. On the next frame after the stimulus 'presentation time' the luminance of the screen flash increased.

.. figure:: ../../images/BottOfScreen.jpg

    Figure 2: photodiode trace of the same large stimulus at bottom of screen. The image above shows comes from exactly the same script as the above but the photodiode is positioned at the bottom of the screen. In this case, after the stimulus is 'requested' the current frame (which is dark) finishes drawing and then, 10ms later than the above image, the screen goes bright at the bottom.

.. warning:: If you're using a regular computer display, *you have a hardware-limited temporal precision of 10 ms irrespective of your response box or software clocks etc...* and should bear that in mind when looking for effect sizes of less than that.

Can I have my stimulus to appear with a very precise rate?
------------------------------------------------------------

Yes. Generally to do that you should time your stimulus (its onset/offset, its rate of change...) using the frame refresh rather than a clock. e.g. you should write your code to say 'for 20 frames present this stimulus' rather than 'for 300ms present this stimulus'. Provided your graphics card is set to synchronise page-flips with the vertical blank, and provided that you aren't :doc:`dropping frames <detectingFrameDrops>` the frame rate will always be absolutely constant.
