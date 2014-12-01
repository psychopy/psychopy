from __future__ import print_function
from gevent import select, socket
import struct, collections
from highrestimer import getTime as _cobratime

#
## Cobra Eye Tracker Client Interface Class
#

class CobraEyeTrackerClient(object):
    """
    CobraEyeTrackerClient is used to receive sample data
    sent from a COBRA Server application. The COBRA Server
    **must** be running on the same computer as this client.
    
    Once a CobraEyeTrackerClient object is created, use
    open() to start receiving the eye sample data stream 
    from the server. Use close() to stop listening for any
    eye sample data.
    
    Implementation Notes
    ---------------------

    The COBRA Eye Tracking Server broadcasts one packet for each
    frame processed by the server. This data stream is broadcast 
    constantly while the server application runs.
    
    Each packet contains the contents of the EyeSample C structure 
    defined in et_server/source/eye.h. The python 'struct' module is
    used to convert the EyeSample byte stream into a list containing
    the value of each EyeSample C structure field. This in turn is
    converted into a namedtuple so that the eye sample data fields
    can be accessed by field names.
    
    Given the above, it is **critical** that the EyeSample C structure
    definition is correctly represented by the 
    CobraEyeTrackerClient.rawsamplestruct attribute. If the two
    do not match, an error will occur each time a sample is received 
    from the server, or the received data conversion will be corrupt. 

    The current expected EyeSample C structure is expected to be as
    follows (inner structs have been expanded)::

        typedef struct _EyeSample
        {
            double time = 0;	    // timestamp of eye sample		
            double tx_time = 0;	    // time data was broadcast by et_server app		
            unsigned long long frame_number;	// frame number of eye sample		
            double pupil_x = -1;		// raw (sensor) pupil center x			
            double pupil_y = -1;		// raw (sensor) pupil center y
            double pupil_area = -1;		// pupil centroid area
            int status = 0;		    // Status of eye sample. 0 == sample data should be valid. 
                                    // 1 == no eye data could be found for that sample.
        } EyeSample;


    """
    rawsamplestruct = struct.Struct("ddQdddi")
    rawsamplesize = rawsamplestruct.size
    EyeSample = collections.namedtuple("EyeSample", ("time", "tx_time", "frame_num", "pupil_x", "pupil_y", "pupil_area", "status", "delay"))
    lastpackettime = None
    activeserverthreshold = 1.0
    def __init__(self, address='', portnum=5444):
        """
        portnum must match port used by COBRA server. 
        Current default of 5444 is listed as unassigned
        as of Novemeber 2014.
        See http://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml?&page=92 
        """
        self._portnum = portnum
        self._address = address
        self._sock = None

    def open(self):
        """
        Opens the client socket that listens for sample data
        broadcast from the COBRA Server. This must be called
        before poll() will return any sample data. 
        """
        if self._sock:
            raise RuntimeWarning("CobraEyeTrackerClient socket already open. First use .close() to re open connection.")
            return True

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((self._address, self._portnum))
        #self._sock.setblocking(0)

    def close(self):
        """
        Closes the client socket that is listening for sample data
        broadcast from the COBRA Server. 
        """
        self.lastpackettime = None
        if self._sock:
            self._sock.close()
            self._sock = None

    def isServerActive(self):
        """
        If a broadcast package has been received from the cobra sever within
        the given time limit, the server is considered to be running,
        otherwise it is assumed that the server has shutdown.
        :return: bool
        """
        return self.lastpackettime is None or (self._sock and
                _cobratime() - self.lastpackettime < self.activeserverthreshold)

    def getTrackerTime(self):
        """
        Returns the current Cobra Eye Tracker Time (sec.msec format). 
        This time is based on the QPC API, and is the same timebase
        as the psychopy.clock.getTime() function.

        **IMPORTANT**: COBRA Server must be running on same computer
        as this client or time will be totally invalid.
        """
        return _cobratime()

    def getNextSample(self):
        """
        Returns any new udp broadcast packets received from the COBRA Server.
        Each packet is converted into a COBRA EyeSample before being returned. 
        """
        if self._sock:
            r, w, x = select.select([self._sock], [], [], self.activeserverthreshold)
            if r:
                CobraEyeTrackerClient.lastpackettime = self.getTrackerTime()
                rawsamplelist = list(self.rawsamplestruct.unpack(r[0].recv(self.rawsamplesize)))
                rawsamplelist.append(CobraEyeTrackerClient.lastpackettime - rawsamplelist[0])
                return self.EyeSample(*rawsamplelist)

    def __del__(self):
        self.close()

if __name__ == '__main__':
    import time
    POLLING_RATE = 0.002 # 2 msec
    NO_RX_TIMEOUT = 10.0 # If no data is received for this long, exit app.

    cobraclient = CobraEyeTrackerClient()
    cobraclient.open()

    print("CobraEyeTrackerClient saving samples to 'cobra_samples.dat'....")

    last_msg_time = cobraclient.getTrackerTime()
    scount=0
    with open('cobra_samples.dat', 'w') as fout:
        fout.write("\t".join(cobraclient.EyeSample._fields))
        fout.write('\n')
        
        fount_str_format = "\t".join(["{%d}"%(i) for i in range(len(cobraclient.EyeSample._fields))])
        fount_str_format+="\n"
         
        while cobraclient.isServerActive():
            s = cobraclient.getNextSample()
            if s:
                #last_msg_time = s.time
                scount+=1
                fout.write(fount_str_format.format(*s))
                if scount%24==0:
                    print("Received %d samples.\r"%(scount), end='')
                # don't swamp CPU with busy looping......
                #time.sleep(POLLING_RATE)

    print("CobraEyeTrackerClient Closed.")
    cobraclient.close()