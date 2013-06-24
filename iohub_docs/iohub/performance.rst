============================
Performance Considerations
============================


Benefits and Disclaimers to Using the ioHub Event Monitoring Framework
======================================================================

ioHub has been written to try and have as little impact on the PsychoPy
Process as possible, as integration with PsychoPy continues to evolve, the net 
effect on processing load for the PsychoPy Process should actually diminish.

Recall that ioHub runs as a separate operating system process to PsychoPy. The
two processes communicate via a very fast and lightweight message request, 
message response pattern using UDP. As is shown below, the average round trip delay 
for PsychoPy to request new events from the ioHub and receive the event object 
representations back from the ioHub Server is under 0.5 msec, with maximum delays 
typically less than 1.0 msec.

The advantage of the ioHub Event Model is that the ioHub Process is able to spend all its time
checking for new events from devices that need to be polled and handling callback 
functions from devices that use event driven modification. This monitoring occurs
regardless of what state the PsychoPy experiment is in. Events are handled and processed
by the ioHub when PsychoPy is loading an image, drawing updated graphics to the video 
card backbuffer, or waiting in a blocked state for the start of the next vertical 
retrace to occur in the video card logic. This means that the precision of event time stamping
will be much better than what is possible when events are processed *between*
other activities. Timing should also be improved over the case of an application 
using multiple Python threads to try and handle the event processing for devices
that can even report events on a different thread. This is because the Python Interpreter
only allows a single Python thread to run at a time; Python threads can not take
advantage of the benefits that multi core CPUs that are common place today offer.

The model ioHub uses for event monitoring and communication with the 'client' process
( PsychoPy ) is relatively unique and as discussed has clear advantages for an experiment runtime
environment. However there are also considerations that have to be remembered to ensure
that the ioHub - PsychoPy dual process model works as intended:

    #. Since multiple processes are in use, it is required that the experiment computer has multiple processing units (multiple cores or multiple physical CPUs), or performance will be significantly suppressed. Multicore processors are the defacto standard now, even with inexpensive entry level PCs. A dual core system is the minimum that is suggested; a quad core CPU, and to a lesser extent dual core CPU with hyper threading capabilities, is the ideal CPU for use with PsychoPy and ioHub. If a single CPU, single core system is used, the experiment will run and events will be received, however the performance of the experiment runtime and ioHub will be greatly reduced. This is because the two separate processes are having to share a single CPU and take turns using the processing bandwidth available. When processes have to repeatedly start and stop to allow another process to have some CPU time, this is a *very* expensive operation for a computer, and wastes a large amount of the overall processing capabilities of the CPU.
    #. Communication between PsychoPy and the ioHub is very fast, however it is still *slow* relative to how much information can be passed around within a single application process. Therefore, as is seen in the ioHub examples, requests for static data values from the ioHub Process are generally made once and saved to a local PsychoPy variable that can be referenced through out the experiment. Repeatedly calling an ioHub device method that will always return the same value is a waste of interprocess messaging, no matter how fast that messaging may be. In some cases it is obviously necessary to ask for the data from the ioHub server every frame. That is expected and in general will never be an issue. However it is a good practice to do so when necessary only, and cache static values locally when possible. 
    

ioHub Event Model and ioDataStore DeviceEvent storage
=====================================================

When ioHub is used for event monitoring, all event detection (and even storage) is 
handled by a separate Python program that is running in a separate Python Process,
utilizing a separate CPU core of a multicore CPU if possible (which it should be).

The ioHub is constantly either checking for new events from a device, 
or is being notified of new events as they are made available by the underlying 
device driver / user level event API. ioHub has been written to run as a non-
blocking event server, meaning that no code that checks for new events on a device
'waits' until an event is available. For devices that need to be polled, 
a 'peak' and 'get' approach is always used instead. This results in any given 
operation that runs on the ioHub taking well under a msec, often under 50 usec.
 
Device are constantly being monitored with an average update interval
of about 1 msec across all devices within the ioHub software itself.  This means that
event time stamping will occur within about 1 msec or less on average, relative to when
the event was made available to the ioHub system. Furthermore, since ioHub runs
as a separate Python process, on a separate CPU core, much 'more' can be done
with the events that are received than is normally feasible when event collection
is handled by the same Python process that is responsible for all the really heavy work
that an experiment runtime needs to handle. Overall system CPU usage is higher of course,
but it is spread across two CPU cores instead of all being limited to one.

