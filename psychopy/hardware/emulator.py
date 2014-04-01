"""Idea: Run or debug an experiment script using exactly the same code, i.e., for
both testing and online data acquisition. To debug timing, you can emulate sync
pulses and user responses. Limitations: pyglet only; keyboard events only.
"""
# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

__author__ = 'Jeremy Gray'

from psychopy import visual, event, core, logging
from psychopy.errors import TimeoutError
import threading

from psychopy.sound import Sound # for SyncGenerator tone

class ResponseEmulator(threading.Thread):
    def __init__(self, simResponses=None):
        """Class to allow simulation of a user's keyboard responses during a scan.

        Given a list of response tuples (time, key), the thread will simulate a
        user pressing a key at a specific time (relative to the start of the run).

        Author: Jeremy Gray; Idea: Mike MacAskill
        """
        if not simResponses:
            self.responses = []
        else:
            self.responses = sorted(simResponses) # sort by onset times
        self.clock = core.Clock()
        self.stopflag = False
        threading.Thread.__init__(self, None, 'ResponseEmulator', None)
        self.running = False

    def run(self):
        self.running = True
        self.clock.reset()
        last_onset = 0.000
        # wait until next event requested, and simulate a key press
        for onset, key in self.responses:
            core.wait(float(onset) - last_onset)
            if type(key) == int:
                #log.warning('ResponseEmulator: int converted to str')
                key = str(key)[0]  # avoid cryptic error if int
            if type(key) == str:
                event._onPygletKey(symbol=key, modifiers=None, emulated=True)
            else:
                logging.error('ResponseEmulator: only keyboard events are supported')
            last_onset = onset
            if self.stopflag: break
        self.running = False

    def stop(self):
        self.stopflag = True

class SyncGenerator(threading.Thread):
    def __init__(self, TR=1.0, volumes=10, sync='5', skip=0, sound=False):
        """Class for a character-emitting metronome thread (emulate MR sync pulse).

            Aim: Allow testing of temporal robustness of fMRI scripts by emulating
            a hardware sync pulse. Adds an arbitrary 'sync' character to the key
            buffer, with sub-millisecond precision (less precise if CPU is maxed).
            Recommend: TR=1.000 or higher and less than 100% CPU. Shorter TR
            --> higher CPU load.

            Parameters:
                TR:      seconds per whole-brain volume
                volumes: number of 3D volumes to obtain in a given scanning run
                sync:    character used as flag for sync timing, default='5'
                skip:    how many frames to silently omit initially during T1
                         stabilization, no sync pulse. Not needed to test script
                         timing, but will give more accurate feel to start of run.
                         aka "discdacqs".
                sound:   simulate scanner noise
        """
        if TR < 0.1:
            raise ValueError, 'SyncGenerator:  whole-brain TR < 0.1 not supported'
        self.TR = TR
        self.hogCPU = 0.035
        self.timesleep = self.TR
        self.volumes = int(volumes)
        self.sync = sync
        self.skip = skip
        self.playSound = sound
        if self.playSound:
            self.sound1 = Sound(800, secs=self.TR-.08, volume=0.15, autoLog=False)
            self.sound2 = Sound(813, secs=self.TR-.08, volume=0.15, autoLog=False)

        self.clock = core.Clock()
        self.stopflag = False
        threading.Thread.__init__(self, None, 'SyncGenerator', None)
        self.running = False
    def run(self):
        self.running = True
        if self.skip:
            for i in range(int(self.skip)):
                if self.playSound:
                    self.sound1.play()
                    self.sound2.play()
                core.wait(self.TR, hogCPUperiod=0) # emulate T1 stabilization without data collection
        self.clock.reset()
        for vol in range(1, self.volumes+1):
            if self.playSound:
                self.sound1.play()
                self.sound2.play()
            if self.stopflag:
                break
            # "emit" a sync pulse by placing a key in the buffer:
            event._onPygletKey(symbol=self.sync, modifiers=None, emulated=True)
            # wait for start of next volume, doing our own hogCPU for tighter sync:
            core.wait(self.timesleep - self.hogCPU, hogCPUperiod=0)
            while self.clock.getTime() < vol * self.TR:
                pass # hogs the CPU for tighter sync
        self.running = False
    def stop(self):
        self.stopflag = True

