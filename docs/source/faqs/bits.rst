Why is the bits++ demo not working?
=====================================

So far PsychoPy supports bits++ only in the bits++ mode (rather than mono++ or color++). In this mode, a code (the T-lock code) is written to the lookup table on the bits++ device by drawing a line at the top of the window. The most likely reason that the demo isn't working for you is that this line is not being detected by the device, and so the lookup table is not being modified. Most of these problems are actually nothing to do with PsychoPy /per se/, but to do with your graphics card and the CRS bits++ box itself.

There are a number of reasons why the T-lock code is not being recognised:

* the bits++ device is in the wrong mode. Open the utility that CRS supply and make sure you're in the right mode. Try resetting the bits++ (turn it off and on).
* the T-lock code is not fully on the screen. If you create a window that's too big for the screen or badly positioned then the code will be broken/not visible to the device.
* the T-lock code is on an 'odd' pixel. 
* the graphics card is doing some additional filtering (win32). Make sure you turn off any filtering in the advanced display properties for your graphics card
* the gamma table of the graphics card is not set to be linear (but this should normally be handled by PsychoPy, so don't worry so much about it).
* you've got a Mac that's performing temporal dithering (new Macs, around 2009). Apple have come up with a new, very annoying idea, where they continuously vary the pixel values coming out of the graphics card every frame to create additional intermediate colours. This will break the T-lock code on 1/2-2/3rds of frames.
