:mod:`psychopy.monitors` - for those that don't like Monitor Center
======================================================================

Most users won't need to use the code here. In general the Monitor Centre interface is sufficient
and monitors setup that way can be passed as strings to :class:`~psychopy.visual.Window` s. If there
is some aspect of the normal calibration that you wish to override. eg::

   from psychopy import visual, monitors
   mon = monitors.Monitor('SonyG55')#fetch the most recent calib for this monitor
   mon.setDistance(114)#further away than normal?
   win = visual.Window(size=[1024,768], monitor=mon)
    
You might also want to fetch the :class:`~psychopy.monitors.Photometer` class for conducting your own calibrations
    
:class:`Monitor`
------------------------------------
.. autoclass:: psychopy.monitors.Monitor
    :members: 
    :undoc-members: 
    
--------
    
:class:`GammaCalculator`
------------------------------------
.. autoclass:: psychopy.monitors.GammaCalculator
    :members: 
    :undoc-members: 
    
--------
    
:func:`getAllMonitors`
------------------------------------
.. autofunction:: psychopy.monitors.getAllMonitors

:func:`findPR650`
------------------------------------
.. autofunction:: psychopy.monitors.findPR650 

:func:`getLumSeriesPR650`
------------------------------------
.. autofunction:: psychopy.monitors.getLumSeriesPR650

:func:`getRGBspectra`
------------------------------------
.. autofunction:: psychopy.monitors.getRGBspectra

:func:`gammaFun`
------------------------------------
.. autofunction:: psychopy.monitors.gammaFun

:func:`gammaInvFun`
------------------------------------
.. autofunction:: psychopy.monitors.gammaInvFun

:func:`makeDKL2RGB`
------------------------------------
.. autofunction:: psychopy.monitors.makeDKL2RGB

:func:`makeLMS2RGB`
------------------------------------
.. autofunction:: psychopy.monitors.makeLMS2RGB
