"""Base class for serial devices. Includes some convenience methods to open
ports and check for the expected device
"""
# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import time
from psychopy import logging
from psychopy.hardware import serialdevice

evtChannels = {
    0:"Key4",
    1:"Key3",
    2:"Key2",
    3:"Key1",
    4:"Opto4",
    5:"Opto3",
    6:"Opto2",
    7:"Opto1",
    8:"TTL2",
    9:"TTL1",
    10:"Mic2",
    11:"Mic1",
    }

class BlackBoxToolkit(serialdevice.SerialDevice):
    """A base class for serial devices, to be sub-classed by specific devices
    """
    name='BlackBoxToolkit'
    longName ="BlackBoxToolkit 2"
    driverFor = ["BlackBoxToolkit 2"] #list of supported devices (if more than one supports same protocol)

    def __init__(self, port=None, sendBreak=False):
        #if we're trying to send the break signal then presumably the device is sleeping
        if sendBreak:
            checkAwake = False
        else:
            checkAwake = True
        #run initialisation
        super(BlackBoxToolkit, self).__init__(port,
            baudrate=460800, eol="\n",
            parity='N',    # enable parity checking
            pauseDuration = 0.5,
            checkAwake=checkAwake,
            )
        if sendBreak:
            self.sendBreak()
            time.sleep(3.0) #give time to reset

    def sendBreak(self):
        """Send a break event to reset the box if needed
        (can be done by setting sendBreak=true at __init__)
        """
        self.com.sendBreak()

    def isAwake(self):
        """Checks that the black box returns "BBTK;\n" when probed with "CONN"
        """
        self.pause()
        self.sendMessage('CONN')
        self.pause()
        reply = self.getResponse(timeout=1.0)
        return reply=='BBTK;\n'

    def showAbout(self):
        """Will show the 'about' screen on the LCD panel for 2 seconds
        """
        self.pause()
        self.sendMessage('ABOU')

    def getFirmware(self):
        """Returns the firmware version in YYYYMMDD format
        """
        self.sendMessage("FIRM")
        self.pause()
        return self.getResponse(timeout=0.5).replace(";","")

    def setEventThresholds(self, threshList=[]):
        """This takes some time (requires switching the BBTK to STM mode)
        """
        time.sleep(1.0)
        self.sendMessage('SEPV')
        time.sleep(5) #it takes quite a while to switch to this mode
        for threshVal in threshList:
            time.sleep(0.5)
            self.sendMessage(str(threshVal))

    def getEventThresholds(self):
        self.sendMessage("GEPV")
        self.pause()
        reply = self.getResponse(timeout=5.0)
        if reply == '':
            return []
        else:
            reply = reply.replace(';\n','') #remove final ';'
            reply = reply.split(',')
        return reply

    def setSmoothing(self, smoothStr):
        """By default the BBTK is set to smooth inputs
        (for CRT screens and noisy mics this is good)
        and this results in a delay of 20ms per channel.

        BBTK.setSmoothing('0'*8) #turns off smoothing on all
        BBTK.setSmoothing('1'*8) #turns on smoothing on all
        BBTK.setSmoothing('0110000') #turns on smoothing for mic2 and opto4

        The channel orders are these (from BBTKv2 manual):
            [mic1 mic2 opto4 opto3 opto2 opto1 n/a n/a]
        """
        self.sendMessage('SMOO')
        self.pause()
        self.sendMessage(smoothStr)
    def clearMemory(self):
        """
        """
        self.sendMessage('SPIE')
        self.pause()
        reply = self.getResponse(timeout=10)
        #should return either FRMT or ESEC to indicate it started
        if reply.startswith('FRMT'):
            logging.info("BBTK.clearMemory(): Starting full format of BBTK memory")
        elif reply.startswith('ESEC'):
            logging.info("BBTK.clearMemory(): Starting quick erase of BBTK memory")
        else:
            logging.error("BBTK.clearMemory(): didn't get a reply from %s" %(str(self.com)))
            return False
        logging.flush() #we aren't in a time-critical period so flush messages
        #now wait until we get told 'DONE'
        self.com.setTimeout(20)
        retVal = self.com.readline()
        if retVal.startswith("DONE"):
            logging.info("BBTK.clearMemory(): completed")
            logging.flush() #we aren't in a time-critical period so flush messages
            return True
        else:
            logging.error("BBTK.clearMemory(): Stalled waiting for %s" %(str(self.com)))
            logging.flush() #we aren't in a time-critical period so flush messages
            return False

    def recordStimulusData(self, duration):
        """Record data for a given duration (seconds) and return a list of
        events that occured in that period.
        """
        self.sendMessage("DSCM")
        logging.flush() #we aren't in a time-critical period so flush messages
        time.sleep(5.0)
        self.sendMessage("TIML")
        logging.flush() #we aren't in a time-critical period so flush messages
        self.pause()
        self.sendMessage("%i" %(int(duration*1000000)), autoLog=False) #BBTK expects this in microsecs
        self.pause()
        self.sendMessage("RUDS")
        logging.flush() #we aren't in a time-critical period so flush messages

    def getEvents(self, timeout=10):
        """Look for a string that matches SDAT;\n.........EDAT;\n
        and process it as events
        """
        foundDataStart=False
        t0=time.time()
        while not foundDataStart and (time.time()-t0)<timeout:
            if self.com.readline().startswith('SDAT'):
                foundDataStart=True
                logging.info("BBTK.getEvents() found data. Processing...")
                logging.flush() #we aren't in a time-critical period so flush messages
                break
        #check if we're processing data
        if not foundDataStart:
            logging.warning("BBTK.getEvents() found no data (SDAT was not found on serial port inputs")
            return []

        #helper function to parse time and event code
        def parseEventsLine(line, lastState=None):
            """Returns a list of dictionaries, one for each change detected in the state
            """
            state = line[:12]
            timeSecs = int(line[-14:-2])/10.0**6
            evts=[]
            evt=''
            if lastState is None:
                evts.append({'evt':'', 'state':state, 'time':timeSecs})
            else:
                for n in evtChannels.keys():
                    if state[n]!=lastState[n]:
                        if state[n]=='1':
                            evt = evtChannels[n]+"_on"
                        else:
                            evt = evtChannels[n]+"_off"
                        evts.append({'evt':evt, 'state':state, 'time':timeSecs})
            return evts

        #we've been sent data so work through it
        events=[]
        eventLines=[]
        lastState=None
        #try to read from port
        self.pause()
        self.com.setTimeout(2.0)
        nEvents = int(self.com.readline()[:-2]) #last two chars are ;\n
        self.com.readline()[:-2] # microseconds recorded (ignore)
        self.com.readline()[:-2] #samples recorded (ignore)
        while True:
            line = self.com.readline()
            if line.startswith('EDAT'): #end of data stream
                break
            events.extend(parseEventsLine(line, lastState))
            lastState = events[-1]['state']
            eventLines.append(line)
        if nEvents != len(eventLines):
            logging.warning("BBTK reported %i events but told us to expect %i events!!" %(len(events), nEvents))
        logging.flush() #we aren't in a time-critical period so flush messages
        return events

if __name__=="__main__":

    logging.console.setLevel(logging.DEBUG)

    BBTK = BlackBoxToolkit('/dev/ttyACM0')
    print BBTK.com #info about the com port that's open

    time.sleep(0.2)
    BBTK.showAbout()

    time.sleep(0.1)
    BBTK.setEventThresholds([20]*8)
    time.sleep(2)
    print 'thresholds:', BBTK.getEventThresholds()

    BBTK.clearRAM()
    time.sleep(2)
    print 'leftovers:', BBTK.com.read(BBTK.com.inWaiting())
