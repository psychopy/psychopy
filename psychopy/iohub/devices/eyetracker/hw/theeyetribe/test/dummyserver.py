# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 14:20:02 2014

@author: Sol
"""
import gevent
from gevent import sleep, socket
from gevent.server import StreamServer
import json
from timeit import default_timer as getTime

# The dict format used to send a sample frame from the server to the
# connected client. The DummyServer just updates the time field of the dict
# each time a sample is sent.

sample_frame={
    "category": "tracker",
    "statuscode": 200,
    "values": {
        "frame" : {
            "time": getTime(),              #timestamp
            "fix": False,           #is fixated?
            "state": 1,             #32bit masked state integer
            "raw": {                  #raw gaze coordinates in pixels
                "x": 2,
                "y": 3
            },
            "avg": {                  #smoothed gaze coordinates in pix
                "x": 4,
                "y": 5
            },
            "lefteye": {
                "raw": {              #raw coordinates in pixels
                    "x": 6,
                    "y": 7
                },
                "avg": {              #smoothed coordinates in pix
                    "x": 8,
                    "y": 9
                },
                "psize": 1.1,       #pupil size
                "pcenter": {          #pupil coordinates normalized
                    "x": 2.2,
                    "y": 3.3
                }
            },
            "righteye": {
                "raw": {             #raw coordinates in pixels
                    "x": 1,
                    "y": 2
                },
                "avg": {             #smoothed coordinates in pix
                    "x": 3,
                    "y": 4
                },
                "psize": 1.1,     #pupil size
                "pcenter": {        #pupil coordinates normalized
                    "x": 2.2,
                    "y": 3.3
                }
            }
        }
    }
}

#
## FakeEyeTribeServer is used to simulate theeyetribe so I could test here.
## It is just an echo server that also sends a sample each time it get a tx. ;)
#

# this handler will be run for each incoming connection in a dedicated greenlet
def FakeEyeTribeServer(socket, address):
    # The dummy server just echo's back any msg's received from the client.
    # Each time a heartbeat msg is received, the server also sends a dummy
    # eye sample frame.The dummy server just runs until the script that created it
    # exits.
    while True:
        # check for any incoming msgs from the client.
        data = socket.recv(1024)
        if not data:
            # since the server is running in 'blocking' mode, 
            # if a recv call returns no data, the client must have
            # disconnected.
            break
        # echo back what was received.....
        rx_dict=json.loads(data)
        tx_str=json.dumps(rx_dict).replace('\n','')
        # The '\r\n' added to the end of the reply is a hack that should not be
        # needed when the real et server is used.
        socket.sendall(tx_str+'\r\n')

        if rx_dict.values()[0] == 'heartbeat':
            # If the msg recv was a heartbeat, also rend a pretend eye sample
            sample_frame['values']['frame']['time']=getTime()
            tx_str=json.dumps(sample_frame).replace('\n','')
            socket.sendall(tx_str+'\r\n')

def startDummyServer(address):
    server = StreamServer((address[0], address[1]), FakeEyeTribeServer)
    server.start()
    return server