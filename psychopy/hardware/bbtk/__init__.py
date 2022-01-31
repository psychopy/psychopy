#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Base class for serial devices. Includes some convenience methods to open
ports and check for the expected device
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import time
from psychopy import logging
from psychopy.hardware import serialdevice

evtChannels = {
    0: "Key4",
    1: "Key3",
    2: "Key2",
    3: "Key1",
    4: "Opto4",
    5: "Opto3",
    6: "Opto2",
    7: "Opto1",
    8: "TTL2",
    9: "TTL1",
    10: "Mic2",
    11: "Mic1",
}

class BlackBoxToolkit(serialdevice.SerialDevice):
    """A base class for serial devices, to be sub-classed by specific devices
    """
    name = b'BlackBoxToolkit'
    longName = b"BlackBoxToolkit 2"
    # list of supported devices (if more than one supports same protocol)
    driverFor = [b"BlackBoxToolkit 2"]
    def __init__(self,
                 port=None,
                 sendBreak=False,
                 smoothing=False,
                 bufferSize=262144):
        # if we're trying to send the break signal then presumably the device
        # is sleeping
        if sendBreak:
            checkAwake = False
        else:
            checkAwake = True
        # run initialisation; parity = enable parity checking
        super(BlackBoxToolkit, self).__init__(port,
                                              baudrate=230400, eol="\r\n",
                                              parity='N',
                                              pauseDuration=1.0,  # 1 second pause!! slow device
                                              checkAwake=checkAwake)
        if sendBreak:
            self.sendBreak()
            time.sleep(3.0)  # give time to reset

        if smoothing == False:
            # For use with CRT monitors which require smoothing. LCD monitors do not.
            # Remove smoothing for optos, but keep mic smoothing - refer to BBTK handbook re: mic smoothing latency
            # Important to remove smoothing for optos, as smoothing adds 20ms delay to timing.
            logging.info("Opto sensor smoothing removed.  Mic1 and Mic2 smoothing still active.")
            self.setSmoothing('11000000')
            self.pause()

        try: # set buffer size - can make proportional to size of data (32 bytes per line * events)+1000
            self.com.set_buffer_size(bufferSize)
        except Exception:
            logging.warning("Could not set buffer size. The default buffer size for Windows is 4096 bytes.")

    def sendBreak(self):
        """Send a break event to reset the box if needed
        (can be done by setting sendBreak=true at __init__)
        """
        try:
            self.com.send_break()
        except AttributeError:
            self.com.sendBreak()  # not sure when this was deprecated

    def isAwake(self):
        """Checks that the black box returns "BBTK;\n" when probed with "CONN"
        """
        self.pause()
        self.sendMessage(b'CONN')
        self.pause()
        reply = self.getResponse(timeout=1.0)
        return reply == b'BBTK;\n'

    def showAbout(self):
        """Will show the 'about' screen on the LCD panel for 2 seconds
        """
        self.pause()
        self.sendMessage(b'ABOU')

    def getFirmware(self):
        """Returns the firmware version in YYYYMMDD format
        """
        self.sendMessage(b"FIRM")
        self.pause()
        return self.getResponse(timeout=1.0).replace(b";", b"")

    def setEventThresholds(self, threshList=()):
        """This takes some time (requires switching the BBTK to STM mode)
        """
        time.sleep(1.0)
        self.sendMessage(b'SEPV')
        time.sleep(5)  # it takes quite a while to switch to this mode
        for threshVal in threshList:
            time.sleep(0.5)
            self.sendMessage(threshVal) # threshVal must be byte, not str

    def getEventThresholds(self):
        self.sendMessage(b"GEPV")
        self.pause()
        reply = self.getResponse(timeout=5.0)
        if reply == '':
            return []
        else:
            reply = reply.replace(b';\n', b'').split(b',')
        return reply

    def setSmoothing(self, smoothStr):
        """By default the BBTK is set to smooth inputs
        (for CRT screens and noisy mics this is good)
        and this results in a delay of 20ms per channel.

        BBTK.setSmoothing('0'*8)  # turns off smoothing on all
        BBTK.setSmoothing('1'*8)  # turns on smoothing on all
        BBTK.setSmoothing('0110000')  # turns on smoothing for mic2 and opto4

        The channel orders are these (from BBTKv2 manual):
            [mic1 mic2 opto4 opto3 opto2 opto1 n/a n/a]
        """
        self.sendMessage(b'SMOO')
        self.pause()
        self.sendMessage(smoothStr)

    def clearMemory(self):
        """Clear the stored data from a previous run.
        This should be done before collecting a further timing data
        """
        self.sendMessage(b'SPIE')
        self.pause()
        reply = self.getResponse(timeout=10)
        # should return either FRMT or ESEC to indicate it started
        if reply.startswith(b'FRMT'):
            logging.info("BBTK.clearMemory(): "
                         "Starting full format of BBTK memory")
        elif reply.startswith(b'ESEC'):
            logging.info("BBTK.clearMemory(): "
                         "Starting quick erase of BBTK memory")
        else:
            logging.error("BBTK.clearMemory(): "
                          "didn't get a reply from %s" % str(self.com))
            return False
        # we aren't in a time-critical period so flush messages
        logging.flush()
        # now wait until we get told 'DONE'
        self.com.timeout = 20
        retVal = self.com.readline()
        if retVal.startswith(b"DONE"):
            logging.info("BBTK.clearMemory(): completed")
            # we aren't in a time-critical period so flush messages
            logging.flush()
            return True
        else:
            logging.error("BBTK.clearMemory(): "
                          "Stalled waiting for %s" % str(self.com))
            # we aren't in a time-critical period so flush messages
            logging.flush()
            return False

    def recordStimulusData(self, duration):
        """Record data for a given duration (seconds) and return a list of
        events that occurred in that period.
        """
        # we aren't in a time-critical period so flush messages
        self.sendMessage(b"DSCM")
        logging.flush()
        time.sleep(5.0)
        self.sendMessage(b"TIML")
        logging.flush()
        self.pause()
        # BBTK expects this in microsecs
        self.sendMessage(b"%i" % int(duration * 1000000), autoLog=False)
        self.pause()
        self.sendMessage(b"RUDS")
        logging.flush()

    def getEvents(self, timeout=10):
        """Look for a string that matches SDAT;\n.........EDAT;\n
        and process it as events
        """
        foundDataStart = False
        t0 = time.time()
        while not foundDataStart and time.time() - t0 < timeout:
            startLine = self.com.readline()
            if startLine == b'\n':
                startLine = self.com.readline()
            if startLine.startswith(b'SDAT'):
                foundDataStart = True
                logging.info("BBTK.getEvents() found data. Processing...")
                logging.flush()  # we aren't in a time-critical period
                break
        # check if we're processing data
        if not foundDataStart:
            logging.warning("BBTK.getEvents() found no data "
                            "(SDAT was not found on serial port inputs")
            return []

        # helper function to parse time and event code
        def parseEventsLine(line, lastState=None):
            """Returns a list of dictionaries, one for each change
            detected in the state
            """
            state = line[:12]
            timeSecs = int(line[-14:-2]) / 10.0**6
            evts = []
            evt = ''
            if lastState is None:
                evts.append({'evt': '',
                             'state': state,
                             'time': timeSecs})
            else:
                for n in evtChannels:
                    if state[n] != lastState[n]:
                        if chr(state[n]) =='1':
                            evt = evtChannels[n] + "_on"
                        else:
                            evt = evtChannels[n] + "_off"
                        evts.append({'evt': evt,
                                     'state': state,
                                     'time': timeSecs})
            return evts

        # we've been sent data so work through it
        events = []
        eventLines = []
        lastState = None
        # try to read from port
        self.pause()
        self.com.timeout = 5.0
        nEvents = int(self.com.readline()[:-2])  # last two chars are ;\n
        self.com.readline()[:-2]  # microseconds recorded (ignore)
        self.com.readline()[:-2]  # samples recorded (ignore)
        while True:
            line = self.com.readline()
            if line.startswith(b'EDAT'):  # end of data stream
                break
            events.extend(parseEventsLine(line, lastState))
            lastState = events[-1]['state']
            eventLines.append(line)
        if nEvents != len(eventLines):
            msg = "BBTK reported %i events but told us to expect %i events!!"
            logging.warning(msg % (len(events), nEvents))
        logging.flush()  # we aren't in a time-critical period
        return events

    def setResponse(self, sensor=None, outputPin = None, testDuration = None,
                    responseTime=None, nTrials=None,
                    responseDuration = None):
        """
        Sets Digi Stim Capture and Response (DSCAR) for BBTK.

        :param sensor: Takes string for single sensor, and tuple or list of strings for multiple sensors, or
                        a list of lists (or tuples) for multiple events
        :param outputPin: Takes string for single output, and tuple or list of strings for multiple outputs
        :param testDuration: The duration of the testing session in seconds
        :param responseTime: Time in seconds from stimulus capture that robotic actuator should respond
        :param nTrials: Number of trials for testing session
        :param responseDuration: Time in seconds that robotic actuator should stay activated for each response
        """

        def sensorValidator(sensor):
            """Sensor name validation."""
            if type(sensor) is str:
                sensor = [sensor,]
            for sensors in sensor:
                if sensors not in sensorDict.keys():
                    raise KeyError(
                        "{} is not a valid sensor name. Choose from the following: {}".format(sensors, list(sensorDict.keys())))
            if len(sensor) != len(set(sensor)):
                raise ValueError("Duplicate sensors are not allowed. Please use unique sensor names. E.g., {}"
                                 .format(list(set(sensor))))

        # Create sensor codes
        def createSensorCode(sensor, eCodes, idx):
            """Creates event codes for trial list based on sensors requested."""
            idx += 1
            key = 'event' + str(idx)  # Get dict key
            eCodes[key] = '0' * 12
            if type(sensor) is str:
                sensor = [sensor, ]
            if sensor is not None:
                if type(sensor) in allowedListTypes:
                    for sensors in sensor:
                        eCodes[key] = eCodes[key][:sensorDict[sensors]] + '1' + eCodes[key][sensorDict[sensors] + 1:]
            return eCodes

        # Check sensor and output param casing
        allowedListTypes = (type(()), type([]))
        noneTypes = ['', None, 'None', 'none', False]
        logging.info("Converting sensor and output names to lower case.")
        if sensor in noneTypes:
            sensor = None
        if type(sensor) == tuple:
            sensor = list(sensor)
        if outputPin in noneTypes:
            outputPin = None
        if sensor is not None and any(type(elements) in allowedListTypes for elements in sensor):  # list of lists
            if not all(type(elements) in allowedListTypes for elements in sensor):
                raise ValueError("For more than one event type, sensors must be list of lists.")
            if any(len(elements) > 12 for elements in sensor):
                raise ValueError("You can only set 12 sensor values for each event.")
            if len(sensor) > 3:
                raise ValueError("You can set sensors for a maximum of 3 events. "
                                 "You have created {} events.".format(len(sensor)))
            for idx, lists in enumerate(sensor):
                if type(sensor[idx]) == type(()):
                    sensor[idx] = list(sensor[idx])
                if type(sensor[idx]) == type([]):
                    for nextIdx, elements in enumerate(sensor[idx]):
                        sensor[idx][nextIdx] = sensor[idx][nextIdx].lower()
        elif sensor is not None and type(sensor) in allowedListTypes:  # Single list of sensors
            if len(sensor) > 12:
                raise ValueError("You can only set 12 sensor values for each event.")
            sensor = [sensors.lower() for sensors in sensor]
        elif sensor is not None:  # Single string
            sensor = sensor.lower()
        if type(sensor) in allowedListTypes and len(sensor) > 12:
            raise ValueError("You can only set 12 sensor values.")
        # Check outputs
        if not outputPin is None and type(outputPin) in allowedListTypes:
            outputPin = [outputs.lower() for outputs in outputPin]
        elif not outputPin is None:
            outputPin = outputPin.lower()
        # Create sensor and outputPin dicts
        sensorDict = dict(zip(
            ['keypad4', 'keypad3', 'keypad2', 'keypad1', 'opto4',
             'opto3', 'opto2', 'opto1', 'ttlin2', 'ttlin1', 'mic2','mic1'],
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]))
        outputDict = dict(
            zip(['actclose4', 'actclose3', 'actclose2', 'actclose1', 'ttlout2', 'ttlout1', 'sounder2', 'sounder1'],
                [0, 1, 2, 3, 4, 5, 6, 7]))
        # Check sensor parameters
        if sensor is None:
            logging.info("Setting BBTK pattern matching to 'INDI' - respond to any trigger")

        # Validate sensor names
        if any(type(elements) == type([]) for elements in sensor):
            for lists in sensor:
                sensorValidator(lists)
        else:
            sensorValidator(sensor)
        # Check output pin parameters
        if outputPin is None:
            raise ValueError("None values not accepted as outputs. OutputPin argument requires string e.g., 'TTLout1'.")
        if type(outputPin) in allowedListTypes and len(outputPin) > 8:
            raise ValueError("You can only set 8 sensor values. You have provided {} values.".format(len(outputPin)))
        if type(outputPin) in allowedListTypes:
            for outputs in outputPin:
                if not outputs in outputDict.keys():
                    raise KeyError(
                        "{} is not a valid output pin name. Choose from the following: {}".format(outputs, list(outputDict.keys())))
            if len(outputPin) != len(set(outputPin)):
                raise ValueError("Duplicate output pins are not allowed. Please use unique output pin names. E.g., {}"
                                 .format(list(set(outputPin))))
        if not type(outputPin) in allowedListTypes and not outputPin in outputDict.keys():
            raise KeyError("{} is not a valid output pin name. Choose from the following: {}".format(outputPin, list(outputDict.keys())))
        # Check timing parameters
        if testDuration is None:
            raise ValueError("Please provide a test time duration (in seconds)")
        if responseTime is None:
            raise ValueError("Please provide a time (in seconds) for the Robot Key Actuator to respond.")
        if responseDuration is None:
            raise ValueError("Please provide a duration (in seconds) for the Robot Key Actuator to respond.")
        # Create event lists from sensors
        sensorCodes = dict(zip(['event1', 'event2', 'event3'], ['9' * 12, '9' * 12, '9' * 12]))
        if any(type(elements) == type([]) for elements in sensor):
            for idx, lists in enumerate(sensor):
                sensorCodes = createSensorCode(lists, sensorCodes, idx)
        else:
            sensorCodes = createSensorCode(sensor, sensorCodes, 0)
        # Create output codes
        if outputPin in allowedListTypes:
            outputCode = '00000000'
            for outputs in outputPin:
                outputCode = outputCode[:outputDict[outputs]] + '1' + outputCode[outputDict[outputs]+1:]
        else:
            outputCode = '00000000'[:outputDict[outputPin]] + '1' + '00000000'[outputDict[outputPin]+1:]
        # Create trialList for BBTK trials
        trialList = '{input},{responseT},{output},{responseD}\r\n'.format(
            input=','.join(sensorCodes.values()),
            responseT=int(responseTime * 1000000),
            output=outputCode,
            responseD=int(responseDuration * 1000000))*nTrials
        # Write trials to disk for records
        saveTrials = open('trialList.txt', 'w')
        saveTrials.write(trialList)
        saveTrials.close()
        # Send instructions to program BBTK
        self.sendMessage(b'PDCR')  # program DSCAR
        self.pause()
        self.sendMessage(b'STYP') # Type of response
        self.pause()
        if sensor is None:
            self.sendMessage(b'INDI')  # Set to respond to any trigger
        else:
            self.sendMessage(b'PATT')  # Set to exact port trigger match
        self.pause()
        if int(testDuration) >= 0:
            self.sendMessage(b'TIML')
            self.pause()
            self.sendMessage(b"%i" % int(testDuration * 1000000))
            self.pause()
        if nTrials:
            self.sendMessage(trialList)
            time.sleep(5)
        self.sendMessage(b'PCCR')  # Sequence complete
        self.pause()
        if int(testDuration) == 0:
            self.sendMessage(b'RUSR')  # DSRE
        else:
            self.sendMessage(b'RUCR')  # DSCAR
        self.pause()

if __name__ == "__main__":

    logging.console.setLevel(logging.DEBUG)

    BBTK = BlackBoxToolkit('/dev/ttyACM0')
    print(BBTK.com)  # info about the com port that's open

    time.sleep(0.2)
    BBTK.showAbout()

    time.sleep(0.1)
    BBTK.setEventThresholds([20] * 8)
    time.sleep(2)
    print(('thresholds:', BBTK.getEventThresholds()))

    BBTK.clearRAM()
    time.sleep(2)
    print('leftovers: %s' % BBTK.com.read(BBTK.com.in_waiting()))