def launchScan(win, settings, globalClock=None, simResponses=None,
               mode='None', esc_key='escape',
               instr='select Scan or Test, press enter',
               wait_msg="waiting for scanner...",
               wait_timeout=300, log=True):
    """
    Accepts up to four fMRI scan parameters (TR, volumes, sync-key, skip), and
    launches an experiment in one of two modes: Scan, or Test.

    :Usage:
        See Coder Demo -> experiment control -> fMRI_launchScan.py.

        In brief: 1) from psychopy.hardware.emulator import launchScan;
        2) Define your args; and 3) add 'vol = launchScan(args)'
        at the top of your experiment script.

    launchScan() waits for the first sync pulse and then returns, allowing your
    experiment script to proceed. The key feature is that, in test mode, it first
    starts an autonomous thread that emulates sync pulses (i.e., emulated by your CPU rather
    than generated by an MRI machine). The thread places a character in the key buffer, exactly like
    a keyboard event does. launchScan will wait for the first such sync pulse (i.e.,
    character in the key buffer). launchScan returns the number of sync pulses
    detected so far (i.e., 1), so that a script can account for them explicitly.

    If a globalClock is given (highly recommended), it is reset to 0.0 when the
    first sync pulse is detected. If a mode was not specified when calling
    launchScan, the operator is prompted to select Scan or Test.

    If **scan mode** is selected, the script will wait until the first scan pulse
    is detected. Typically this would be coming from the scanner, but note that
    it could also be a person manually pressing that key.

    If **test mode** is selected, launchScan() starts a separate thread to emit
    sync pulses / key presses. Note that this thread is effectively nothing more than
    a key-pressing metronome, emitting a key at the start of every TR, doing so with
    high temporal precision.

    If your MR hardware interface does not deliver a key character as a sync flag,
    you can still use launchScan() to test script timing. You have to code
    your experiment to trigger on either a sync character (to test timing) or
    your usual sync flag (for actual scanning).

    :Parameters:
        win: a :class:`~psychopy.visual.Window` object (required)

        settings : a dict containing up to 5 parameters (2 required: TR, volumes)

            TR :
                seconds per whole-brain volume (minimum value = 0.1s)
            volumes :
                number of whole-brain (3D) volumes to obtain in a given scanning run.
            sync :
                (optional) key for sync timing, default = '5'.
            skip :
                (optional) how many volumes to silently omit initially (during T1
                stabilization, no sync pulse). default = 0.
            sound :
                (optional) whether to play a sound when simulating scanner sync pulses

        globalClock :
            optional but highly recommended :class:`~psychopy.core.Clock` to
            be used during the scan; if one is given, it is reset to 0.000 when
            the first sync pulse is received.

        simResponses :
            optional list of tuples [(time, key), (time, key), ...]. time values
            are seconds after the first scan pulse is received.

        esc_key :
            key to be used for user-interrupt during launch. default = 'escape'

        mode :
            if mode is 'Test' or 'Scan', launchScan() will start in that mode.

        instr :
            instructions to be displayed to the scan operator during mode selection.

        wait_msg :
            message to be displayed to the subject while waiting for the scan to
            start (i.e., after operator indicates start but before the first
            scan pulse is received).

        wait_timeout :
            time in seconds that launchScan will wait before assuming something went
            wrong and exiting. Defaults to 300sec (5 minutes). Raises a TimeoutError
            if no sync pulse is received in the allowable time.
    """

    if not 'sync' in settings:
        settings.update({'sync': '5'})
    if not 'skip' in settings:
        settings.update({'skip': 0})
    try: wait_timeout = max(0.01, float(wait_timeout))
    except ValueError:
        raise ValueError("wait_timeout must be number-like, but instead it was %s." % str(wait_timeout))
    settings['sync'] = unicode(settings['sync'])
    settings['TR'] = float(settings['TR'])
    settings['volumes'] = int(settings['volumes'])
    settings['skip'] = int(settings['skip'])
    runInfo = "vol: %(volumes)d  TR: %(TR).3fs  skip: %(skip)d  sync: '%(sync)s'" % (settings)
    if log:
        logging.exp('launchScan: ' + runInfo)
    instructions = visual.TextStim(win, text=instr, height=.05, pos=(0,0), color=.4, autoLog=log)
    parameters = visual.TextStim(win, text=runInfo, height=.05, pos=(0,-0.5), color=.4, autoLog=log)

    # if a valid mode was specified, use it; otherwise query:
    mode = mode.capitalize()
    if mode not in ['Scan', 'Test']:
        run_type = visual.RatingScale(win, choices=['Scan', 'Test'], marker='circle',
            markerColor='DarkBlue', size=.8, stretch=.3, pos=(0.8,-0.9),
            markerStart='Test', lineColor='DarkGray', autoLog=log)
        while run_type.noResponse:
            instructions.draw()
            parameters.draw()
            run_type.draw()
            win.flip()
        mode = run_type.getRating()
    doSimulation = bool(mode == 'Test')

    win.setMouseVisible(False)
    if mode == 'Test':
        wait_msg += ' (simulation)'
    msg = visual.TextStim(win, color='DarkGray', text=wait_msg, autoLog=log)
    msg.draw()
    win.flip()
    if wait_timeout is None or wait_timeout > 10:
        core.wait(1.2) # show msg for a bit, wait for scanner start

    event.clearEvents() # do before starting the threads
    if doSimulation:
        syncPulse = SyncGenerator(**settings)
        syncPulse.start() # start emitting sync pulses
        core.runningThreads.append(syncPulse)
        if simResponses:
            roboResponses = ResponseEmulator(simResponses)
            roboResponses.start() # start emitting simulated user responses
            core.runningThreads.append(roboResponses)

    # wait for first sync pulse:
    timeoutClock = core.Clock() # zeroed now
    allKeys = []
    while not settings['sync'] in allKeys:
        allKeys = event.getKeys()
        if esc_key and esc_key in allKeys:
            core.quit()
        if timeoutClock.getTime() > wait_timeout:
            raise TimeoutError('Waiting for scanner has timed out in %.3f seconds.' % wait_timeout)
    if globalClock:
        globalClock.reset()
    if log:
        logging.exp('launchScan: start of scan')
    win.flip() # blank the screen on first sync pulse received
    elapsed = 1 # one sync pulse has been caught so far

    return elapsed