Dedicated event monitoring allows 'all' events received by ioHub to be saved for later access and analysis,
regardless of what subset of these events are actually being used by the experiment paradigm.
For example ioHub has been used to simultaneously save analog input data
from eight channels of a DAQ device sampling each channel at 1000 Hz, while also saving
all eye data from a 1000 Hz eye tracking device and making these events, as well as the
events from other devices such as the keyboard and mouse, available to the PsychoPy
experiment in real-time. This is done without any increase in frame drops or 
processing ability of the PsychoPy process (assuming the CPU considerations 
mentioned above are followed). 

So overall CPU usage on a multicore system when using ioHub along with
PsychoPy is higher compared to running PsychoPy alone, however this usage is caused by
truly parallel processing occurring on the two processing being discussed. 
One core of the CPU will be running at a high usage rate by the ioHub system, 
while a separate core will be running at the same, or potentially much lower 
utilization rate depending on the paradigm being performed and the device
set that is being monitored by ioHub. While admittedly this system design will not win 
any awards for reducing the power consumption of a PC, it will often result in new 
opportunities from an event processing perspective, something that is important
for many research applications.   

How Real-time Device Event End to End Delay is Impacted
========================================================

One of the primary goals of the ioHub is to try and ensure that it adds as little
additional delay, or latency, to the events being delivered from devices to your
experiment during data collection. This is critical for eye tracking paradigms
in particular where gaze contingent manipulations of the display need to be 
performed based on the eye data provided by the eye tracker device. The below four figures
each show the end to end delay distribution from when the PsychoPy process requests events
from the ioHub process, to when the PsychoPy user script has received the 
new events and can being to use the data. The left subplot of each figure is from 
1000 getEvent() requests that returned at least one new device event in the 
response to PsychoPy. The sub plots on the middle and right of the figure show 
the retrace interval as detected and reported by PsychoPy. 

Not only is it important that ioHub is as fast as possible at transferring events 
to the experiment runtime, but it is also critical that this does not influence the
stability of graphics presentation and timing.


    .. figure:: iohubEventDelayTestResults_1.png
        :align: center
        :alt: PsychoPy - ioHub Round Trip Event Retrieval Time (left), and PsychoPy Retrace Rate Timing (middle and right)
        :figclass: align-center

    .. figure:: iohubEventDelayTestResults_2.png
        :align: center
        :alt: PsychoPy - ioHub Round Trip Event Retrieval Time (left), and PsychoPy Retrace Rate Timing (middle and right)
        :figclass: align-center

    .. figure:: iohubEventDelayTestResults_3.png
        :align: center
        :alt: PsychoPy - ioHub Round Trip Event Retrieval Time (left), and PsychoPy Retrace Rate Timing (middle and right)
        :figclass: align-center

    .. figure:: iohubEventDelayTestResults_4.png
        :align: center
        :alt: PsychoPy - ioHub Round Trip Event Retrieval Time (left), and PsychoPy Retrace Rate Timing (middle and right)
        :figclass: align-center
        
        PsychoPy - ioHub Round Trip Event Retrieval Time (left), and PsychoPy Retrace Rate Timing (middle and right)

.. note::
    #. Times are in msec.usec format.
    #. This data was collected using an Asus Essentio Series desktop, equiped with an Intel i7 3.4 Ghz 4-core CPU, 16 GB of RAM, a SATA II hard drive, and Windows 7 64 bit.
    #. A NVIDIA 580GXT Video card was driving a dual monitor setup.
    #. All foreground applications other than the Spyder IDE were closed during the tests. No services were disabled during the tests however.
    #. The test can be run on your hardware by using the ioHubEventDelayTest example found in the examples folder of the ioHub package.
    
As can be seen, the delay added by the ioHub in these tests was minimal and would not significantly effect the performance of any gaze contingent 
eye tracking paradigm I am aware of given even the shortest possible video based eye tracker delays available.
