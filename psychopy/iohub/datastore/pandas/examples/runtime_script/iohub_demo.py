# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 22:46:06 2013

@author: Sol
"""
from __future__ import print_function
from psychopy import visual, core
from psychopy.data import TrialHandler, importConditions
from psychopy.iohub.client import launchHubServer
from psychopy.iohub.devices import Computer
from psychopy.iohub.constants import EventConstants
getTime = Computer.getTime

psychopy_mon_name = 'testMonitor'
exp_code = 'io_stroop'
io = launchHubServer(
    psychopy_monitor_name=psychopy_mon_name,
    experiment_code=exp_code)

io.sendMessageEvent(category='EXP', text='Experiment Started')

kb = io.devices.keyboard
mouse = io.devices.mouse

win = visual.Window(allowGUI=False, fullscr=True)
gabor = visual.GratingStim(
    win, tex='sin', mask='gauss', texRes=256, size=[
        200.0, 200.0], sf=[
            4, 0], ori=0, name='gabor1')
letter = visual.TextStim(win, pos=(0.0, 0.0), text='X')

retrace_count = 0


def loggedFlip(letter_char, letter_color):
    global retrace_count
    gabor.draw()
    letter.setText(letter_char)
    letter.setColor(letter_color)
    letter.draw()
    flip_time = win.flip()
    io.sendMessageEvent(
        category='VSYNC',
        text=str(retrace_count),
        sec_time=flip_time)
    retrace_count += 1
    return flip_time


def openTrialHandler(xlsx_source):
    exp_conditions = importConditions(xlsx_source)
    trials = TrialHandler(exp_conditions, 1)

    # Inform the ioDataStore that the experiment is using a
    # TrialHandler. The ioDataStore will create a table
    # which can be used to record the actual trial variable values (DV or IV)
    # in the order run / collected.
    #
    io.createTrialHandlerRecordTable(trials)
    return trials

trials = openTrialHandler(
    'D:\\Dropbox\\WinPython-32bit-2.7.5.3\\my-code\\psychopy\\psychopy\\iohub\\experimental_code\\pandas_tests\\conditions.csv')

color_mapping = dict(R=[1, 0, 0], G=[0, 1, 0], B=[0, 0, 1])
key_mapping = dict(LEFT='R', DOWN='G', RIGHT='B')

for t, trial in enumerate(trials):
    tstart_flip_time = loggedFlip(
        trial['LETTER'], color_mapping[
            trial['COLOR']])
    io.sendMessageEvent(
        category='EXP',
        text='TRIAL_START',
        sec_time=tstart_flip_time)
    io.clearEvents()

    # repeat drawing for each frame
    key_pressed = None
    while not key_pressed:
        gabor.setPhase(0.01, '+')
        flip_time = loggedFlip(trial['LETTER'], color_mapping[trial['COLOR']])
        # handle key presses each frame
        key_events = kb.getEvents(
            event_type_id=EventConstants.KEYBOARD_RELEASE)

        for ke in key_events:
            if ke.key in key_mapping:
                key_pressed = ke
                break
            elif ke.key == 'ESCAPE':
                break

    if key_pressed is None:
        print('Experiment Terminated By User')
        io.quit()
        core.quit()
        import sys
        sys.exit(1)

    tend_flip_time = loggedFlip(trial['LETTER'], color_mapping[trial['COLOR']])
    win.clearBuffer()

    if key_pressed.key == 'ESCAPE':
        break

    trial['RESPONSE'] = key_mapping[key_pressed.key]
    trial['RT'] = key_pressed.time - tstart_flip_time
    trial['TRIAL_START'] = tstart_flip_time
    trial['TRIAL_END'] = tend_flip_time

    for k, v in trial.items():
        print(k, v, type(v))
    print('---')
    io.sendMessageEvent(
        category='EXP',
        text='TRIAL_END',
        sec_time=tend_flip_time)
    io.addTrialHandlerRecord(trial.values())

win.close()
io.quit()
core.quit()

io.sendMessageEvent(category='EXP', text='Experiment Finished')
