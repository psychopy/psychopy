#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
import serial
import json
from matplotlib import pyplot
import numpy as np
from psychopy import core, event, visual
import psychopy.sound as sound

def getSerialPorts():
    available = []
    if os.name == 'nt':  # Windows
        for i in range(1, 256):
            try:
                sport = 'COM' + str(i)
                s = serial.Serial(sport, baudrate=128000)
                available.append(sport)
                s.close()
            except (serial.SerialException, ValueError):
                pass
    else:  # Mac / Linux
        from serial.tools import list_ports
        available = [port[0] for port in list_ports.comports()]
    return available


def getLabHackerDevices(device_types=["USB2TTL8", "MilliKey"]):
    devices = []
    available = getSerialPorts()
    for p in available:
        try:
            mkey_sport = serial.Serial(p, baudrate=128000, timeout=0.1)
            while mkey_sport.readline():
                pass
            mkey_sport.write(b"GET CONFIG\n")
            rx_data = mkey_sport.readline()
            if rx_data:
                rx_data = rx_data[:-1].strip()
                try:
                    mkconf = json.loads(rx_data)
                    if mkconf.get('name','') in device_types:
                        mkconf['port'] = p
                        devices.append(mkconf)
                except:
                    raise RuntimeError("ERROR: {}".format(rx_data))
            mkey_sport.close()
        except:
            pass
    return devices

def quit(scon):
    sconn.write(b"WRITE 0\n")
    scon.close()
    core.quit()

def plotYX(yaxis, xaxis, description=''):
    pyplot.plot(xaxis, yaxis)
    pyplot.grid(True)
    pyplot.title(description)
    pyplot.ylabel('[std %.1f]' % np.std(yaxis))
    pyplot.draw()
    pyplot.show()

if __name__ == "__main__":
    lhdevs = getLabHackerDevices()
    if len(lhdevs) == 0:
        print("No LabHackers device detected. Exiting test...")
        core.quit()

    sconn = serial.Serial(lhdevs[0]['port'], baudrate=128000, timeout=0.0)
    sconn.write(b"SET DATA_MODE WRITE\n")

    # initial set up:
    win = visual.Window(fullscr=False, units='height')
    circle = visual.Circle(win, 0.25, fillColor=1, edges=64)

    ## getting connected microphones
    microphones = sound.Microphone.getDevices()
    ## create a new microphone stream
    recordingMicrophone = microphones[0]  # get the first device
    print(recordingMicrophone.deviceName)  # print the device name
    ## initialize a microphone
    mic = sound.Microphone(recordingMicrophone, sampleRateHz=sound.SAMPLE_RATE_48kHz,
                           bufferSecs=10.0)

    instr = visual.TextStim(win, 'Press Any key to start...', color=-1, height=0.05)
    circle.draw()
    instr.draw()
    win.flip()
    if 'escape' in event.waitKeys():
        core.quit()

    # Wait for release so key sound is not recorded.
    core.wait(2)

    # Turn all digital outs off.
    sconn.write(b"WRITE 0\n")

    rec_duration = 2.0
    for i in range(5):
        time.sleep(0.5)

        # Instruct USB2TTL8 to start toggling digital out every 200 msec
        # (generating a sound on the attached piezo buzzer every 200 msec)
        # from the start of the mic recording in the experiment.
        sconn.write(b"WRITE 255 200000 0 1\n")
        stime = core.getTime()
        ## start a recording
        mic.start()
        stime2 = core.getTime()
        print("Recording %d start returned in %.3f msec." % (i, (stime2-stime)*1000.0))

        circle.draw()
        win.flip()

        wait_dur = rec_duration-(core.getTime()-stime2)
        print('left to wait:', wait_dur)
        core.wait(wait_dur)

        # Turn all digital outs off / stop toggling
        sconn.write(b"WRITE 0\n")

        if len(event.getKeys(['escape'])):
            break

        myRecording, _, _, _ = mic.getAudioClip()  # get the audio clip as an AudioClip
        mic.stop()  # end the recording
        ## save the result
        myRecording.save('mic_rec%d.flac'%i, codec='flac')
        time.sleep(0.5)
        #print("audioClip.duration: ", audioClip.duration, i)  # should be ~10 seconds
        #print("audioClip.samples.shape: ",audioClip.samples.shape, i)
        #audioClip.save('test%d.wav'%i)  # save the recorded audio as a 'wav' file
        #    print("sample count:", len(data))
        #clip_length = len(data)/rate
        #tvals = np.linspace(0.0,clip_length, len(data))
        #print('clip_length:', clip_length)
        #plotYX(data, tvals, "time domain @ %iHz" % sampleRate)

    win.close()
    quit(sconn)

# The contents of this file are in the public domain.
