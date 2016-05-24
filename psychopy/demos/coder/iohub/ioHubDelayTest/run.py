#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Tests the round trip delay from when the experiment runtime requests
new events from the ioHub server to when a response with >=1 new
event is received and ready for use within the experiment script.

Only getEvent requests that return with atleast one new event are used
in the calculated statistics to try and ensure the reported delay is
measuring the higher processing load case of new events being
returned, vs. the case of no new events being available.

At the end of the test, a MatPlotLib figure is displayed showing a
histogram of the round trip event request delays as well as two figures
representing the retrace onset detection stability of PsychoPy when the
ioHub is being used.

PsychoPy code is taken from an example psychopy script in the coder
documentation.
"""

from __future__ import division, print_function, absolute_import

from numpy import zeros
from collections import OrderedDict
from psychopy import core, visual
from psychopy.iohub.devices import Computer
from psychopy.iohub.client import launchHubServer

totalEventRequestsForTest = 1000


win = None
psychoStim = OrderedDict()
numEventRequests = 0
flipTime = 0.0
lastFlipTime = 0.0
results = None

def createPsychoGraphicsWindow():
    # create a window
    global win
    win = visual.Window(
        io.devices.display.getPixelResolution(),
        monitor=io.devices.display.getPsychopyMonitorName(),
        units=io.devices.display.getCoordinateType(),
        color=[
            128,
            128,
            128],
        colorSpace='rgb255',
        fullscr=True,
        allowGUI=False,
        screen=io.devices.display.getIndex())

    currentPosition = io.devices.mouse.setPosition((0, 0))

    fixation = visual.PatchStim(win, size=25, pos=[0, 0],
                                sf=0, color=[-1, -1, -1], colorSpace='rgb')
    title = visual.TextStim(win=win,
                            text='ioHub getEvents Delay Test',
                            pos=[0, 125], height=36, color=[1, .5, 0],
                            colorSpace='rgb', alignHoriz='center',
                            wrapWidth=800.0)

    instxt = 'Move the mouse around, press keyboard keys and mouse buttons'
    instr = visual.TextStim(win=win, text=instxt,
                            pos=[0, -125], height=32, color=[-1, -1, -1],
                            colorSpace='rgb', alignHoriz='center',
                            wrapWidth=800.0)

    psychoStim['static'] = visual.BufferImageStim(win,
                                                       stim=(fixation,
                                                             title, instr))
    psychoStim['grating'] = visual.PatchStim(win,
                                                  mask='circle', size=75,
                                                  pos=[-100, 0], sf=.075)
    psychoStim['keytext'] = visual.TextStim(win,
                                                 text='key',
                                                 pos=[0, 300],
                                                 height=48,
                                                 color=[-1, -1, -1],
                                                 colorSpace='rgb',
                                                 alignHoriz='left',
                                                 wrapWidth=800.0)
    psychoStim['mouseDot'] = visual.GratingStim(win,
                                                     tex=None,
                                                     mask='gauss',
                                                     pos=currentPosition,
                                                     size=(50, 50),
                                                     color='purple')
    psychoStim['progress'] = visual.ShapeStim(win,
                                                   vertices=[(0, 0),
                                                             (0, 0),
                                                             (0, 0),
                                                             (0, 0)],
                                                   pos=(400, -300))

def drawAndFlipPsychoWindow():
    global flipTime, lastFlipTime, events
    # advance phase by 0.05 of a cycle
    psychoStim['grating'].setPhase(0.05, '+')
    currentPosition, currentDisplayIndex = io.devices.mouse.getPosition(
        return_display_index=True)

    if currentDisplayIndex == io.devices.display.getIndex():
        currentPosition = (float(currentPosition[0]),
                           float(currentPosition[1]))
        psychoStim['mouseDot'].setPos(currentPosition)

    if events:
        diff = totalEventRequestsForTest - numEventRequests
        v = win.size[1] / 2.0
        v = v * diff / totalEventRequestsForTest
        vert = [[0, 0], [0, v], [2, v], [2, 0]]
        psychoStim['progress'].setVertices(vert)

        kb_presses = io.devices.keyboard.getPresses()
        for r in kb_presses:
            psychoStim['keytext'].setText(r.key)
        events = None

    [psychoStim[skey].draw() for skey in psychoStim]

    flipTime = win.flip()
    d = flipTime - lastFlipTime
    lastFlipTime = flipTime
    return d

def checkForEvents():
    # get the time we request events from the ioHub
    stime = Computer.getTime()
    r = io.getEvents()
    if r and len(r) > 0:
        # so there were events returned in the request, so include this
        # getEvent request in the tally
        etime = Computer.getTime()
        dur = etime - stime
        return r, dur * 1000.0
    return None, None

def initStats():
    global numEventRequests, flipTime, lastFlipTime, results, events
    if io is None:
        print("Error: ioHub must be enabled to run "
              "the testEventRetrievalTiming test.")
        return

    # Init Results numpy array
    results = zeros((totalEventRequestsForTest, 3), dtype='f4')
    numEventRequests = 0
    flipTime = 0.0
    lastFlipTime = 0.0
    events = None
    # clear the ioHub event Buffer before starting the test.
    io.clearEvents()

def updateStats(new_events, duration, ifi):
    global numEventRequests
    # ctime it took to get events from ioHub
    results[numEventRequests][0] = duration
    # number of events returned
    results[numEventRequests][1] = len(new_events)
    # calculating inter flip interval.
    results[numEventRequests][2] = ifi * 1000.0
    # incrementing tally counter
    numEventRequests += 1

def spinDownTest():
    # OK, we have collected the number of requested getEvents,
    # that have returned >0 events so _close psychopy window
    win.close()

    # disable high priority in both processes
    Computer.setPriority('normal')

def plotResults():
    # calculate stats on collected data and draw some plots
    import matplotlib.mlab as mlab
    from matplotlib.pyplot import (axis, title, xlabel, hist, grid, show,
                                   ylabel, plot)
    import pylab

    durations = results[:, 0]
    flips = results[1:, 2]
    dmin = durations.min()
    dmax = durations.max()
    dmean = durations.mean()
    dstd = durations.std()
    fmean = flips.mean()
    fstd = flips.std()

    pylab.figure(figsize=[30, 10])
    pylab.subplot(1, 3, 1)

    # the histogram of the delay data
    n, bins, patches = hist(durations, 50, normed=True, facecolor='blue',
                            alpha=0.75)
    # add a 'best fit' line
    y = mlab.normpdf(bins, dmean, dstd)
    plot(bins, y, 'r--', linewidth=1)
    xlabel('ioHub getEvents Delay')
    ylabel('Percentage')
    title('ioHub Event Delay Histogram (msec.usec):\n' +
          r'$\ \min={0:.3f},\ \max={1:.3f},\ \mu={2:.3f},\ \sigma={3:.3f}$'.format(
          dmin, dmax, dmean, dstd))
    axis([0, dmax + 1.0, 0, 25.0])
    grid(True)

    # graphs of the retrace data
    # Code taken from retrace example in psychopy demos folder.
    intervalsMS = flips
    m = fmean
    sd = fstd
    dstr_proto = "Mean={0:.1f}ms,\ts.d.={1:.1f},\t99%CI={2:.1f}-{3:.1f}"
    distString = dstr_proto.format(m, sd, m - 3 * sd, m + 3 * sd)
    nTotal = len(intervalsMS)
    nDropped = sum(intervalsMS > (1.5 * m))
    droppedString = 'Dropped/Frames = {0:d}/{1:d} = {2}%'.format(
                                            nDropped,
                                            nTotal,
                                            int(nDropped) / float(nTotal))

    pylab.subplot(1, 3, 2)
    # plot the frameintervals
    pylab.plot(intervalsMS, '-')
    pylab.ylabel('t (ms)')
    pylab.xlabel('frame N')
    pylab.title(droppedString)

    pylab.subplot(1, 3, 3)
    pylab.hist(intervalsMS, 50, normed=0, histtype='stepfilled')
    pylab.xlabel('t (ms)')
    pylab.ylabel('n frames')
    pylab.title(distString)

    show()

if __name__ == '__main__':
    global io, events
    # Start the ioHub Server process. Since an experiment_code is provided,
    # data will be saved to an hdf5 file with an autogenerated name. 
    io = launchHubServer(experiment_code='gevt_test')
    
    # create fullscreen pyglet window at current resolution, as well as
    # required resources / drawings
    createPsychoGraphicsWindow()

    # create stats numpy arrays, set experiment process to high priority.
    initStats()

    # enable high priority mode for the experiment process
    # Computer.enableHighPriority()

    # draw and flip to the updated graphics state.
    ifi = drawAndFlipPsychoWindow()

    # START TEST LOOP >>>>>>>>>>>>>>>>>>>>>>>>>>

    while numEventRequests < totalEventRequestsForTest:
        # send an Experiment Event to the ioHub server process
        io.sendMessageEvent(
            'This is a test message %.3f' %
            flipTime)

        # check for any new events from any of the devices,
        # and return the events list and the time it took to
        # request the events and receive the reply
        events, callDuration = checkForEvents()
        if events:
            # events were available
            updateStats(events, callDuration, ifi)
            # draw and flip to the updated graphics state.

        ifi = drawAndFlipPsychoWindow()

    # END TEST LOOP <<<<<<<<<<<<<<<<<<<<<<<<<<

    # close necessary files / objects, disable high priority.
    spinDownTest()

    # plot collected delay and retrace detection results.
    plotResults()
