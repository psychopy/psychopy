
Reducing dropped frames
--------------------------

There are many things that can affect the speed at which drawing is achieved on your computer. These include, but are probably not limited to; your graphics card, CPU, operating system, running programs, stimuli, and your code itself. Of these, the CPU and the OS appear to make rather little difference. To determine whether you are actually dropping frames see :doc:`detectingFrameDrops`.

Things to change on your system:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   1. make sure you have a good graphics card. Avoid integrated graphics chips, especially Intel integrated chips and especially on laptops (because on these you don't get to change your mind so easily later). In particular, try to make sure that you card supports OpenGL 2.0
   2. shut down as many programs as you can, including background processes (e.g. anti-virus auto-updating)
   3. On OS X, Turn off TimeMachine backups 

Writing optimal scripts
~~~~~~~~~~~~~~~~~~~~~~~

   1. run in full-screen mode (rather than simply filling the screen with your window). This way the OS doesn't have to spend time working out what application is currently getting keyboard/mouse events.
   2. after generating stimuli
   3. don't generate your stimuli when you need them. Generate them in advance and then just modify them later with the methods like setContrast(), setOrientation() etc...
   4. calls to the following functions are comparatively slow, because they require more cpu time than most other functions and then have to send a large amount of data to the graphics card. Try to use these methods in inter-trial intervals. This is especially true when you need to load an image from disk too as the texture.
         1. PatchStim.setTexture()
         2. RadialStim.setTexture()
         3. TextStim.setText() 
   5. if you don't have OpenGL 2.0 then calls to setContrast, setRGB and setOpacity will also be slow, because they also make a call to setTexture(). If you have shader support then this call is not necessary and a large speed increase will result.
   6. avoid loops in your python code (use numpy arrays to do maths with lots of elements)
   7. if you need to create a large number (e.g. greater than 10) similar stimuli, then try the ElementArrayStim 

Possible good ideas 
~~~~~~~~~~~~~~~~~~~~~

It isn't clear that these actually make a difference, but they might).

   1. disconnect the internet cable (to prevent programs performing auto-updates?)
   2. on Macs you can actually shut down the Finder. It might help. See Alex Holcombe's page
   3. use a single screen rather than two (probably there is some graphics card overhead in managing double the number of pixels?)

