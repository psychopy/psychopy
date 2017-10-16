##################################
ioHub Event Monitoring Framework
##################################

ioHub is a Python package providing a cross-platform computer device event monitoring 
and storage framework. ioHub is free to use and is GPL version 3 licensed.

ioHub is not a complete experiment design and runtime API. It's main focus is 
on device event monitoring, real-time reporting, and persistent storage of 
input device events on a system wide basis. When ioHub is used for experiment 
device monitoring during a psychology or neuroscience type study, 
ioHub is designed to be used with the most excellent `PsychoPy <http://www.psychopy.org>`_. 

.. note:: As of the May 8th, 2013 release of PsychoPy 1.77 rc1, the ioHub Package has merged with
    the PsychoPy package and is now being distributed as part of PsychoPy. This 
    version of the documentation has been updated to reflect the correct class, 
    method, and function name paths when using psychopy.iohub.

OS and Device Support
#####################

* Support for the following operating Systems:
	#. Windows XP SP3, 7, 8
	#. Apple OS X 10.6 - 10.8.5 (10.9 *is not* currently supported)
	#. Linux 2.6+
	
* Monitoring of events from computer devices such as:
	#. Keyboard
	#. Mouse
	#. Analog to Digital Converter
	#. XInput Compatible Game Pad
	#. Eye Tracker, via a Common Eye Tracking Interface
	#. Elo Touch Screens
	
.. note::
    The Common Eye Tracking Interface provides the same user level API for all supported hardware,
    meaning the same experiment script can be run with any supported eye tracker and the same 
    data analyses can be performed on any eye tracking data saved via ioHub in the ioDataStore
    as long as the event type being used for analysis is supported by the different implementations used.
     
    The Common Eye Tracking Interface currently supports the following eye tracking systems:
	
        #. `LC Technologies <http://www.eyegaze.com>`_ EyeGaze and EyeFollower models.
        #. `SensoMotoric Instruments <http://www.smivision.com>`_ iViewX models.
        #. `SR Research <http://www.sr-research.com>`_ EyeLink models.
        #. `TheEyeTribe <http://theeyetribe.com/>`_ TheEyeTribe system (In Progress).
        #. `Tobii <http://www.tobii.com>`_ Technologies Tobii models.

ioHub Features
###############

* Independent device event monitoring:
    The ioHub Process, responsible for the monitoring, bundling, and storage of device events, runs in a separate OS process from the main PsychoPy Process. ioHub DeviceEvents are monitored continuously system-wide rather than intermittently or relative to the PsychoPy window. In fact, no graphical window is needed to monitor supported devices (An example of using this *headless* event tracking mode is provided in the examples folder). ioHub Device event monitoring and callback processing occurs very quickly in parallel, regardless of what state the PsychoPy Process is in (i.e. even when it is performing a blocking operation and would not be able to monitor new events itself).
* Easy data storage and retrieval:
    ioHub Device event data are saved in the *ioHub DataStore*, a structured event definition using the `HDF5 <http://www.hdfgroup.org/HDF5/>`_ standard. With a multicore CPU, all device events during an experiment can be automatically saved for post hoc analyses without impairing performance of the PsychoPy Process. The same device events saved to the ioDataStore can be accessed during an experiment as numpy ndarray's, affording direct use in powerful scientific Python models such as Scipy and MatPlotLib. These events can be retrieved during the PsychoPy experiment and from the ioDataStore very flexibly: for example, by event time (chronologically and device independent), by device (e.g., mouse events), and by event type (e.g., fixation events).
* Smooth integration with PsychoPy:
    When used with full `PsychoPy <http://www.psychopy.org>`_ functionality, ioHub can save debugging messages to PsychoPy log files, and PsychoPy *LogEvents* can be saved in the ioDataStore (as well as the PsychoPy logging system). Furthermore, ioHub and PsychoPy share a common time base, so times read from the PsychoPy Experiment process are directly comparable to times read from ioHub Device Events (if the PsychoPy time is based on psychopy.core.getTime or default psychopy.logging.defaultClock mechanisms).
* High-precision synchronization:
    The ioHub Process provides a common timebase to automatically synchronize device events from multiple physical and virtual devices. In some cases the ioHub Process interacts with the PsychoPy Process 'as if' it were another virtual device: descriptive MessageEvents can be sent in the PsychoPy experiment script to the ioHub Process in real-time, allowing important information in the course of the experiment (such as stimulus onsets, etc.) to be time stamped with microsecond-level precision and saved in the ioDataStore alongside similarly time-stamped device events.


Github Hosted
##############

The ioHub project source is available on GitHub `here <https://www.github.com/isolver/ioHub>`_.
Given the merging of the ioHub Package with PsychoPy, the ioHub Github repository will be kept for
historical reasons, but users wanting to install and use ioHub should do so by 
going to the `PsychoPy <http://www.psychopy.org>`_ website and following download and installation instructions
there.

Support
########

Given the merging of ioHub with PsychoPy, please visit the 
`PsychoPy <http://www.psychopy.org>`_ website and follow the links to the
PsychoPy User groups.

Documentation Contents
########################

.. toctree::
   :maxdepth: 4
   
   Installation <iohub/installation>
   Supported Device Types for Your OS <iohub/supported_devices>
   Quick Start Guide <iohub/quickstart>
   User Manual / API Review <iohub/api_and_manual/start_here>
   Performance <iohub/performance>
   Credits <iohub/credits>
   License <iohub/license>
   Change Log <iohub/change_log>
