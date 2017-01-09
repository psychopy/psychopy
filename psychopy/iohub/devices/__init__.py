# -*- coding: utf-8 -*-
from __future__ import division

"""
ioHub
.. file: ioHub/devices/__init__.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

import gc, os, sys, copy
import collections
from collections import deque
from operator import itemgetter
import numpy as N
import psutil
from ..util import convertCamelToSnake, print2err,printExceptionDetailsToStdErr
from psychopy.clock import monotonicClock

class ioDeviceError(Exception):
    def __init__(self, device, msg):
        Exception.__init__(self, msg)
        self.device = device
        self.msg = msg

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "ioDeviceError:\n\tMsg: {0:>s}\n\tDevice: {1}\n".format(self.msg,repr(self.device))

class ioObjectMetaClass(type):
    def __new__(meta, name, bases, dct):
        return type.__new__(meta, name, bases, dct)
    def __init__(cls, name, bases, dct):
        type.__init__(cls,name, bases, dct)

        if '_newDataTypes' not in dct:
            cls._newDataTypes=[]

        if '_baseDataTypes' not in dct:
            parent = cls._findDeviceParent(bases)
            if parent:
                cls._baseDataTypes=parent._dataType
            else:
                cls._baseDataTypes=[]

        cls._dataType=cls._baseDataTypes+cls._newDataTypes
        cls.CLASS_ATTRIBUTE_NAMES=[e[0] for e in cls._dataType]
        cls.NUMPY_DTYPE=N.dtype(cls._dataType)

        if len(cls.__subclasses__())==0 and 'DeviceEvent' in [c.__name__ for c in cls.mro()]:
            cls.namedTupleClass=collections.namedtuple(name+'NT',cls.CLASS_ATTRIBUTE_NAMES)


    def _findDeviceParent(cls,bases):
        parent=None
        if len(bases)==1:
            parent=bases[0]
        else:
            for p in bases:
                if 'Device' in p.__name__:
                    parent=p
                    break
        if parent is None or 'object' in parent.__name__:
            return None
        return parent

class ioObject(object):
    """
    The ioObject class is the base class for all ioHub Device and DeviceEvent classes.

    Any ioHub Device or DeviceEvent class (i.e devices like Keyboard Device, Mouse Device, etc;
    and device events like Message, KeyboardPressEvent, MouseMoveEvent, etc.)
    also include the methods and attributes of this class.
    """
    __metaclass__= ioObjectMetaClass
    __slots__=['_attribute_values',]
    def __init__(self,*args,**kwargs):
        self._attribute_values=[]

        if len(args) > 0:
            for i,n in enumerate(self.CLASS_ATTRIBUTE_NAMES):
                setattr(self,n,args[i])
                self._attribute_values.append(args[i])

        elif len(kwargs)>0:
            for key in self.CLASS_ATTRIBUTE_NAMES:
                value=kwargs[key]
                setattr(self,key,value)
                self._attribute_values.append(value)

    def _asDict(self):
        """
        Return the ioObject in dictionary format, with keys as the ioObject's
        attribute names, and dictionary values equal to the attribute values.

        Return (dict): dictionary of ioObjects attribute_name, attributes values.
        """
        return dict(zip(self.CLASS_ATTRIBUTE_NAMES,self._attribute_values))

    def _asList(self):
        """
        Return the ioObject in list format, which is a 1D list of the ioObject's
        attribute values, in the order the ioObject expects them if passed to a class constructor.

        Return (list): 1D list of ioObjects _attribute_values
        """
        return self._attribute_values

    def _asNumpyArray(self):
        """
        Return the ioObject as a numpy array, with the array values being equal to
        what would be returned by the asList() method, and the array cell data types
        being specified by NUMPY_DTYPE class constant.

        Return (numpy.array): numpy array representation of object.
        """
        return N.array([tuple(self._attribute_values),],self.NUMPY_DTYPE)

    def _getRPCInterface(self):
        rpcList=[]
        dlist = dir(self)
        for d in dlist:
            if d[0] is not '_' and d not in ['asNumpyArray',]:
                if callable(getattr(self,d)):
                    rpcList.append(d)
        return rpcList

REALTIME_PRIORITY_CLASS = -18
HIGH_PRIORITY_CLASS = -10

class Computer(object):
    """
    The Computer class does not actually extend the ioHub.devices.Device class.
    However it is sometimes conceptually convenient to think of the Computer class as a type of
    ioHub Device.

    The Computer class manages the ioHub global clock used to synchronize event times
    from all ioHub Devices and ioHub DeviceEvents. This universal timebase can be accessed
    by both the PsychoPy and ioHub Processes.

    .. note:: As of May, 2013 both PsychoPy and ioHub packages implement the
        same timebase. PsychoPy users accustomed to accessing the timebase with
        psychopy.core.getTime() or the default psychopy.logging.defaultClock object
        can also access the timebase with iohub.devices.Computer.getTime. All methods
        access the same timebase without any user-controlled synchronization!

    The Computer class contains methods to allocate the ioHub and PsychoPy
    Process affinities to particular processing units of the computer
    if desired. The operating system priority of either process can also be
    increased.

    .. note:: Setting process affinities and manipulating process priority is not
        currently supported on OS X.

    The Computer class also has methods to monitor current Computer memory
    and CPU usage. The psutil Process object can access
    process level memory, CPU, thread count, disk, and network utilization.

    The Computer class contains only static or class level methods, so an instance
    of the Computer class does **not** need to be explicitly created. The Computer
    device can be accessed via the Computer class alone (using 'iohub.devices.Computer')
    or using the 'self.devices.computer' attribute of the ioHubExperimentRuntime
    class.
    """
    _nextEventID=1

    #: True if the current process is the ioHub Server Process. False if the
    #: current process is the Experiment Runtime Process.
    is_iohub_process=False

    #: If Computer class is on the iohub server process, psychopy_process is
    #: the psychopy process created from the pid passed to iohub on startup.
    #: The iohub server checks that this process exists
    #: (server.checkForPsychopyProcess()) and shuts down if it does not.
    psychopy_process = None

    #: True if the current process is currently in high or real-time priority mode
    #: (enabled by calling Computer.enableHighPriority() or Computer.enableRealTimePriority() )
    #: False otherwise.
    in_high_priority_mode=False

    #: A iohub.MonotonicClock class instance used as the common time base for all devices
    #: and between the ioHub Server and Experiment Runtime Process. Do not
    #: access this class directly, instead use the Computer.getTime()
    #: and associated method name alias's to actually get the current ioHub time.
    global_clock=monotonicClock

    #: The name of the current operating system Python is running on.
    system=sys.platform

    #: Attribute representing the number of *processing units* available on the current computer.
    #: This includes cpu's, cpu cores, and hyperthreads. Notes:
    #:      * processing_unit_count = num_cpus*num_cores_per_cpu*num_hyperthreads.
    #:      * For single core CPU's,  num_cores_per_cpu = 1.
    #:      * For CPU's that do not support hyperthreading,  num_hyperthreads = 1, otherwise num_hyperthreads = 2.
    try:
        processing_unit_count = psutil.cpu_count()
        core_count = psutil.cpu_count(False) #hyperthreads not included
    except AttributeError:
        # psutil might be too old (cpu_count added in 2.0)
        import multiprocessing
        processing_unit_count = multiprocessing.cpu_count()
        core_count = None  # but not used anyway

    #: Access to the psutil.Process class for the current system Process.
    current_process = psutil.Process()

    #: The OS process ID of the ioHub Process.
    iohub_process_id=None

    #: The psutil Process object for the ioHub Process.
    iohub_process=None

    try:
        _process_original_nice_value=psutil.Process().nice() # used on linux.
    except TypeError:
        # on older versions of psutil (in ubuntu 14.04) nice is attr not call
        _process_original_nice_value=psutil.Process().nice

    def __init__(self):
        print2err("WARNING: Computer is a static class, no need to create an instance. just use Computer.xxxxxx")


    @staticmethod
    def getProcessPriority(proc=None):
        """
        **Deprecated Method:** Use Computer.getPriority() instead.

        :param proc:
        :return: success(bool)
        """

        if proc is None:
            proc = psutil.Process()
        proc_priority = proc.nice()
        if Computer.system == 'win32':
            if proc_priority == psutil.HIGH_PRIORITY_CLASS:
                return 'high'
            if proc_priority == psutil.REALTIME_PRIORITY_CLASS:
                return 'realtime'
            if proc_priority == psutil.NORMAL_PRIORITY_CLASS:
                return 'normal'
        else:
            if proc_priority <= REALTIME_PRIORITY_CLASS:
                return 'realtime'
            if proc_priority <= HIGH_PRIORITY_CLASS:
                return 'high'
            if proc_priority == Computer._process_original_nice_value:
                return 'normal'
        return proc_priority

    @staticmethod
    def getPriority():
        """
        Returns the current processes priority as a string.

        This method is not supported on OS X.

        :return: 'normal', 'high', or 'realtime'
        """
        return Computer.getProcessPriority()

    @staticmethod
    def setPriority(level='normal', disable_gc=False):
        """
        Attempts to change the current processes priority based on level.
        Supported levels are:

          * 'normal': sets the current process priority to NORMAL_PRIORITY_CLASS on Windows, or to the processes original nice value on Linux.
          * 'high': sets the current process priority to HIGH_PRIORITY_CLASS on Windows, or to a nice value of -10 value on Linux.
          * 'realtime': sets the current process priority to REALTIME_PRIORITY_CLASS on Windows, or to a nice value of -18 value on Linux.

        If level is 'normal', Python GC is also enabled.
        If level is 'high' or 'realtime', and disable_gc is True, then the Python garbage collection (GC) thread is suspended.

        This method is not supported on OS X.

        :return: Priority level of process when method returns.
        """
        if level.lower() == 'normal':
            Computer.disableRealTimePriority()
        elif level.lower() == 'high':
            Computer.enableHighPriority(disable_gc)
        elif level.lower() == 'realtime':
            Computer.enableRealTimePriority(disable_gc)

        return Computer.getPriority()

    @staticmethod
    def enableHighPriority(disable_gc=True):
        """
        **Deprecated Method:** Use Computer.setPriority('high', disable_gc) instead.

        Sets the priority of the current process to high priority
        and optionally (default is true) disable the python GC. This is very
        useful for the duration of a trial, for example, where you enable at
        start of trial and disable at end of trial.

        On Linux, the process is set to a nice level of -10.

        This method is not supported on OS X.

        Args:
            disable_gc (bool): True = Turn of the Python Garbage Collector. False = Leave the Garbage Collector running. Default: True
        """
        if Computer.in_high_priority_mode is False:
            nice_val = HIGH_PRIORITY_CLASS
            Computer._process_original_nice_value = Computer.current_process.nice()
            if Computer.system=='win32':
                nice_val = psutil.HIGH_PRIORITY_CLASS

            try:
                Computer.current_process.nice(nice_val)
                Computer.in_high_priority_mode=True

                if disable_gc:
                    gc.disable()

            except psutil.AccessDenied:
                print2err("WARNING: Could not increased priority for process {0}".format(Computer.current_process.pid))
                return False
        return True

    @staticmethod
    def enableRealTimePriority(disable_gc=True):
        """
        **Deprecated Method:** Use Computer.setPriority('high', disable_gc) instead.

        Sets the priority of the current process to real-time priority class
        and optionally (default is true) disable the python GC. This is very
        useful for the duration of a trial, for example, where you enable at
        start of trial and disable at end of trial. Note that on Windows 7
        it is not possible to set a process to real-time priority, so high-priority
        is used instead.

        On Linux, the process is set to a nice level of 16.

        This method is not supported on OS X.

        Args:
            disable_gc (bool): True = Turn of the Python Garbage Collector. False = Leave the Garbage Collector running. Default: True
        """
        if Computer.in_high_priority_mode is False:
            nice_val = REALTIME_PRIORITY_CLASS
            Computer._process_original_nice_value = Computer.current_process.nice()
            if Computer.system=='win32':
                nice_val = psutil.REALTIME_PRIORITY_CLASS

            try:
                Computer.current_process.nice(nice_val)
                Computer.in_high_priority_mode=True

                if disable_gc:
                    gc.disable()

            except psutil.AccessDenied:
                print2err("WARNING: Could not increased priority for process {0}".format(Computer.current_process.pid))
                return False
        return True

    @staticmethod
    def disableRealTimePriority():
        """
        **Deprecated Method:** Use Computer.setPriority('normal') instead.

        Sets the priority of the Current Process back to normal priority
        and enables the python GC. In general you would call
        enableRealTimePriority() at start of trial and call
        disableHighPriority() at end of trial.

        On Linux, sets the nice level of the process back to the value being used
        prior to the call to enableRealTimePriority()

        This method is not supported on OS X.

        Return:
            None
        """
        return Computer.disableHighPriority()

    @staticmethod
    def disableHighPriority():
        """
        **Deprecated Method:** Use Computer.setPriority('normal') instead.

        Sets the priority of the Current Process back to normal priority
        and enables the python GC. In general you would call
        enableHighPriority() at start of trial and call
        disableHighPriority() at end of trial.

        On Linux, sets the nice level of the process back to the value being used
        prior to the call to enableHighPriority()

        This method is not supported on OS X.

        Return:
            None
        """
        try:
            if Computer.in_high_priority_mode is True:
                nice_val = Computer._process_original_nice_value
                gc.enable()

                Computer.current_process.nice(nice_val)
                Computer.in_high_priority_mode=False
        except psutil.AccessDenied:
            print2err("WARNING: Could not disable increased priority for process {0}".format(Computer.current_process.pid))
            return False
        return True

    @staticmethod
    def getProcessingUnitCount():
        """
        Return the number of *processing units* available on the current computer.
        Processing Units include: cpu's, cpu cores, and hyper threads.

        Notes:

        * processing_unit_count = num_cpus*num_cores_per_cpu*num_hyperthreads.
        * For single core CPU's,  num_cores_per_cpu = 1.
        * For CPU's that do not support hyperthreading,  num_hyperthreads = 1, otherwise num_hyperthreads = 2.

        Args:
            None

        Returns:
            int: the number of processing units on the computer.
        """

        return Computer.processing_unit_count

    @staticmethod
    def getProcessAffinities():
        """
        Retrieve the current PsychoPy Process affinity list and ioHub Process affinity list.

        For example, on a 2 core CPU with hyper-threading, the possible 'processor'
        list would be [0,1,2,3], and by default both the PsychoPy and ioHub
        Processes can run on any of these 'processors', so::


            psychoCPUs,ioHubCPUS=Computer.getProcessAffinities()
            print psychoCPUs,ioHubCPUS

            >> [0,1,2,3], [0,1,2,3]


        If Computer.setProcessAffinities was used to set the PsychoPy Process to core 1
        (index 0 and 1) and the ioHub Process to core 2 (index 2 and 3),
        with each using both hyper threads of the given core, the set call would look like::


            Computer.setProcessAffinities([0,1],[2,3])

            psychoCPUs,ioHubCPUS=Computer.getProcessAffinities()
            print psychoCPUs,ioHubCPUS

            >> [0,1], [2,3]


        If the ioHub is not being used (i.e self.hub is None), then only the PsychoPy
        Process affinity list will be returned and None will be returned for the
        ioHub Process affinity::

            psychoCPUs,ioHubCPUS=Computer.getProcessAffinities()
            print psychoCPUs,ioHubCPUS

            >> [0,1,2,3], None

        **But in this case, why are you using the ioHub package at all? ;)**

        This method is not supported on OS X.

        Args:
            None

        Returns:
            (list,list) Tuple of two lists: PsychoPy Process affinity ID list and ioHub Process affinity ID list.

        """
        Computer.current_process.cpu_affinity(),Computer.iohub_process.cpu_affinity()

    @staticmethod
    def setProcessAffinities(experimentProcessorList, ioHubProcessorList):
        """
        Sets the processor affinity for the PsychoPy Process and the ioHub Process.

        For example, on a 2 core CPU with hyper-threading, the possible 'processor'
        list would be [0,1,2,3], and by default both the experiment and ioHub
        server processes can run on any of these 'processors',
        so to have both processes have all processors available
        (which is the default), you would call::

            Computer.setProcessAffinities([0,1,2,3], [0,1,2,3])

            # check the process affinities
            psychoCPUs,ioHubCPUS=Computer.getProcessAffinities()
            print psychoCPUs,ioHubCPUS

            >> [0,1,2,3], [0,1,2,3]

        based on the above CPU example.

        If setProcessAffinities was used to set the experiment process to core 1
        (index 0,1) and the ioHub server process to core 2 (index 2,3), with
        each using both hyper threads of the given core, the set call would look
        like::

            Computer.setProcessAffinities([0,1],[2,3])

            # check the process affinities
            psychoCPUs,ioHubCPUS=Computer.getProcessAffinities()
            print psychoCPUs,ioHubCPUS

            >> [0,1], [2,3]

        Args:
           experimentProcessorList (list): list of int processor ID's to set the PsychoPy Process affinity to. An empty list means all processors.

           ioHubProcessorList (list): list of int processor ID's to set the ioHub Process affinity to. An empty list means all processors.

        Returns:
           None
        """
        Computer.current_process.cpu_affinity(experimentProcessorList)
        Computer.iohub_process.cpu_affinity(ioHubProcessorList)

    @staticmethod
    def autoAssignAffinities():
        """
        Auto sets the PsychoPy Process and ioHub Process affinities
        based on some very simple logic.

        It is not known at this time if the implementation of this method makes
        any sense in terms of actually improving performance. Field tests and
        feedback will need to occur, based on which the algorithm can be improved.

        Currently:

        * If the system is detected to have 1 processing unit, or greater than 8 processing units, nothing is done by the method.
        * For a system that has two processing units, the PsychoPy Process is assigned to index 0, ioHub Process assigned to 1.
        * For a system that has four processing units, the PsychoPy Process is assigned to index's 0,1 and the ioHub Process assigned to 2,3.
        * For a system that has eight processing units, the PsychoPy Process is assigned to index 2,3, ioHub Process assigned to 4,5. All other processes running on the OS are attempted to be assigned to indexes 0,1,6,7.

        Args:
            None

        Returns:
            None
        """
        cpu_count=Computer.processing_unit_count
        if cpu_count == 2:
            #print 'Assigning experiment process to CPU 0, ioHubServer process to CPU 1'
            Computer.setProcessAffinities([0,],[1,])
        elif cpu_count == 4:
            #print 'Assigning experiment process to CPU 0,1, ioHubServer process to CPU 2,3'
            Computer.setProcessAffinities([0,1],[2,3])
        elif cpu_count == 8:
            #print 'Assigning experiment process to CPU 2,3, ioHubServer process to CPU 4,5, attempting to assign all others to 0,1,6,7'
            Computer.setProcessAffinities([2,3],[4,5])
            Computer.setAllOtherProcessesAffinity([0,1,6,7],[Computer.currentProcessID,Computer.iohub_process_id])
        else:
            print "autoAssignAffinities does not support %d processors."%(cpu_count,)

    @staticmethod
    def getCurrentProcessAffinity():
        """
        Returns a list of 'processor' ID's (from 0 to Computer.processing_unit_count-1)
        that the current (calling) process is able to run on.

        Args:
            None

        Returns:
            None
        """
        return Computer.current_process.cpu_affinity()

    @staticmethod
    def setCurrentProcessAffinity(processorList):
        """
        Sets the list of 'processor' ID's (from 0 to Computer.processing_unit_count-1)
        that the current (calling) process should only be allowed to run on.

        Args:
           processorList (list): list of int processor ID's to set the current Process affinity to. An empty list means all processors.

        Returns:
            None

        """
        return Computer.current_process.cpu_affinity(processorList)

    @staticmethod
    def setProcessAffinityByID(process_id,processor_list):
        """
        Sets the list of 'processor' ID's (from 0 to Computer.processing_unit_count-1)
        that the process with the provided OS Process ID is able to run on.

        Args:
           processID (int): The system process ID that the affinity should be set for.

           processorList (list): list of int processor ID's to set process with the given processID too. An empty list means all processors.

        Returns:
            None
        """
        p=psutil.Process(process_id)
        return p.cpu_affinity(processor_list)

    @staticmethod
    def getProcessAffinityByID(process_id):
        """
        Returns a list of 'processor' ID's (from 0 to Computer.processing_unit_count-1)
        that the process with the provided processID is able to run on.

        Args:
           processID (int): The system process ID that the affinity should be set for.

        Returns:
           processorList (list): list of int processor ID's to set process with the given processID too. An empty list means all processors.
        """
        p=psutil.Process(process_id)
        return p.cpu_affinity()

    @staticmethod
    def setAllOtherProcessesAffinity(processor_list, exclude_process_id_list=[]):
        """
        Sets the affinity for all OS Processes other than those specified in the
        exclude_process_id_list, to the processing unit indexes specified in processor_list.
        Valid values in the processor_list are between 0 to Computer.processing_unit_count-1.

        exclude_process_id_list should be a list of OS Process ID integers,
        or an empty list (indicating to set the affiinty to all processing units).

        Note that the OS may not allow the calling process to set the affinity
        of every other process running on the system. For example, some system
        level processing can not have their affinity set by a user level application.

        However, in general, many processes can have their affinity set by another user process.

        Args:
           processor_list (list): list of int processor ID's to set all OS Processes to. An empty list means all processors.

           exclude_process_id_list (list):  A list of process ID's that should not have their process affinity settings changed.

        Returns:
           None
        """
        for p in psutil.pids():
            if p not in exclude_process_id_list:
                try:
                    psutil.Process(p).cpu_affinity(processor_list)
                except Exception:
                    pass

    @staticmethod
    def currentTime():
        """
        Alias for Computer.currentSec()
        """
        return Computer.global_clock.getTime()

    @staticmethod
    def currentSec():
        """
        Returns the current sec.msec-msec time of the system.

        The underlying timer that is used is based on OS and Python version.
        Three requirements exist for the ioHub time base implementation:

        * The Python interpreter does not apply an offset to the times returned based on when the timer module being used was loaded or when the timer fucntion first called was first called.
        * The timer implementation used must be monotonic and report elapsed time between calls, 'not' CPU usage time.
        * The timer implementation must provide a resolution of 50 usec or better.

        Given the above requirements, ioHub selects a timer implementation as follows:

        * On Windows, the Windows Query Performance Counter API is used using ctypes access.
        * On other OS's, if the Python version being used is 2.6 or lower, time.time is used. For Python 2.7 and above, the timeit.default_timer function is used.

        Args:
           None

        Returns:
           None
        """

        return Computer.global_clock.getTime()

    @staticmethod
    def getTime():
        """
        Alias for Computer.currentSec()
        """
        return Computer.global_clock.getTime()

    @staticmethod
    def _getNextEventID():
        n = Computer._nextEventID
        Computer._nextEventID+=1
        return n

    @staticmethod
    def getPhysicalSystemMemoryInfo():
        """
        Return a class containing information about current memory usage.

        Args:
           None

        Returns:
           vmem: (total=long, available=long, percent=float, used=long, free=long)

        Where:

        * vmem.total: the total amount of memory in bytes.
        * vmem.available: the available amount of memory in bytes.
        * vmem.percent: the percent of memory in use by the system.
        * vmem.used: the used amount of memory in bytes.
        * vmem.free: the amount of memory that is free in bytes.On Windows, this is the same as vmem.available.
        """
        m= psutil.virtual_memory()
        return m

    @staticmethod
    def getCPUTimeInfo(percpu=False):
        """
        Return a float representing the current CPU utilization as a percentage.

        Args:
           percpu (bool): If True, a list of cputimes objects is returned,
                          one for each processing unit for the computer.
                          If False, only a single cputimes object is returned.
        Returns:
           object: (user=float, system=float, idle=float)
        """
        return psutil.cpu_times_percent(percpu=percpu)


    @staticmethod
    def getCurrentProcess():
        """
        Get the current / Local process.

        On Windows and Linux, this is a psutil.Process class instance.

        Args:
           None

        Returns:
           object: Process object for the current system process.
        """
        return Computer.current_process


    @staticmethod
    def getIoHubProcess():
        """
        Get the ioHub Process.

        On Windows and Linux, this is a psutil.Process class instance.

        Args:
           None

        Returns:
           object: Process object for the ioHub Process.
        """
        return Computer.iohub_process

########### Base Abstract Device that all other Devices inherit from ##########
class Device(ioObject):
    """
    The Device class is the base class for all ioHub Device types.
    Any ioHub Device class (i.e Keyboard, Mouse, etc)
    also include the methods and attributes of this class.
    """
    DEVICE_USER_LABEL_INDEX=0
    DEVICE_NUMBER_INDEX=1
    DEVICE_MANUFACTURER_NAME_INDEX=2
    DEVICE_MODEL_NAME_INDEX=3
    DEVICE_MODEL_NUMBER_INDEX=4
    DEVICE_SOFTWARE_VERSION_INDEX=5
    DEVICE_HARDWARE_VERSION_INDEX=6
    DEVICE_FIRMWARE_VERSION_INDEX=7
    DEVICE_SERIAL_NUMBER_INDEX=8
    DEVICE_BUFFER_LENGTH_INDEX=9
    DEVICE_MAX_ATTRIBUTE_INDEX=9

    # Multiplier to use to convert this devices event time stamps to sec format.
    # This is set by the author of the device class or interface implementation.
    DEVICE_TIMEBASE_TO_SEC=1.0

    _baseDataTypes=ioObject._baseDataTypes
    _newDataTypes=[
                   ('name',N.str,24),           # The name given to this device instance. User Defined. Should be
                                                # unique within all devices of the same type_id for a given experiment.
                   ('device_number', N.uint8),  # For devices that support multiple connected to the computer at once, with some devices the device_number can be used to select which device ot use.
                   ('manufacturer_name',N.str_,64), # The name of the manufacturer for the device being used.
                   ('model_name',N.str_,32),    # The string name of the device model being used. Some devices support different models.
                   ('model_number',N.str_,32),    # The device model number being used. Some devices support different models.
                   ('software_version',N.str_,8), # Used to optionally store the devices software / API version being used by the ioHub Device
                   ('hardware_version',N.str_,8), # Used to optionally store the devices hardware version
                   ('firmware_version',N.str_,8), # Used to optionally store the devices firmware
                   ('serial_number',N.str_,32),    # The serial number for the device being used. Serial numbers 'should' be unique across all devices of the same brand and model.
                   ('manufacture_date',N.str_,10),    # The serial number for the device being used. Serial numbers 'should' be unique across all devices of the same brand and model.
                   ('event_buffer_length',N.uint16) # The maximum size of the device level event buffer for this
                                                        # device instance. If the buffer becomes full, when a new event
                                                        # is added, the oldest event in the buffer is removed.
                ]

    EVENT_CLASS_NAMES=[]

    _display_device=None
    _iohub_server=None
    next_filter_id = 1
    DEVICE_TYPE_ID=None
    DEVICE_TYPE_STRING=None

    __slots__=[e[0] for e in _newDataTypes]+['_native_event_buffer',
                                            '_event_listeners',
                                            '_iohub_event_buffer',
                                            '_last_poll_time',
                                            '_last_callback_time',
                                            '_is_reporting_events',
                                            '_configuration',
                                            'monitor_event_types',
                                            '_filters']

    def __init__(self,*args,**kwargs):
        #: The user defined name given to this device instance. A device name must be
        #: unique for all devices of the same type_id in a given experiment.
        self.name=None

        #: For device classes that support having multiple of the same type
        #: being monitored by the ioHub Process at the same time (for example XInput gamepads),
        #: device_number is used to indicate which of the connected devices of that
        #: type a given ioHub Device instance should connect to.
        self.device_number=None

        #: The maximum size ( in event objects ) of the device level event buffer for this
        #: device instance. If the buffer becomes full, when a new event
        #: is added, the oldest event in the buffer is removed.
        self.event_buffer_length=None

        #: A list of event class names that can be generated by this device type
        #: and should be monitored and reported by the ioHub Process.
        self.monitor_event_types=None

        #: The name of the manufacturer of the device.
        self.manufacturer_name=None

        #: The model of this Device subclasses instance. Some Device types
        #: explicitedly support different models of the device and use different
        #: logic in the ioHub Device implementation based on the model_name given.
        self.model_name=None

        #: Model number can be optionally used to hold the specific model number
        #: specified on the device.
        self.model_number=None

        #: The software version attribute can optionally be used to store the
        #: devices software / API version being used by the ioHub Device
        self.software_version=None

        #: The hardware version attribute can optionally be used to store the
        #: physical devices hardware version / revision.
        self.hardware_version=None

        #: The firmware version attribute can optionally be used to store the
        #: physical devices hardware version / revision.
        self.firmware_version=None

        #: The unique serial number of the specific device instance being used,
        #: if applicable.
        self.serial_number=None

        #: The manufactured date of the specific device instance being used,
        #: if applicable.(Use DD-MM-YYYY string format.)
        self.manufacture_date=None


        ioObject.__init__(self, *args, **kwargs)

        self._is_reporting_events = kwargs.get('auto_report_events', False)
        self._iohub_event_buffer = dict()
        self._event_listeners = dict()
        self._configuration = kwargs
        self._last_poll_time = 0
        self._last_callback_time = 0
        self._native_event_buffer = deque(maxlen=self.event_buffer_length)
        self._filters = dict()

    def getConfiguration(self):
        """
        Retrieve the configuration settings information used to create the device instance.
        This will be a combination of the default settings for the device
        (found in iohub.devices.<device_name>.default_,defice_name>.yaml, plus any
        device settings specified by the experiment author within an
        iohub_config.yaml file if the ioHubExperimentRuntime is being used
        to define the experiment logic, or if using the iohub.launchHubProcess()
        function in the experriment script, as device settings in dictionary form.

        Changing any values in the returned dictionary has no effect on the device state.

        Args:
            None

        Returns:
            (dict): The dictionary of the device configuration settings used to create the device.
        """
        return self._configuration

    def getEvents(self,*args,**kwargs):
        """
        Retrieve any DeviceEvents that have occurred since the last call to the
        device's getEvents() or clearEvents() methods.

        Note that calling getEvents() at a device level does not change the Global Event Buffer's
        contents.

        Args:
            event_type_id (int): If specified, provides the ioHub DeviceEvent ID for which events should be returned for.  Events that have occurred but do not match the event ID specified are ignored. Event type ID's can be accessed via the EventConstants class; all available event types are class atttributes of EventConstants.

            clearEvents (int): Can be used to indicate if the events being returned should also be removed from the device event buffer. True (the defualt) indicates to remove events being returned. False results in events being left in the device event buffer.

            asType (str): Optional kwarg giving the object type to return events as. Valid values are 'namedtuple' (the default), 'dict', 'list', or 'object'.

        Returns:
            (list): New events that the ioHub has received since the last getEvents() or clearEvents() call to the device. Events are ordered by the ioHub time of each event, older event at index 0. The event object type is determined by the asType parameter passed to the method. By default a namedtuple object is returned for each event.
        """
        self._iohub_server.processDeviceEvents()
        eventTypeID = None
        clearEvents = True
        if len(args)==1:
            eventTypeID=args[0]
        elif len(args)==2:
            eventTypeID=args[0]
            clearEvents=args[1]

        if eventTypeID is None:
            eventTypeID=kwargs.get('event_type_id',None)
            if eventTypeID is None:
                eventTypeID=kwargs.get('event_type',None)
        clearEvents=kwargs.get('clearEvents',True)

        filter_id=kwargs.get('filter_id',None)

        currentEvents=[]
        if eventTypeID:
            currentEvents=list(self._iohub_event_buffer.get(eventTypeID,[]))

            if filter_id:
                currentEvents = [e for e in currentEvents if e[DeviceEvent.EVENT_FILTER_ID_INDEX] == filter_id]

            if clearEvents is True and len(currentEvents)>0:
                self.clearEvents(eventTypeID,filter_id=filter_id, call_proc_events=False)
        else:
            if filter_id:
                [currentEvents.extend([fe for fe in l if fe[DeviceEvent.EVENT_FILTER_ID_INDEX] == filter_id]) for l in self._iohub_event_buffer.values()]
            else:
                [currentEvents.extend(l) for l in self._iohub_event_buffer.values()]

            if clearEvents is True and len(currentEvents)>0:
                self.clearEvents(filter_id=filter_id, call_proc_events=False)

        if len(currentEvents)>0:
            currentEvents=sorted(currentEvents, key=itemgetter(DeviceEvent.EVENT_HUB_TIME_INDEX))
        return currentEvents


    def clearEvents(self, event_type=None, filter_id=None, call_proc_events=True):
        """
        Clears any DeviceEvents that have occurred since the last call to the device's getEvents(),
        or clearEvents() methods.

        Note that calling clearEvents() at the device level only clears the
        given device's event buffer. The ioHub Process's Global Event Buffer
        is unchanged.

        Args:
            None

        Returns:
            None
        """
        if call_proc_events:
            self._iohub_server.processDeviceEvents()

        if event_type:
            if filter_id:
                event_que = self._iohub_event_buffer[event_type]
                newque = deque([e for e in event_que if e[DeviceEvent.EVENT_FILTER_ID_INDEX] != filter_id], maxlen=self.event_buffer_length)
                self._iohub_event_buffer[event_type] = newque
            else:
                self._iohub_event_buffer.setdefault(event_type,
                                deque(maxlen=self.event_buffer_length)).clear()
        else:
            if filter_id:
                for event_type, event_deque in self._iohub_event_buffer.items():
                    newque = deque([e for e in event_deque if e[DeviceEvent.EVENT_FILTER_ID_INDEX] != filter_id], maxlen=self.event_buffer_length)
                    self._iohub_event_buffer[event_type] = newque
            else:
                self._iohub_event_buffer.clear()

    def enableEventReporting(self,enabled=True):
        """
        Specifies if the device should be reporting events to the ioHub Process
        (enabled=True) or whether the device should stop reporting events to the
        ioHub Process (enabled=False).


        Args:
            enabled (bool):  True (default) == Start to report device events to the ioHub Process. False == Stop Reporting Events to the ioHub Process. Most Device types automatically start sending events to the ioHUb Process, however some devices like the EyeTracker and AnlogInput device's do not. The setting to control this behavour is 'auto_report_events'

        Returns:
            bool: The current reporting state.
        """
        self.clearEvents()
        self._is_reporting_events=enabled
        return self._is_reporting_events

    def isReportingEvents(self):
        """
        Returns whether a Device is currently reporting events to the ioHub Process.

        Args: None

        Returns:
            (bool): Current reporting state.
        """
        return self._is_reporting_events

    def addFilter(self, filter_file_path, filter_class_name, kwargs):
        """
        Take the filter_file_path and add the filters module dir to sys.path
        if it does not already exist.

        Then import the filter module (file) class based on filter_class_name.
        Create a filter instance, and add it to the _filters dict:

        self._filters[filter_file_path+'.'+filter_class_name]

        :param filter_path:
        :return:
        """
        try:
            import importlib
            from psychopy.iohub import EventConstants, convertCamelToSnake

            filter_file_path = os.path.normpath(os.path.abspath(filter_file_path))
            fdir, ffile = os.path.split(filter_file_path)
            if not ffile.endswith(".py"):
                ffile = ffile+".py"
            if os.path.isdir(fdir) and os.path.exists(filter_file_path):
                if fdir not in sys.path:
                    sys.path.append(fdir)

                # import module using ffile
                filter_module = importlib.import_module(ffile[:-3])

                # import class filter_class_name
                filter_class = getattr(filter_module, filter_class_name, None)
                if filter_class is None:
                    print2err("Can not create Filter, filter class not found")
                    return -1
                else:
                    # Create instance of class
                    # For now, just use a class level counter.
                    filter_class_instance = filter_class(**kwargs)
                    filter_class_instance._parent_device_type = self.DEVICE_TYPE_ID
                    # Add to filter list for device
                    filter_key = filter_file_path+'.'+filter_class_name
                    filter_class_instance._filter_key = filter_key
                    self._filters[filter_key] = filter_class_instance
                    return filter_class_instance.filter_id

            else:
                print2err("Could not add filter . File not found.")
            return -1
        except Exception:
            printExceptionDetailsToStdErr()
            print2err("ERROR During Add Filter")

    def removeFilter(self, filter_file_path, filter_class_name):
        filter_key = filter_file_path+'.'+filter_class_name
        if filter_key in self._filters:
            del self._filters[filter_key]
            return True
        return False

    def resetFilter(self,filter_file_path, filter_class_name):
        filter_key = filter_file_path+'.'+filter_class_name
        if filter_key in self._filters:
            self._filters[filter_key].reset()
            return True
        return False

    def enableFilters(self,yes=True):
        for f in self._filters.values():
            f.enable = yes

    def _handleEvent(self,e):
        event_type_id = e[DeviceEvent.EVENT_TYPE_ID_INDEX]
        self._iohub_event_buffer.setdefault(event_type_id,
                               deque(maxlen=self.event_buffer_length)).append(e)

        # Add the event to any filters bound to the device which
        # list wanting the event's type and events filter_id
        input_evt_filter_id = e[DeviceEvent.EVENT_FILTER_ID_INDEX]
        for event_filter in self._filters.values():
            if event_filter.enable is True:
                current_filter_id = event_filter.filter_id
                if current_filter_id != input_evt_filter_id:
                    # stops circular event processing
                    evt_filter_ids= event_filter.input_event_types.get(event_type_id, [])
                    if input_evt_filter_id in evt_filter_ids:
                        event_filter._addInputEvent(copy.deepcopy(e))

    def _getNativeEventBuffer(self):
        return self._native_event_buffer

    def _addNativeEventToBuffer(self,e):
        if self.isReportingEvents():
            self._native_event_buffer.append(e)

    def _addEventListener(self,l,eventTypeIDs):
        for ei in eventTypeIDs:
            self._event_listeners.setdefault(ei,[]).append(l)

    def _removeEventListener(self,l):
        for etypelisteners in self._event_listeners.values():
            if l in etypelisteners:
                etypelisteners.remove(l)

    def _getEventListeners(self,forEventType):
        return self._event_listeners.get(forEventType,[])

    def getCurrentDeviceState(self, clear_events=True):
        result_dict={}
        self._iohub_server.processDeviceEvents()
        events = {key:tuple(value) for key, value in self._iohub_event_buffer.items()}
        result_dict['events'] = events
        if clear_events:
            self.clearEvents(call_proc_events=False)

        result_dict['reporting_events'] = self._is_reporting_events

        return result_dict

    def resetState(self):
        self.clearEvents()

    def _poll(self):
        """
        The _poll method is used when an ioHub Device needs to periodically
        check for new events received from the native device / device API.
        Normally this means that the native device interface is using some
        data buffer or queue for new device events until the ioHub Device
        reads them.

        The ioHub Device can *poll* and check for any new events that
        are available, retrieve the new events, and process them
        to create ioHub Events as necessary. Each subclass of ioHub.devives.Device
        that wishes to use event polling **must** override the _poll method
        in the Device classes implementation. The configuration section of the
        iohub_config.yaml for the device **must** also contain the device_timer: interval
        parameter as explained below.

        .. note::
            When an event is created by an ioHub Device, it is represented in
            the form of an ordered list, where the number of elements in the
            list equals the number of public attributes of the event, and the order
            of the element values matches the order that the values would be provided
            to the constructor of the associated DeviceEvent class. This list format
            keeps internal event representation overhead (both in terms of creation
            time and memory footprint) to a minimum. The list event format
            also allows for the most compact representation of the event object
            when being transferred between the ioHub and Experiment processes.

            The ioHub Process can convert these list event representations to
            one of several, user-friendly, object formats ( namedtuple [default], dict, or the correct
            ioHub.devices.DeviceEvent subclass. ) for use within the experiment script.

        If an ioHub Device uses polling to check for new device events, the ioHub
        device configuration must include the following property in the devices
        section of the iohub_config.yaml file for the experiment:

            device_timer:
                interval: sec.msec

        The device_timer.interval preference informs ioHub how often the Device._poll
        method should be called while the Device is running.

        For example:

            device_timer:
                interval: 0.01

        indicates that the Device._poll method should ideally be called every 10 msec
        to check for any new events received by the device hardware interface. The
        correct or optimal value for device_timer.interval depends on the device
        type and the expected rate of device events. For devices that receive events
        rapidly, for example at an average rate of 500 Hz or more, or for devices
        that do not provide native event time stamps (and the ioHub Process must
        time stamp the event) the device_timer.interval should be set to 0.001 (1 msec).

        For devices that receive events at lower rates and have native time stamps
        that are being converted to the ioHub time base, a slower polling rate is
        usually acceptable. A general suggestion would be to set the device_timer.interval
        to be equal to two to four times the expected average event input rate in Hz,
        but not exceeding a device_timer.interval 0.001 seconds (a polling rate of 1000 Hz).
        For example, if a device sends events at an average rate of 60 Hz,
        or once every 16.667 msec, then the polling rate could be set to the
        equivelent of a 120 - 240 Hz. Expressed in sec.msec format,
        as is required for the device_timer.interval setting, this would equal about
        0.008 to 0.004 seconds.

        Of course it would be ideal if every device that polled for events was polling
        at 1000 to 2000 Hz, or 0.001 to 0.0005 msec, however if too many devices
        are requested to poll at such high rates, all will suffer in terms of the
        actual polling rate achieved. In devices with slow event output rates,
        such high polling rates will result in many calls to Device._poll that do
        not find any new events to process, causing extra processing overhead that
        is not needed in many cases.

        Args:
            None

        Returns:
            None
        """
        pass

    def _handleNativeEvent(self,*args,**kwargs):
        """
        The _handleEvent method can be used by the native device interface (implemented
        by the ioHub Device class) to register new native device events
        by calling this method of the ioHub Device class.

        When a native device interface uses the _handleNativeEvent method it is
        employing an event callback approach to notify the ioHub Process when new
        native device events are available. This is in contrast to devices that use
        a polling method to check for new native device events, which would implement
        the _poll() method instead of this method.

        Generally speaking this method is called by the native device interface
        once for each new event that is available for the ioHub Process. However,
        with good cause, there is no reason why a single call to this
        method could not handle multiple new native device events.

        .. note::
            If using _handleNativeEvent, be sure to remove the device_timer
            property from the devices configuration section of the iohub_config.yaml.

        Any arguments or kwargs passed to this method are determined by the ioHub
        Device implementation and should contain all the information needed to create
        an ioHub Device Event.

        Since any callbacks should take as little time to process as possible,
        a two stage approach is used to turn a native device event into an ioHub
        Device event representation:
            #. This method is called by the native device interface as a callback, providing the necessary information to be able to create an ioHub event. As little processing should be done in this method as possible.
            #. The data passed to this method, along with the time the callback was called, are passed as a tuple to the Device classes _addNativeEventToBuffer method.
            #. During the ioHub Servers event processing routine, any new native events that have been added to the ioHub Server using the _addNativeEventToBuffer method are passed individually to the _getIOHubEventObject method, which must also be implemented by the given Device subclass.
            #. The _getIOHubEventObject method is responsible for the actual conversion of the native event representation to the required ioHub Event representation for the accociated event type.

        Args:
            args(tuple): tuple of non keyword arguements passed to the callback.

        Kwargs:
            kwargs(dict): dict of keyword arguements passed to the callback.

        Returns:
            None
        """
        return False

    def _getIOHubEventObject(self,native_event_data):
        """
        The _getIOHubEventObject method is called by the ioHub Process to convert
        new native device event objects that have been received to the appropriate
        ioHub Event type representation.

        If the ioHub Device has been implemented to use the _poll() method of checking for
        new events, then this method simply should return what it is passed, and is the
        default implementation for the method.

        If the ioHub Device has been implemented to use the event callback method
        to register new native device events with the ioHub Process, then this method should be
        overwritten by the Device subclass to convert the native event data into
        an appropriate ioHub Event representation. See the implementation of the
        Keyboard or Mouse device classes for an example of such an implementation.

        Args:
            native_event_data: object or tuple of (callback_time, native_event_object)

        Returns:
            tuple: The appropriate ioHub Event type in list form.
        """
        return native_event_data


    def _close(self):
        try:
            self.__class__._iohub_server=None
            self.__class__._display_device=None
        except Exception:
            pass

    def __del__(self):
        self._close()

########### Base Device Event that all other Device Events inherit from ##########

class DeviceEvent(ioObject):
    """
    The DeviceEvent class is the base class for all ioHub DeviceEvent types.

    Any ioHub DeviceEvent class (i.e MouseMoveEvent, MouseScrollEvent, MouseButtonPressEvent,
    KeyboardPressEvent, KeyboardReleaseEvent, etc.) also has access to the
    methods and attributes of the DeviceEvent class.
    """
    EVENT_EXPERIMENT_ID_INDEX=0
    EVENT_SESSION_ID_INDEX=1
    DEVICE_ID_INDEX=2
    EVENT_ID_INDEX=3
    EVENT_TYPE_ID_INDEX=4
    EVENT_DEVICE_TIME_INDEX=5
    EVENT_LOGGED_TIME_INDEX=6
    EVENT_HUB_TIME_INDEX=7
    EVENT_CONFIDENCE_INTERVAL_INDEX=8
    EVENT_DELAY_INDEX=9
    EVENT_FILTER_ID_INDEX=10
    BASE_EVENT_MAX_ATTRIBUTE_INDEX=EVENT_FILTER_ID_INDEX

    # The Device Class that generates the given type of event.
    PARENT_DEVICE=None

    # The string label for the given DeviceEvent type. Should be usable to get Event type
    #  from ioHub.EventConstants.getName(EVENT_TYPE_STRING), the value of which is the
    # event type id. This is set by the author of the event class implementation.
    EVENT_TYPE_STRING='UNDEFINED_EVENT'

    # The type id int for the given DeviceEvent type. Should be one of the int values in
    # ioHub.EventConstants.EVENT_TYPE_ID. This is set by the author of the event class implementation.
    EVENT_TYPE_ID=0


    _baseDataTypes=ioObject._baseDataTypes
    _newDataTypes=[
                ('experiment_id',N.uint32), # The ioDataStore experiment ID assigned to the experiment code
                                            # specified in the experiment configuration file for the experiment.

                ('session_id',N.uint32),    # The ioDataStore session ID assigned to the currently running
                                            # experiment session. Each time the experiment script is run,
                                            # a new session id is generated for use within the hdf5 file.

                ('device_id',N.uint16),     # The unique id assigned to the device that generated the event.
                                            # CUrrrently not used, but will be in the future for device types that
                                            # support > one instance of that device type to be enabled
                                            # during an experiment. Currenly only one device of a given type
                                            #can be used in an experiment.

                ('event_id',N.uint32),      # The id assigned to the current device event instance. Every device
                                            # event generated by monitored devices during an experiment session is
                                            # assigned a unique id, starting from 0 for each session, incrementing
                                            # by +1 for each new event.

                ('type',N.uint8),           # The type id for the event. This is used to create DeviceEvent objects
                                            # or dictionary representations of an event based on the data from an
                                            # event value list.

                ('device_time',N.float32),   # If the device that generates the given device event type also time stamps
                                            # events, this field is the time of the event as given by the device,
                                            # converted to sec.msec-usec for consistancy with all other ioHub device times.
                                            # If the device that generates the given event type does not time stamp
                                            # events, then the device_time is set to the logged_time for the event.

                ('logged_time', N.float32),  # The sec time that the event was 'received' by the ioHub Server Process.
                                            # For devices that poll for events, this is the sec time that the poll
                                            # method was called for the device and the event was retrieved. For
                                            # devices that use the event callback, this is the sec time the callback
                                            # executed and accept the event. Time is in sec.msec-usec

                ('time',N.float32),         # Time is in the normalized time base that all events share,
                                            # regardless of device type. Time is calculated differently depending
                                            # on the device and perhaps event type.
                                            # Time is what should be used when comparing times of events across
                                            # different devices. Time is in sec.msec-usec.

                ('confidence_interval', N.float32), # This property attempts to give a sense of the amount to which
                                                    # the event time may be off relative to the true time the event
                                                    # occurred. confidence_interval is calculated differently depending
                                                    # on the device and perhaps event types. In general though, the
                                                    # smaller the confidence_interval, the more likely it is that the
                                                    # calculated time of the event is correct. For devices where
                                                    # a realistic confidence_interval can not be calculated,
                                                    # for example if the event device delay is unknown, then a value
                                                    # of -1.0 should be used. Valid confidence_interval values are
                                                    # in sec.msec-usec and will range from 0.000000 sec.msec-usec
                                                    # and higher.

                ('delay',N.float32)  ,       # The delay of an event is the known (or estimated) delay from when the
                                            # real world event occurred to when the ioHub received the event for
                                            # processing. This is often called the real-time end-to-end delay
                                            # of an event. If the delay for an event can not be reasonably estimated
                                            # or is not known, a delay of -1.0 is set. Delays are in sec.msec-usec
                                            # and valid values will range from 0.000000 sec.msec-usec and higher.

                ('filter_id',N.int16)       # The filter identifier that the event passed through before being saved.
                                            # If the event did not pass through any filter devices, then the value will be 0.
                                            # Otherwise, the value is the | combination of the filter set that the
                                            # event passed through before being made available to the experiment,
                                            # or saved to the ioDataStore. The filter id can be used to determine
                                            # which filters an event was handled by, but not the order in which handling was done.
                                            # Default value is 0.
                ]

    # The name of the hdf5 table used to store events of this type in the ioDataStore pytables file.
    # This is set by the author of the event class implementation.
    IOHUB_DATA_TABLE=None

    __slots__=[e[0] for e in _newDataTypes]

    def __init__(self,*args,**kwargs):
        #: The ioHub DataStore experiment ID assigned to the experiment that is running when the event is collected.
        #: 0 indicates no experiment has been defined.
        self.experiment_id=None

        #: The ioHub DataStore session ID assigned for teh current experiment run.
        #: Each time the experiment script is run, a new session id is generated for use
        #: by the ioHub DataStore within the hdf5 file.
        self.session_id=None

        self.device_id=None

        #: The id assigned to the current event instance. Every device
        #: event generated by the ioHub Process is assigned a unique id,
        #: starting from 0 for each session, incrementing by +1 for each new event.
        self.event_id=None

        #: The type id for the event. This is used to create DeviceEvent objects
        #: or dictionary representations of an event based on the data from an
        #: event value list. Event types are all defined in the
        #: iohub.constants.EventConstants class as class attributes.
        self.type=None

        #: If the device that generates an event type also time stamps
        #: the events, this field is the time of the event as given by the device,
        #: converted to sec.msec-usec for consistancy with all other device times.
        #: If the device that generates the event does not time stamp
        #: events, then the device_time is set to the logged_time for the event.
        self.device_time=None

        #: The sec.msec time that the event was 'received' by the ioHub Process.
        #: For devices where the ioHub polls for events, this is the time that the poll
        #: method was called for the device and the event was retrieved. For
        #: devices that use the event callback to inform the ioHub of new events,
        #: this is the time the callback began to be executed. Time is in sec.msec-usec
        self.logged_time=None

        #: The calculated ioHub time is in the normalized time base that all events share,
        #: regardless of device type. Time is calculated differently depending
        #: on the device and perhaps event type.
        #: Time is what should be used when comparing times of events across
        #: different devices or with times given py psychopy.core.getTime(). Time is in sec.msec-usec.
        self.time=None

        #: This property attempts to give a sense of the amount to which
        #: the event time may be off relative to the true time the event
        #: may have become available to te ioHub Process.
        #: confidence_interval is calculated differently depending
        #: on the device and perhaps event types. In general though, the
        #: smaller the confidence_interval, the more accurate the
        #: calculated time of the event will be. For devices where
        #: a meaningful confidence_interval can not be calculated, a value
        #: of 0.0 is used. Valid confidence_interval values are
        #: in sec.msec-usec and will range from 0.000001 sec.msec-usec
        #: and higher.
        self.confidence_interval=None

        #: The delay of an event is the known (or estimated) delay from when the
        #: real world event occurred to when the ioHub received the event for
        #: processing. This is often called the real-time end-to-end delay
        #: of an event. If the delay for an event can not be reasonably estimated
        #: or is not known at all, a delay of 0.0 is set. Delays are in sec.msec-usec
        #: and valid values will range from 0.000001 sec.msec-usec and higher.
        #: the delay of an event is suptracted from the initially determined ioHub
        #: time for the eventso that the event.time attribute reports the actual
        #: event time as accurately as possible.
        self.delay=None

        self.filter_id=None

        ioObject.__init__(self,*args,**kwargs)

    def __cmp__(self,other):
        return self.time-other.time

    @classmethod
    def createEventAsClass(cls,eventValueList):
        kwargs =cls.createEventAsDict(eventValueList)
        return cls(**kwargs)

    @classmethod
    def createEventAsDict(cls,values):
        return dict(zip(cls.CLASS_ATTRIBUTE_NAMES,values))

    #noinspection PyUnresolvedReferences
    @classmethod
    def createEventAsNamedTuple(cls,valueList):
        return cls.namedTupleClass(*valueList)
#
# Import Devices and DeviceEvents
#


import sys

def import_device(module_path, device_class_name):
    module = __import__(module_path, fromlist=[device_class_name])
    device_class=getattr(module, device_class_name)

    setattr(sys.modules[__name__], device_class_name, device_class)

    event_classes=dict()

    for event_class_name in device_class.EVENT_CLASS_NAMES:
        event_constant_string=convertCamelToSnake(event_class_name[:-5],False)

        event_module = __import__(module_path, fromlist=[event_class_name])
        event_class=getattr(event_module, event_class_name)

        event_class.DEVICE_PARENT=device_class

        event_classes[event_constant_string]=event_class

        setattr(sys.modules[__name__], event_class_name, event_class)

    return device_class,device_class_name,event_classes

try:
    if getattr(sys.modules[__name__],'Display',None) is None:
        display_class,device_class_name,event_classes=import_device('psychopy.iohub.devices.display','Display')
        setattr(sys.modules[__name__],'Display', display_class)

except Exception:
    print2err("Warning: display device module could not be imported.")
    printExceptionDetailsToStdErr()

