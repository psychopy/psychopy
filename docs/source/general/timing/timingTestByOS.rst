.. _osComparison:

Comparing Operating Systems under PsychoPy
================================================

This is an attempt to quantify the ability of PsychoPy draw without dropping frames on a variety of hardware/software. The following tests were conducted using the script at the bottom of the page. Note, of course that the hardware fully differs between the Mac and Linux/Windows systems below, but that both are standard off-the-shelf machines.

All of the below tests were conducted with 'normal' systems rather than anything that had been specifically optimised:
    - the machines were connected to network
    - did not have anti-virus turned off (except Ubuntu had no anti-virus)
    - they even all had dropbox clients running
    - Linux was the standard (not 'realtime' kernel)

No applications were actively being used by the operator while tests were run.

In order to test drawing under a variety of processing loads the test stimulus was one of:
    - a single drifting Gabor
    - 500 random dots continuously updating
    - 750 random dots continuously updating
    - 1000 random dots continuously updating


Common settings:
    - Monitor was a CRT 1024x768 100Hz
    - all tests were run in full screen mode with mouse hidden
System Differences:
    - the iMac was lower spec than the Windows/Linux box and running across two monitors (necessary in order to connect to the CRT)
    - the Windows/Linux box ran off a single monitor

Each run below gives the number of dropped frames out of a run of 10,000 (2.7 mins at 100Hz). 

================  ===============   ==============  ===============  ===============
_                  Windows XP        Windows 7       Mac OS X 10.6    Ubuntu 11.10
_                  (SP3)             Enterprise      Snow Leopard    
================  ===============   ==============  ===============  ===============
Gabor               0                 5              0                   0
500-dot RDK         0                 5              54                3
750-dot RDK         21                7              aborted           1174
1000-dot RDK        776               aborted        aborted           aborted
----------------  ---------------   --------------  ---------------  ---------------
GPU               Radeon 5400       Radeon 5400     Radeon *2400*    Radeon 5400
GPU driver        Catalyst 11.11    Catalyst 11.11                   Catalyst 11.11
CPU               Core Duo 3GHz     Core Duo 3GHz   Core Duo 2.4GHz  Core Duo 3GHz
RAM               4GB               4GB             2GB              4GB
================  ===============   ==============  ===============  ===============

I'll gradually try to update these tests to include:
    - longer runs (one per night!)
    - a faster Mac
    - a real-time Linux kernel
