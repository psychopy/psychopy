# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import gc
import sys

import psutil

from ..errors import print2err
from psychopy import clock

REALTIME_PRIORITY_CLASS = -18
HIGH_PRIORITY_CLASS = -10

class Computer():
    """Computer provides access to OS and Process level functionality:

    * Read the current time in sec.msec format. The time base used is shared by
      the ioHub and PsychoPy processes.
    * Access the iohub and psychopy psutil.Process objects
    * Get / set process priority and affinity.
    * Read system memory and CPU usage

    Computer contains only static methods and class attributes. Therefore
    all supported functionality can be accessed directly from the Computer
    class itself; an instance of the class never needs to be created.
    """

    #: Access to the psutil.Process class for the current system Process.
    current_process = psutil.Process()

    #: The psutil Process object for the ioHub Process.
    iohub_process = None

    #: If Computer class is on the iohub server process, psychopy_process is
    #: the psychopy process created from the pid passed to iohub on startup.
    #: The iohub server checks that this process exists
    #: (server.checkForPsychopyProcess()) and shuts down if it does not.
    psychopy_process = None

    #: The OS process ID of the ioHub Process.
    iohub_process_id = None

    #: True if the current process is the ioHub Server Process. False if the
    #: current process is the Experiment Runtime Process.
    is_iohub_process = False

    #: global_clock is used as the common time base for all devices
    #: and between the ioHub Server and Experiment Runtime Process. Do not
    #: access this class directly, instead use the Computer.getTime()
    #: and associated method name alias's to actually get the current ioHub
    # time.
    global_clock = clock.monotonicClock

    #: The name of the current operating system Python is running on.
    platform = sys.platform

    #: Python Env. bits: 32 or 64. Note that when a
    #: Python 32 bit runtime is used a 64 bit OS sysbits will equal 32.
    pybits = 32 + int(sys.maxsize > 2 ** 32) * 32

    try:
        #: Attribute representing the number of *processing units* available on
        #: the current computer. This includes cpu's, cpu cores, and hyperthreads.
        #:
        #: processing_unit_count = num_cpus * cores_per_cpu * num_hyperthreads
        #:
        #: where:
        #:      * num_cpus: Number of CPU chips on the motherboard
        #:        (usually 1 now).
        #:      * cores_per_cpu: Number of processing cores per CPU (2,4 is common)
        #:      * num_hyperthreads: Hyper-threaded cores = 2, otherwise 1.
        processing_unit_count = psutil.cpu_count()

        #: The number of cpu cores available on the computer.
        #: Hyperthreads are NOT included.
        core_count = psutil.cpu_count(False) #hyperthreads not included
    except AttributeError:
        # psutil might be too old (cpu_count added in 2.0)
        import multiprocessing
        processing_unit_count = multiprocessing.cpu_count()
        core_count = None  # but not used anyway

    try:
        #: Process priority when first started. If process is set to
        #: high priority, this value is used when the process is set back to
        #: normal priority.
        _process_original_nice_value=psutil.Process().nice() # used on linux.
    except TypeError:
        # on older versions of psutil (in ubuntu 14.04) nice is attr not call
        _process_original_nice_value=psutil.Process().nice

    #: True if the current process is currently in high or real-time
    #: priority mode (enabled by calling Computer.setPriority()).
    in_high_priority_mode = False

    def __init__(self):
        print2err('WARNING: Computer is a static class, '
                  'no need to create an instance. just use Computer.xxxxxx')

    @staticmethod
    def getPriority():
        """Returns the current processes priority as a string.

        This method is not supported on OS X.

        :return: 'normal', 'high', or 'realtime'
        """
        proc_priority = Computer.current_process.nice()
        if Computer.platform == 'win32':
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
    def _setProcessPriority(process, nice_val, disable_gc):
        org_nice_val = Computer._process_original_nice_value
        try:
            process.nice(nice_val)
            Computer.in_high_priority_mode = nice_val != org_nice_val
            if disable_gc:
                gc.disable()
            else:
                gc.enable()
            return True
        except psutil.AccessDenied:
            print2err('WARNING: Could not set process {} priority '
                      'to {}'.format(process.pid, nice_val))
            return False
    @staticmethod
    def setPriority(level='normal', disable_gc=False):
        """
        Attempts to change the current processes priority based on level.
        Supported levels are:

          * 'normal': sets the current process priority to
          NORMAL_PRIORITY_CLASS on Windows, or to the processes original
          nice value on Linux.
          * 'high': sets the current process priority to HIGH_PRIORITY_CLASS
          on Windows, or to a nice value of -10 value on Linux.
          * 'realtime': sets the current process priority to
          REALTIME_PRIORITY_CLASS on Windows, or to a nice value of -18
          value on Linux.

        If level is 'normal', Python GC is also enabled.
        If level is 'high' or 'realtime', and disable_gc is True, then the
        Python garbage collection (GC) thread is suspended.

        This method is not supported on OS X.

        :return: Priority level of process when method returns.
        """
        level = level.lower()
        current_process = Computer.current_process
        nice_val = Computer._process_original_nice_value

        if level == 'normal':
            disable_gc = False
        elif level == 'high':
            nice_val = HIGH_PRIORITY_CLASS
            if Computer.platform == 'win32':
                nice_val = psutil.HIGH_PRIORITY_CLASS
        elif level.lower() == 'realtime':
            nice_val = REALTIME_PRIORITY_CLASS
            if Computer.platform == 'win32':
                nice_val = psutil.REALTIME_PRIORITY_CLASS

        Computer._setProcessPriority(current_process, nice_val, disable_gc)

        return Computer.getPriority()


    @staticmethod
    def getProcessingUnitCount():
        """
        Return the number of *processing units* available on the current
        computer.
        Processing Units include: cpu's, cpu cores, and hyper threads.

        Notes:

        * processing_unit_count = num_cpus*num_cores_per_cpu*num_hyperthreads.
        * For single core CPU's,  num_cores_per_cpu = 1.
        * For CPU's that do not support hyperthreading,  num_hyperthreads =
        1, otherwise num_hyperthreads = 2.

        Args:
            None

        Returns:
            int: the number of processing units on the computer.
        """

        return Computer.processing_unit_count

    @staticmethod
    def getProcessAffinities():
        """Retrieve the current PsychoPy Process affinity list and ioHub
        Process affinity list.

        For example, on a 2 core CPU with hyper-threading, the possible
        'processor'
        list would be [0,1,2,3], and by default both the PsychoPy and ioHub
        Processes can run on any of these 'processors', so::


            psychoCPUs,ioHubCPUS=Computer.getProcessAffinities()
            print psychoCPUs,ioHubCPUS

            >> [0,1,2,3], [0,1,2,3]


        If Computer.setProcessAffinities was used to set the PsychoPy
        Process to core 1
        (index 0 and 1) and the ioHub Process to core 2 (index 2 and 3),
        with each using both hyper threads of the given core, the set call
        would look like::


            Computer.setProcessAffinities([0,1],[2,3])

            psychoCPUs,ioHubCPUS=Computer.getProcessAffinities()
            print psychoCPUs,ioHubCPUS

            >> [0,1], [2,3]


        If the ioHub is not being used (i.e self.hub is None), then only the
        PsychoPy
        Process affinity list will be returned and None will be returned for
        the
        ioHub Process affinity::

            psychoCPUs,ioHubCPUS=Computer.getProcessAffinities()
            print psychoCPUs,ioHubCPUS

            >> [0,1,2,3], None

        **But in this case, why are you using the ioHub package at all? ;)**

        This method is not supported on OS X.

        Args:
            None

        Returns:
            (list,list) Tuple of two lists: PsychoPy Process affinity ID
            list and ioHub Process affinity ID list.

        """
        curproc_affinity = Computer.current_process.cpu_affinity()
        iohproc_affinity = Computer.iohub_process.cpu_affinity()
        return curproc_affinity, iohproc_affinity

    @staticmethod
    def setProcessAffinities(experimentProcessorList, ioHubProcessorList):
        """Sets the processor affinity for the PsychoPy Process and the ioHub
        Process.

        For example, on a 2 core CPU with hyper-threading, the possible
        'processor'
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

        If setProcessAffinities was used to set the experiment process to
        core 1
        (index 0,1) and the ioHub server process to core 2 (index 2,3), with
        each using both hyper threads of the given core, the set call would
        look
        like::

            Computer.setProcessAffinities([0,1],[2,3])

            # check the process affinities
            psychoCPUs,ioHubCPUS=Computer.getProcessAffinities()
            print psychoCPUs,ioHubCPUS

            >> [0,1], [2,3]

        Args:
           experimentProcessorList (list): list of int processor ID's to set
           the PsychoPy Process affinity to. An empty list means all
           processors.

           ioHubProcessorList (list): list of int processor ID's to set the
           ioHub Process affinity to. An empty list means all processors.

        Returns:
           None

        """
        Computer.current_process.cpu_affinity(experimentProcessorList)
        Computer.iohub_process.cpu_affinity(ioHubProcessorList)

    @staticmethod
    def autoAssignAffinities():
        """Auto sets the PsychoPy Process and ioHub Process affinities based on
        some very simple logic.

        It is not known at this time if the implementation of this method makes
        any sense in terms of actually improving performance. Field tests and
        feedback will need to occur, based on which the algorithm can be
        improved.

        Currently:

        * If the system is detected to have 1 processing unit, or greater
        than 8 processing units, nothing is done by the method.
        * For a system that has two processing units, the PsychoPy Process
        is assigned to index 0, ioHub Process assigned to 1.
        * For a system that has four processing units, the PsychoPy Process
        is assigned to index's 0,1 and the ioHub Process assigned to 2,3.
        * For a system that has eight processing units, the PsychoPy Process
        is assigned to index 2,3, ioHub Process assigned to 4,5. All other
        processes running on the OS are attempted to be assigned to indexes
        0,1,6,7.

        Args:
            None

        Returns:
            None

        """
        cpu_count = Computer.processing_unit_count
        if cpu_count == 2:
            # print 'Assigning experiment process to CPU 0, ioHubServer process
            # to CPU 1'
            Computer.setProcessAffinities([0, ], [1, ])
        elif cpu_count == 4:
            # print 'Assigning experiment process to CPU 0,1, ioHubServer
            # process to CPU 2,3'
            Computer.setProcessAffinities([0, 1], [2, 3])
        elif cpu_count == 8:
            # print 'Assigning experiment process to CPU 2,3, ioHubServer
            # process to CPU 4,5, attempting to assign all others to 0,1,6,7'
            Computer.setProcessAffinities([2, 3], [4, 5])
            Computer.setAllOtherProcessesAffinity(
                    [0, 1, 6, 7],
                    [Computer.currentProcessID, Computer.iohub_process_id])
        else:
            print('autoAssignAffinities does not support %d processors.' % (
            cpu_count,))

    @staticmethod
    def getCurrentProcessAffinity():
        """
        Returns a list of 'processor' ID's (from 0 to
        Computer.processing_unit_count-1)
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
        Sets the list of 'processor' ID's (from 0 to
        Computer.processing_unit_count-1)
        that the current (calling) process should only be allowed to run on.

        Args:
           processorList (list): list of int processor ID's to set the
           current Process affinity to. An empty list means all processors.

        Returns:
            None

        """
        return Computer.current_process.cpu_affinity(processorList)

    @staticmethod
    def setProcessAffinityByID(process_id, processor_list):
        """
        Sets the list of 'processor' ID's (from 0 to
        Computer.processing_unit_count-1)
        that the process with the provided OS Process ID is able to run on.

        Args:
           processID (int): The system process ID that the affinity should
           be set for.

           processorList (list): list of int processor ID's to set process
           with the given processID too. An empty list means all processors.

        Returns:
            None
        """
        p = psutil.Process(process_id)
        return p.cpu_affinity(processor_list)

    @staticmethod
    def getProcessAffinityByID(process_id):
        """
        Returns a list of 'processor' ID's (from 0 to
        Computer.processing_unit_count-1)
        that the process with the provided processID is able to run on.

        Args:
           processID (int): The system process ID that the affinity should
           be set for.

        Returns:
           processorList (list): list of int processor ID's to set process
           with the given processID too. An empty list means all processors.
        """
        p = psutil.Process(process_id)
        return p.cpu_affinity()

    @staticmethod
    def setAllOtherProcessesAffinity(
            processor_list,
            exclude_process_id_list=[]):
        """
        Sets the affinity for all OS Processes other than those specified in
        the
        exclude_process_id_list, to the processing unit indexes specified in
        processor_list.
        Valid values in the processor_list are between 0 to
        Computer.processing_unit_count-1.

        exclude_process_id_list should be a list of OS Process ID integers,
        or an empty list (indicating to set the affiinty to all processing
        units).

        Note that the OS may not allow the calling process to set the affinity
        of every other process running on the system. For example, some system
        level processing can not have their affinity set by a user level
        application.

        However, in general, many processes can have their affinity set by
        another user process.

        Args:
           processor_list (list): list of int processor ID's to set all OS
           Processes to. An empty list means all processors.

           exclude_process_id_list (list):  A list of process ID's that
           should not have their process affinity settings changed.

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
    def getProcessFromName(pnames, id_only=False):
        procs = []
        if isinstance(pnames, str):
            pnames = [pnames, ]
        for p in psutil.process_iter():
            if p.name() in pnames:
                if id_only:
                    procs.append(p.pid)
                else:
                    procs.append(p)
        return procs

    @staticmethod
    def getTime():
        """
        Returns the current sec.msec-msec time of the system.

        The underlying timer that is used is based on OS and Python version.
        Three requirements exist for the ioHub time base implementation:

        * The Python interpreter does not apply an offset to the times
        returned based on when the timer module being used was loaded or
        when the timer function first called was first called.
        * The timer implementation used must be monotonic and report elapsed
        time between calls, 'not' CPU usage time.
        * The timer implementation must provide a resolution of 50 usec or
        better.

        Given the above requirements, ioHub selects a timer implementation
        as follows:

        * On Windows, the Windows Query Performance Counter API is used
        using ctypes access.
        * On other OS's, if the Python version being used is 2.6 or lower,
        time.time is used. For Python 2.7 and above,
        the timeit.default_timer function is used.

        Args:
           None

        Returns:
           None
        """
        return Computer.global_clock.getTime()

    @staticmethod
    def syncClock(lastResetTime):
        """
        Sync times of last reset between Computer.global_clock with given last reset time.

        Parameters
        ----------
        lastResetTime : float
            Last reset time of clock to sync with
        """
        Computer.global_clock._timeAtLastReset = lastResetTime

    @staticmethod
    def getPhysicalSystemMemoryInfo():
        """Return a class containing information about current memory usage.

        Args:
           None

        Returns:
           vmem: (total=long, available=long, percent=float, used=long,
           free=long)

        Where:

        * vmem.total: the total amount of memory in bytes.
        * vmem.available: the available amount of memory in bytes.
        * vmem.percent: the percent of memory in use by the system.
        * vmem.used: the used amount of memory in bytes.
        * vmem.free: the amount of memory that is free in bytes.On Windows,
        this is the same as vmem.available.

        """
        m = psutil.virtual_memory()
        return m

    @staticmethod
    def getCPUTimeInfo(percpu=False):
        """Return a float representing the current CPU utilization as a
        percentage.

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
        """Get the current / Local process.

        On Windows and Linux, this is a psutil.Process class instance.

        Args:
           None

        Returns:
           object: Process object for the current system process.

        """
        return Computer.current_process

    @staticmethod
    def getIoHubProcess():
        """Get the ioHub Process.

        On Windows and Linux, this is a psutil.Process class instance.

        Args:
           None

        Returns:
           object: Process object for the ioHub Process.

        """
        return Computer.iohub_process
