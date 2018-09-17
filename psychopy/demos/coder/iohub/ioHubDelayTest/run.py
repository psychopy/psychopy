#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
iohub
.. file: iohub/examples/ioHubAccessDelayTest/run.py

Authors: Sol Simpson, Jeremy Gray

Changes:
    *. September, 2012: Initial release (SS).
    *. April, 2013: greatly improved graphics rendering time by optimizing PsychoPy stim resource usage (JG).

"""

from __future__ import absolute_import, division, print_function

from numpy import zeros

from psychopy import core, visual
from psychopy.iohub import Computer, ioHubExperimentRuntime, EventConstants
from collections import OrderedDict


class ExperimentRuntime(ioHubExperimentRuntime):
    def run(self,*args,**kwargs):
        """
        Tests the round trip delay from when the experiment runtime requests
        new events from the ioHub server to when a response with >=1 new
        event is received and ready for use within the experiment script.

        Only getEvent requests that return with at least one new event are used in
        the calculated statistics to try and ensure the reported delay is measuring
        the higher processing load case of new events being returned, vs. the
        case of no new events being available.

        At the end of the test, a MatPlotLib figure is displayed showing a
        histogram of the round trip event request delays as well as two figures
        representing the retrace onset detection stability of PsychoPy when the
        ioHub is being used.

        PsychoPy code is taken from an example psychopy script in the coder
        documentation.
        """
        self.psychoStim = OrderedDict()
        self.totalEventRequestsForTest=1000
        self.numEventRequests=0
        self.psychoWindow=None
        self.lastFlipTime=0.0
        self.events=None


        # create 'shortcuts' to the devices of interest for this experiment
        self.mouse=self.hub.devices.mouse
        self.kb=self.hub.devices.kb
        self.expRuntime=self.hub.devices.experimentRuntime
        self.display=self.hub.devices.display

        # create fullscreen pyglet window at current resolution, as well as required resources / drawings
        self.createPsychoGraphicsWindow()

        # create stats numpy arrays, set experiment process to high priority.
        self.initStats()

        # enable high priority mode for the experiment process
        #Computer.enableHighPriority()

        #draw and flip to the updated graphics state.
        ifi=self.drawAndFlipPsychoWindow()

        # START TEST LOOP >>>>>>>>>>>>>>>>>>>>>>>>>>

        while self.numEventRequests < self.totalEventRequestsForTest:
            # send an Experiment Event to the ioHub server process
            self.hub.sendMessageEvent("This is a test message %.3f"%self.flipTime)

            # check for any new events from any of the devices, and return the events list and the time it took to
            # request the events and receive the reply
            self.events,callDuration=self.checkForEvents()
            if self.events:
                # events were available
                self.updateStats(self.events, callDuration, ifi)
                #draw and flip to the updated graphics state.

            ifi=self.drawAndFlipPsychoWindow()

        # END TEST LOOP <<<<<<<<<<<<<<<<<<<<<<<<<<

        # close necessary files / objects, disable high priority.
        self.spinDownTest()

        # plot collected delay and retrace detection results.
        self.plotResults()

    def createPsychoGraphicsWindow(self):
        #create a window
        self.psychoWindow = visual.Window(self.display.getPixelResolution(),
                                    monitor=self.display.getPsychopyMonitorName(),
                                    units=self.display.getCoordinateType(),
                                    color=[128,128,128], colorSpace='rgb255',
                                    fullscr=True, allowGUI=False,
                                    screen=self.display.getIndex()
                        )

        currentPosition=self.mouse.setPosition((0,0))
        self.mouse.setSystemCursorVisibility(False)

        fixation = visual.PatchStim(self.psychoWindow, size=25, pos=[0,0], sf=0,
                                    color=[-1,-1,-1], colorSpace='rgb')
        title = visual.TextStim(win=self.psychoWindow,
                                text="ioHub getEvents Delay Test", pos = [0,125],
                                height=36, color=[1,.5,0], colorSpace='rgb',
                                alignHoriz='center', wrapWidth=800.0)

        instr = visual.TextStim(win=self.psychoWindow,
                                text='Move the mouse around, press keyboard keys and mouse buttons',
                                pos = [0,-125], height=32, color=[-1,-1,-1],
                                colorSpace='rgb',alignHoriz='center',wrapWidth=800.0)

        self.psychoStim['static'] = visual.BufferImageStim(win=self.psychoWindow,
                                         stim=(fixation, title, instr))
        self.psychoStim['grating'] = visual.PatchStim(self.psychoWindow,
                                        mask="circle", size=75,pos=[-100,0],
                                        sf=.075)
        self.psychoStim['keytext'] = visual.TextStim(win=self.psychoWindow,
                                        text='key', pos = [0,300], height=48,
                                        color=[-1,-1,-1], colorSpace='rgb',
                                        alignHoriz='left',wrapWidth=800.0)
        self.psychoStim['mouseDot'] = visual.GratingStim(win=self.psychoWindow,
                                        tex=None, mask="gauss",
                                        pos=currentPosition,size=(50,50),
                                        color='purple')
        self.psychoStim['progress'] = visual.ShapeStim(win=self.psychoWindow,
                                        vertices=[(0,0),(0,0),(0,0),(0,0)],
                                        pos=(400, -300))

    def drawAndFlipPsychoWindow(self):
        self.psychoStim['grating'].setPhase(0.05, '+')#advance phase by 0.05 of a cycle
        currentPosition,currentDisplayIndex=self.mouse.getPosition(return_display_index=True)

        if currentDisplayIndex == self.display.getIndex():
            currentPosition=(float(currentPosition[0]),float(currentPosition[1]))
            self.psychoStim['mouseDot'].setPos(currentPosition)

        if self.events:
            diff = self.totalEventRequestsForTest - self.numEventRequests
            v = self.psychoWindow.size[1] / 2.0 * diff / self.totalEventRequestsForTest
            vert = [[0,0], [0,v], [2,v],[2,0]]
            self.psychoStim['progress'].setVertices(vert)

            for r in self.events:
                if r.type is EventConstants.KEYBOARD_PRESS: #keypress code
                    self.psychoStim['keytext'].setText(r.key)

            self.events=None

        [self.psychoStim[skey].draw() for skey in self.psychoStim]

        self.flipTime=self.psychoWindow.flip()
        d=self.flipTime-self.lastFlipTime
        self.lastFlipTime=self.flipTime
        return d

    def checkForEvents(self):
        # get the time we request events from the ioHub
        stime=Computer.currentTime()
        r = self.hub.getEvents()
        if r and len(r) > 0:
            # so there were events returned in the request, so include this getEvent request in the tally
            etime=Computer.currentTime()
            dur=etime-stime
            return r, dur*1000.0
        return None,None


    def initStats(self):
        if self.hub is None:
            print("Error: ioHub must be enabled to run the testEventRetrievalTiming test.")
            return

        # Init Results numpy array
        self.results= zeros((self.totalEventRequestsForTest,3),dtype='f4')

        self.numEventRequests=0
        self.flipTime=0.0
        self.lastFlipTime=0.0

        # clear the ioHub event Buffer before starting the test.
        # This is VERY IMPORTANT, given an existing bug in ioHub.
        # You would want to do this before each trial started until the bug is fixed.
        self.hub.clearEvents('all')

    def updateStats(self, events, duration, ifi):
        self.results[self.numEventRequests][0]=duration     # ctime it took to get events from ioHub
        self.results[self.numEventRequests][1]=len(events)  # number of events returned
        self.results[self.numEventRequests][2]=ifi*1000.0   # calculating inter flip interval.
        self.numEventRequests+=1                            # incrementing tally counterfgh


    def spinDownTest(self):
        # OK, we have collected the number of requested getEvents, that have returned >0 events
        # so _close psychopy window
        self.psychoWindow.close()

        # disable high priority in both processes
        Computer.disableHighPriority()


    def plotResults(self):
        #### calculate stats on collected data and draw some plots ####
        import matplotlib.mlab as mlab
        from matplotlib.pyplot import axis, title, xlabel, hist, grid, show, ylabel, plot
        import pylab

        results= self.results

        durations=results[:,0]
        flips=results[1:,2]

        dmin=durations.min()
        dmax=durations.max()
        dmean=durations.mean()
        dstd=durations.std()

        fmean=flips.mean()
        fstd=flips.std()

        pylab.figure(figsize=[30,10])
        pylab.subplot(1,3,1)

        # the histogram of the delay data
        n, bins, patches = hist(durations, 50, normed=True, facecolor='blue', alpha=0.75)
        # add a 'best fit' line
        y = mlab.normpdf( bins, dmean, dstd)
        plot(bins, y, 'r--', linewidth=1)
        xlabel('ioHub getEvents Delay')
        ylabel('Percentage')
        title('ioHub Event Delay Histogram (msec.usec):\n'+r'$\ \min={0:.3f},\ \max={1:.3f},\ \mu={2:.3f},\ \sigma={3:.3f}$'.format(
                dmin, dmax, dmean, dstd))
        axis([0, dmax+1.0, 0, 25.0])
        grid(True)


        # graphs of the retrace data ( taken from retrace example in psychopy demos folder)
        intervalsMS = flips
        m=fmean
        sd=fstd
        distString= "Mean={0:.1f}ms,    s.d.={1:.1f},    99%CI={2:.1f}-{3:.1f}".format(
                                m, sd, m - 3 * sd, m + 3 * sd)
        nTotal=len(intervalsMS)
        nDropped=sum(intervalsMS>(1.5*m))
        droppedString = "Dropped/Frames = {0:d}/{1:d} = {2}%".format(
                                nDropped, nTotal, int(nDropped) / float(nTotal))

        pylab.subplot(1,3,2)

        #plot the frameintervals
        pylab.plot(intervalsMS, '-')
        pylab.ylabel('t (ms)')
        pylab.xlabel('frame N')
        pylab.title(droppedString)

        pylab.subplot(1,3,3)
        pylab.hist(intervalsMS, 50, normed=0, histtype='stepfilled')
        pylab.xlabel('t (ms)')
        pylab.ylabel('n frames')
        pylab.title(distString)

        show()

from psychopy.iohub import module_directory
runtime=ExperimentRuntime(module_directory(ExperimentRuntime.run), "experiment_config.yaml")
runtime.start()
