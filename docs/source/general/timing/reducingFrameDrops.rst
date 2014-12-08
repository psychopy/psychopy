.. _reducingFrameDrops:

Reducing dropped frames
--------------------------

There are many things that can affect the speed at which drawing is achieved on your computer. These include, but are probably not limited to; your graphics card, CPU, operating system, running programs, stimuli, and your code itself. Of these, the CPU and the OS appear to make rather little difference. To determine whether you are actually dropping frames see :doc:`detectingFrameDrops`.

Things to change on your system:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   #. make sure you have a good graphics card. Avoid integrated graphics chips, especially Intel integrated chips and especially on laptops (because on these you don't get to change your mind so easily later). In particular, try to make sure that your card supports OpenGL 2.0
   #. shut down as many programs, including background processes. Although modern processors are fast and often have multiple cores, substantial disk/memory accessing can cause frame drops
	* anti-virus auto-updating (if you're allowed)
	* email checking software
	* file indexing software
	* backup solutions (e.g. TimeMachine)
	* Dropbox
	* Synchronisation software

Writing optimal scripts
~~~~~~~~~~~~~~~~~~~~~~~

   #. run in full-screen mode (rather than simply filling the screen with your window). This way the OS doesn't have to spend time working out what application is currently getting keyboard/mouse events.
   #. don't generate your stimuli when you need them. Generate them in advance and then just modify them later with the methods like setContrast(), setOrientation() etc...
   #. calls to the following functions are comparatively slow; they require more CPU time than most other functions and then have to send a large amount of data to the graphics card. Try to use these methods in inter-trial intervals. This is especially true when you need to load an image from disk too as the texture.
         #. GratingStim.setTexture()
         #. RadialStim.setTexture()
         #. TextStim.setText()
   #. if you don't have OpenGL 2.0 then calls to setContrast, setRGB and setOpacity will also be slow, because they also make a call to setTexture(). If you have shader support then this call is not necessary and a large speed increase will result.
   #. avoid loops in your python code (use numpy arrays to do maths with lots of elements)
   #. if you need to create a large number (e.g. greater than 10) similar stimuli, then try the ElementArrayStim

Possible good ideas
~~~~~~~~~~~~~~~~~~~~~

It isn't clear that these actually make a difference, but they might).

   #. disconnect the internet cable (to prevent programs performing auto-updates?)
   #. on Macs you can actually shut down the Finder. It might help. See Alex Holcombe's page `here <http://openwetware.org/wiki/Holcombe:VerifyTiming>`_
   #. use a single screen rather than two (probably there is some graphics card overhead in managing double the number of pixels?)
