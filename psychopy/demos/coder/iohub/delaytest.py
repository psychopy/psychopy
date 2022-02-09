#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
representing the retrace onset detection stability of PsychoPy.
"""

from numpy import zeros
from scipy.stats import norm
from psychopy import visual
from psychopy.iohub import Computer, launchHubServer
from psychopy.iohub.constants import EventConstants
from collections import OrderedDict

totalEventRequestsForTest = 1000
numEventRequests = 0


def run():
    global numEventRequests
    # create fullscreen pyglet window at current resolution, as well as required resources / drawings
    psychoWindow, psychoStim = createPsychoGraphicsWindow()

    io = launchHubServer(window=psychoWindow, experiment_code='delay_test')
    io.devices.mouse.setPosition((0, 0))

    lastFlipTime = 0.0

    # create stats numpy arrays, set experiment process to high priority.
    # Init Results numpy array
    results = zeros((totalEventRequestsForTest, 3), dtype='f4')

    numEventRequests = 0

    # clear the ioHub event Buffer before starting the test.
    # This is VERY IMPORTANT, given an existing bug in ioHub.
    # You would want to do this before each trial started until the bug is fixed.
    io.clearEvents('all')

    # draw and flip to the updated graphics state.
    flipTime = drawAndFlipPsychoWindow(psychoStim, psychoWindow, io, None)
    ifi = flipTime - lastFlipTime
    lastFlipTime = flipTime

    # START TEST LOOP >>>>>>>>>>>>>>>>>>>>>>>>>>
    while numEventRequests < totalEventRequestsForTest:
        # send an Experiment Event to the ioHub server process
        io.sendMessageEvent("This is a test message %.3f" % flipTime)

        # check for any new events from any of the devices, and return the events list and the time it took to
        # request the events and receive the reply
        events, callDuration = checkForEvents(io)
        if events:
            # events were available
            results[numEventRequests][0] = callDuration  # ctime it took to get events from ioHub
            results[numEventRequests][1] = len(events)  # number of events returned
            results[numEventRequests][2] = ifi * 1000.0  # calculating inter flip interval.
            numEventRequests += 1  # incrementing tally counterfgh
            # draw and flip to the updated graphics state.

        flipTime = drawAndFlipPsychoWindow(psychoStim, psychoWindow, io, events)
        ifi = flipTime - lastFlipTime
        lastFlipTime = flipTime

    # END TEST LOOP <<<<<<<<<<<<<<<<<<<<<<<<<<

    psychoWindow.close()

    # plot collected delay and retrace detection results.
    plotResults(results)
    printResults(results)


def createPsychoGraphicsWindow():
    # create a window
    psychoStim = OrderedDict()
    psychoWindow = visual.Window((1920, 1080),
                                 monitor='default',
                                 units='pix',
                                 color=[128, 128, 128], colorSpace='rgb255',
                                 fullscr=True, allowGUI=False,
                                 screen=0
                                 )

    psychoWindow.setMouseVisible(False)

    fixation = visual.PatchStim(psychoWindow, size=25, pos=[0, 0], sf=0,
                                color=[-1, -1, -1], colorSpace='rgb')
    title = visual.TextStim(win=psychoWindow,
                            text="ioHub getEvents Delay Test", pos=[0, 125],
                            height=36, color=[1, .5, 0], colorSpace='rgb',
                            wrapWidth=800.0)

    instr = visual.TextStim(win=psychoWindow,
                            text='Move the mouse around, press keyboard keys and mouse buttons',
                            pos=[0, -125], height=32, color=[-1, -1, -1],
                            colorSpace='rgb', wrapWidth=800.0)

    psychoStim['static'] = visual.BufferImageStim(win=psychoWindow,
                                                  stim=(fixation, title, instr))
    psychoStim['grating'] = visual.PatchStim(psychoWindow,
                                             mask="circle", size=75, pos=[-100, 0],
                                             sf=.075)
    psychoStim['keytext'] = visual.TextStim(win=psychoWindow,
                                            text='key', pos=[0, 300], height=48,
                                            color=[-1, -1, -1], colorSpace='rgb',
                                            wrapWidth=800.0)
    psychoStim['mouseDot'] = visual.GratingStim(win=psychoWindow,
                                                tex=None, mask="gauss",
                                                pos=(0,0), size=(50, 50),
                                                color='purple')
    psychoStim['progress'] = visual.ShapeStim(win=psychoWindow,
                                              vertices=[(0, 0), (0, 0), (0, 0), (0, 0)],
                                              pos=(400, -300))

    return psychoWindow, psychoStim


def drawAndFlipPsychoWindow(psychoStim, psychoWindow, io, events):
    psychoStim['grating'].setPhase(0.05, '+')  # advance phase by 0.05 of a cycle
    currentPosition, currentDisplayIndex = io.devices.mouse.getPosition(return_display_index=True)

    if currentDisplayIndex == 0:
        currentPosition = (float(currentPosition[0]), float(currentPosition[1]))
        psychoStim['mouseDot'].setPos(currentPosition)

    if events:
        diff = totalEventRequestsForTest - numEventRequests
        v = psychoWindow.size[1] / 2.0 * diff / totalEventRequestsForTest
        vert = [[0, 0], [0, v], [2, v], [2, 0]]
        psychoStim['progress'].setVertices(vert)

        for r in events:
            if r.type is EventConstants.KEYBOARD_PRESS:  # keypress code
                psychoStim['keytext'].setText(r.key)

    [psychoStim[skey].draw() for skey in psychoStim]

    flipTime = psychoWindow.flip()
    return flipTime


def checkForEvents(io):
    # get the time we request events from the ioHub
    stime = Computer.getTime()
    r = io.getEvents()
    if r and len(r) > 0:
        # so there were events returned in the request, so include this getEvent request in the tally
        etime = Computer.getTime()
        dur = etime - stime
        return r, dur * 1000.0
    return None, None


def plotResults(results):
    #### calculate stats on collected data and draw some plots ####
    from matplotlib.pyplot import axis, title, xlabel, hist, grid, show, ylabel, plot
    import pylab

    durations = results[:, 0]
    flips = results[1:, 2]

    dmean = durations.mean()
    dstd = durations.std()

    fmean = flips.mean()
    fstd = flips.std()

    pylab.figure(figsize=(7, 5))
    pylab.subplot(1, 3, 1)

    # the histogram of the delay data
    n, bins, patches = hist(durations, 50, facecolor='blue', alpha=0.75)
    # add a 'best fit' line
    y = norm.pdf(bins, dmean, dstd)
    plot(bins, y, 'r--', linewidth=1)
    xlabel('ioHub getEvents Delay')
    ylabel('Percentage')
    title('ioHub Event Delays (msec):\n' + r'$\ \mu={0:.3f},\ \sigma={1:.3f}$'.format(dmean, dstd))
    axis([0, durations.max() + 1.0, 0, 25.0])
    grid(True)

    # graphs of the retrace data ( taken from retrace example in psychopy demos folder)
    intervalsMS = flips
    m = fmean
    sd = fstd
    distString = "Mean={0:.1f}ms,    s.d.={1:.1f},    99%CI={2:.1f}-{3:.1f}".format(
        m, sd, m - 3 * sd, m + 3 * sd)
    nTotal = len(intervalsMS)
    nDropped = sum(intervalsMS > (1.5 * m))
    droppedString = "Dropped/Frames = {0:d}/{1:d} = {2:0.2f}%".format(
        nDropped, nTotal, int(nDropped) / float(nTotal))

    pylab.subplot(1, 3, 2)

    # plot the frameintervals
    pylab.plot(intervalsMS, '-')
    pylab.ylabel('t (ms)')
    pylab.xlabel('frame N')
    pylab.title(droppedString)

    pylab.subplot(1, 3, 3)
    pylab.hist(intervalsMS, 50, histtype='stepfilled')
    pylab.xlabel('t (ms)')
    pylab.ylabel('n frames')
    pylab.title(distString)
    show()


def printResults(results):
    durations = results[:, 0]
    dmean = durations.mean()
    dstd = durations.std()
    print("ioHub getEvent Delays:")
    print("\tMEAN: ", dmean)
    print("\tSDEV: ", dstd)


if __name__ == "__main__":
    run()
