Working With Spatial Units
------------------------------------------------------------------

One of the key advantages of PsychoPy over many other experiment-building software packages is that stimuli can be described in a wide variety of real-world, device-independent [units](https://www.psychopy.org/general/units.html). In most other systems you provide the stimuli at a fixed size and location in pixels, or percentage of the screen, and then have to calculate how many cm or degrees of visual angle that was. In PsychoPy, after providing information about your monitor, via the [Monitor Center](https://www.psychopy.org/general/monitors.html), you can simply specify your stimulus in the unit of your choice and allow PsychoPy to calculate the appropriate pixel size for you.

However, understanding what exactly these different units mean can be confusing at first, so this demo provides a visual example of how a square will look at different sizes in different units. 