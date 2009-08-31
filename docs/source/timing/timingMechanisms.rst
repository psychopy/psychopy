PsychoPy timing mechanisms
-----------------------------


Things that PsychoPy will automatically attempt to do on your behalf (as of v1.50.00 unless stated):

    * all systems: PsychoPy was built very much around the use of optimised hardware-accelerated graphics. The graphics card is made to do as much as possible, leaving the cpu relatively free
    
    * win32:
        * The priority of the experiment thread is raised with SetPriorityClass and SetThreadPriority.
        * Syncing to the :term:`VBI` is enabled where possible, but this may not be allowed by some graphics cards (e.g. Intel integrated graphics chips) and may have been forced `off` in the control panel of other cards (check in the advanced panel of your display properties for `vsync`).
      
    * OS X:
        * The priority of the thread is raised with mach/thread_policy_set
        * :term:`VBI syncing` and `VBI blocking` are both achieved on all systems by measuring the current beam position of the monitor
    
    * Linux:
        * The priority of the thread is set to SCHED_RR using sched_setscheduler, but this only operates if the user runs the script with su permissions.
        * At the time of writing I'm (Jon) not sure about whether or not linux systems block on win.flip() 