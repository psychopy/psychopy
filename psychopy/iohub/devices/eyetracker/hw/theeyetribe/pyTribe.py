# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 17:13:14 2014

@author: zahm
"""
from weakref import proxy
import gevent
from gevent import sleep, socket, queue
from gevent.server import StreamServer
try:
    import ujson as json
except Exception:
    import json
from ..... import print2err,printExceptionDetailsToStdErr,Computer,OrderedDict

getTime=Computer.getTime

class TheEyeTribe(object):
    """
    TheEyeTribe class is the client side interface to the TheEyeTribe 
    eye tracking device server.
    """

    # define the dict format for tracker set msgs
    set_tracker_prototype = {
        u"category": u'tracker',
        u"request": u'set',
        u"values": {}
        }
        
    # define the dict format for tracker get msgs
    get_tracker_prototype = {
        "category": 'tracker',
        "request": 'get',
        "values": []
        }

    # see http://dev.theeyetribe.com/api/#cat_tracker
    # list of valid get keys. If a get msg is sent that includes 
    # a key not in this list, that key value pair is ignored and not sent.
    tracker_get_values = [
        'push',
        'heartbeatinterval',
        'version',
        'trackerstate',
        'framerate',
        'iscalibrated',
        'iscalibrating',
        'calibresult',
        'frame',
        'screenindex',
        'screenresw',
        'screenresh',
        'screenpsyw',
        'screenpsyh'
    ]

    # list of valid set keys. If a set msg is sent that includes 
    # a key not in this list, that key value pair is ignored and not sent.
    tracker_set_values = [
        'push',
        'version',
        'screenindex',
        'screenresw',
        'screenresh',
        'screenpsyw',
        'screenpsyh'
    ]

    tracker_calibration_values = [
        'start',        
        'pointstart',
        'pointend',
        'clear'
    ]
    # tracker status states
    TRACKER_CONNECTED = 0 # Tracker device is detected and working
    TRACKER_NOT_CONNECTED = 1 #	Tracker device is not detected
    TRACKER_CONNECTED_BADFW = 2 # Tracker device is detected but not working due to wrong/unsupported firmware
    TRACKER_CONNECTED_NOUSB3 = 3 # Tracker device is detected but not working due to unsupported USB host
    TRACKER_CONNECTED_NOSTREAM = 4 # Tracker device is detected but not working due to no stream could be received

    # Tracker reply status codes (other than standard http response codes):
    #
    # Calibration state has changed. Connected clients should update 
    # themselves.	    
    CALIBRATION_CHANGED = 800    
    # Active display index has changed in multi screen setup. Connected 
    # clients should update themselves.
    DISPLAY_CHANGE = 801
    # The state of the connected tracker device has changed. 
    # Connected clients should update themselves.	
    TRACKER_STATE_CHANGE = 802
    
    # Tracker sample (frame) states
    #
    # Tracker is calibrated and producing on-screen gaze coordinates.
    # Eye control is enabled.
    STATE_TRACKING_GAZE	= 0x1 # true: ((state & mask) != 0)
                              # false: ((state & mask) == 0)
    # Tracker possibly calibrated and is tracking both eyes,
    # including pupil and glint.
    STATE_TRACKING_EYES = 0x2 # true: ((state & mask) != 0)
                              # false: ((state & mask) == 0)
    # Tracker possibly calibrated and is tracking presence of user.
    # Presence defined as face or single eye.
    STATE_TRACKING_PRESENCE = 0x4 # true: ((state & mask) != 0)
                                  # false: ((state & mask) == 0)
    # Tracker failed to track anything in this frame.
    STATE_TRACKING_FAIL = 0x8 # true: ((state & mask) != 0)
                              # false: ((staself._eyetribe.te & mask) == 0)
    # Tracker has failed to detect anything and tracking is now lost.
    STATE_TRACKING_LOST = 0x10 # true: ((state & mask) != 0)
                               # false: ((state & mask) == 0)
    # STATE_TRACKING_FIXATED state is not standard for eyetribe; added for iohub
    # integration so that the eyetribe frame.fix bool can be combined
    # with frame.state, which is then stored in the iohub sample state field.
    # Tracker has failed to detect anything and tracking is now lost.
    STATE_TRACKING_FIXATED = 0x20 # true: ((state & mask) != 0)
                               # false: ((state & mask) == 0)

    def __init__(self, server_ip='127.0.0.1', server_port=6555):
        """
        When an instance of TheEyeTribe client interface is created,
        it creates two greenlets, a EyeTribeTransportManager and a 
        HeartbeatPump.
        """
        # _tracker_state is used to hold the last value received from the
        # eye tracker server for any tracker get keys sent. So as info
        # is requested from the server, the _tracker_state will hold a
        # up to date representation of any eye tracker server values returned
        # by the server based on get requests from the client.
        self._tracker_state={}
        
        self._transport_manager = EyeTribeTransportManager(self,
                                                           address=server_ip,
                                                           port=server_port)
        self._transport_manager.start()
        
        #self.sendSetMessage(push=True, version=1)

        self._heartbeat = HeartbeatPump(self._transport_manager)
        self._heartbeat.start()
        
        #self.sendGetMessage(*self.tracker_get_values)
        
    @property
    def tracker_status(self):
        self.sendGetMessage('trackerstate')
        return self._tracker_state.get('trackerstate','Unknown')   
        
    @property
    def server_response_count(self):
        return self._transport_manager.server_response_count
        
    @property
    def tracker_state(self):
        return self._tracker_state
        
    def handleServerMsg(self,msg):
        #print2err("<<<<<<<<<<<<<<<<<<<<<")
        #print2err("handleServerMsg:\nTime: ",getTime())
        #print2err("Message: ",msg)
        #print2err("<<<<<<<<<<<<<<<<<<<<\n")
        msg_category=msg.get('category')
        msg_statuscode=msg.get('statuscode')
        if msg_statuscode != 200:            
            if msg_statuscode == self.TRACKER_STATE_CHANGE:
                # get updated eye tracker values
                self.sendGetMessage(*self.tracker_get_values)
            elif msg_statuscode == self.DISPLAY_CHANGE:
                print2err("DISPLAY_CHANGE REPLY CODE: NOT HANDLED")
            elif msg_statuscode == self.CALIBRATION_CHANGED:
                print2err("CALIBRATION_CHANGED REPLY CODE: NOT HANDLED")
            else:
                # TODO Handle msg status code error values
                print2err( '***********')
                print2err( 'SERVER REPLY ERROR: ',msg_statuscode)
                print2err( msg)
                print2err( 'Server Msg not being processed due to error.')
                print2err( '***********\n')
                return False

        if msg_category == u'heartbeat':
            return True
        elif msg_category == u'tracker':
            request_type=msg.get('request') 
            if request_type == u'get': 
                if msg.get('values',{}).get('frame'): 
                    return self.processSample(msg)
                for k,v in msg.get('values',{}).iteritems():
                    #print2err('* Updating client.tracker_state[{0}] = {1}'.format(k,v))
                    self.tracker_state[k]=v
                    return True    
            elif request_type == u'set': 
                #print2err( 'SET Rx received from server: ',msg)
                # TODO check status field for any errors
                return True        
        elif msg_category == u'calibration':
            request_type=msg.get('request') 
            #print2err( '::::::::::: Calibration Result: ', msg.get('values',{}).get('calibresult'))            
            if request_type == u'pointend': 
                if msg.get('values',{}).get('calibresult'): 
                    #print2err('::::::::::: Calibration Result: ', msg)                   
                    return self.processCalibrationResult(msg)
            elif request_type == u'pointstart': 
                #print2err( '==========Calibration response: ', msg)
                return True

        print2err('!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print2err('Unhandled Server packet category [{0}] received by client. Full msg contents:\n\n{1}\n<<'.format(msg_category,msg))               
        print2err('!!!!!!!!!!!!!!!!!!!!!!!!!!')
        
    def sendSetMessage(self, **kwargs):
        """
        Send a Set Tracker msg to the server. any kwargs passed into this method
        are used as the key : value pairs that want to be sent to the server.
        
        For example:
        
        eyetracker.sendSetMessage(screenresw=1920,screenresh=1080) 
        
        would send a msg informing the tracker what the client's display 
        resolution is.        
        """
        send_values={}
        for k, v in kwargs.iteritems():
            if k not in self.tracker_set_values:
                print2err('**setTrackerMsg warning": Invalid tracker set value key \
                    [{0}] with value [{1}]. Ignoring'.format(k, v))
            else:
                send_values[k] = v

        self.set_tracker_prototype['values']=send_values
        send_str=json.dumps(self.set_tracker_prototype)
        self._transport_manager.send(send_str)
        self.set_tracker_prototype['values'] = None

    def sendGetMessage(self, *args):
        """
        Send a Get Tracker msg to the server. any args passed into this method
        are used as the keys that are to be sent to the server so the current
        value of each can be returned.
        
        For example:
        
        eyetracker.sendGetMessage('trackerstate','framerate') 
        
        would send a msg asking for the current eye tracker state and 
        framerate.
        """
        send_values=[]
        for k in args:
            if k not in self.tracker_get_values:
                print2err('**getTrackerMsg warning": Invalid tracker get value key \
                    [{0}]. Ignoring'.format(k))
            else:
                send_values.append(k)

        self.get_tracker_prototype['values'] = send_values
        send_str=json.dumps(self.get_tracker_prototype)
        self._transport_manager.send(send_str)
        self.get_tracker_prototype['values']=None

    def processSample(self,frame_dict):
        """
        Process an eye tracker sample frame that has been received.
        """
        #TODO proper handling of sample data
        print2err('++++++++++++++++')
        print2err('Received Sample:\nTime: ',getTime())
        print2err('Frame: ',frame_dict)
        print2err('++++++++++++++++')
        #sample_frame=frame_dict.get('values',{}).get('frame')
        
    def sendCalibrationMessage(self, request_type, **kwargs):
        """
        Examples:
            sendCalibrationMessage('start', pts=9)
            sendCalibrationMessage('pointstart',x=500,y=200)
            sendCalibrationMessage('pointend')
        """
        # TODO How to handle getting calibration response values from tracker
        
        if request_type not in self.tracker_calibration_values:
            # Throw error, return error code??
            print2err('Unknown calibration request_type: ',request_type)
            return False
            
        calreq=OrderedDict(category='calibration', request = request_type)
        if kwargs:
            calreq['values'] = OrderedDict(sorted(kwargs.items(), key = lambda t:t[0]))
        send_str=json.dumps(calreq)
        print2err("send_str: ",send_str)
        self._transport_manager.send(send_str)
        
        
    def calibrate(self):
        """
        Runs complete calibration process according to the TheEyeTribe APIs
        """
        self.sendCalibrationMessage('clear')
        gevent.sleep(self.sleepInterval)        
        self.sendCalibrationMessage('start', pointcount=self.calibrationPoints)
        gevent.sleep(self.sleepInterval)        
        sx_pos= [self.sw*0.25,self.sw*0.5,self.sw*0.75]
        sy_pos= [self.sh*0.25,self.sh*0.5,self.sh*0.75]

        for lx in sx_pos:
            for ly in sy_pos:
                self.sendCalibrationMessage('pointstart', x = int(lx), y = int(ly))
                gevent.sleep(self.sleepInterval)        
                self.sendCalibrationMessage('pointend')
            #gevent.sleep(self.sleepInterval)

    def processCalibrationResult(self, calibrationResult):
        """
        Process the calibration result
        """
        return True
        
    def close(self):
        """
        Close the eye tracker client by closing the transport_manager and
        heartbeat greenlets.
        """
        self._heartbeat.stop()
        self._transport_manager.stop()
        
#
########
#

class EyeTribeTransportManager(gevent.Greenlet):
    """
    EyeTribeTransportManager is used to handle tx and rx with the 
    eye tracker sever. This class is created by the TheEyeTribe class
    when an instance is created.
    
    The client_interface arg is the TheEyeTribe class instance that is
    creating the EyeTribeTransportManager.
    
    EyeTribeTransportManager creates a tcpip connection to the 
    eye tracker server which is used to send messages to the server
    as well as receive responses from the server.
    
    The HeartbeatPump and TheEyeTribe classes send msg's to the eye tracker
    server by calling EyeTribeTransportManager.send(msg_contents). The msg
    is added to the _tracker_requests_queue queue attribute.
    
    As the EyeTribeTransportManager class runs, it checks for any new msg's
    in the _tracker_requests_queue and sends any that are found to the server 
    via the _socket.
    
    As the EyeTribeTransportManager class runs, it is also checking for any 
    incoming data from the eye tracker server. If any is read, it is parsed into
    reply dict's. The type of server reply received is used to determine
    if it should be passed back to the HeartbeatPump or to the TheEyeTribe.
    """
    def __init__(self, client_interface,address='127.0.0.1',port=6555):
        self.server_response_count=0
        self._client_interface=proxy(client_interface)
        gevent.Greenlet.__init__(self)
        self._tracker_requests_queue = queue.Queue()
        self._running = False
        self._socket = self.createConnection(host=address, port=port)
        
    def _run(self):
        self._running = True
        self.server_response_count=0
        msg_fragment=''
        while self._running:
            # used to know if the socket.sendall call timed out or not.
            tx_count=-1
            
            # Check for new messages to be sent to the server. 
            # Send them if found.
            try:
                to_send=self._tracker_requests_queue.get_nowait()
                #print2err('>>>>>>>>>>>>')
                #print2err("SENDING TO TET:\nTime: ",getTime())
                #print2err("Message: ",to_send)
                tx_count=self._socket.sendall(to_send)
                #print2err('>>>>>>>>>>>>\n')
                
            except gevent.queue.Empty, e:
                pass
            except Exception, e:
                print2err('MANAGER ERROR WHEN SENDING MSG:',e)
            #finally:
                # Yield to any other greenlets that are waiting to run.
                #gevent.sleep(0.0)
            
            # if a message was sent over the socket to the server, check
            # to see if any msg replies have been received from the server.
            reply=None
            try:
                reply=self._socket.recv(512)
                if reply:
                    multiple_msgs=reply.split('\n')
                    multiple_msgs=[m for m in multiple_msgs if len(m)>0]
                    for m in multiple_msgs:
                        m='%s%s'%(msg_fragment,m)
                        try:
                            mdict=json.loads(m)
                            self._client_interface.handleServerMsg(mdict)
                            msg_fragment=''
                            self.server_response_count += 1
                        except Exception:
                            msg_fragment=m
            except socket.timeout:
                pass
            except socket.error, e:
                if e.errno==10035 or e.errno==9:
                    pass
                else:
                    print2err( ' socket.error: ',type(e))
                    raise e
            except Exception, e:    
                print2err('>>>>>>>>>>>>')
                print2err('MANAGER ERROR RECEIVING REPLY MSG:',e)
                print2err('reply: ',reply)
                print2err( '<<<<<<<<<<<<')
            finally:
                gevent.sleep(0.001)
        
        # Greenlet has stopped running so close socket.
        self._running=False
        self._socket.close()

    def send(self,msg):
        """
        send is called by other classes that want to send a msg to the 
        eye tracker server. the msg is put in a queue that is emptied 
        as the EyeTribeTransportManager runs.
        """
        if not isinstance(msg,basestring):
            msg=json.dumps(msg)
        self._tracker_requests_queue.put(msg)        
        
    def createConnection(self, host='127.0.0.1', port=6555):
        # Open a socket to the eye tracker server
        try:
            hbp = socket.socket()
            hbp.connect((host, port))
            hbp.settimeout(0.01)
            return hbp
        except Exception, e:
            print2err('** Error creating exception:', e)
            return None

    def stop(self):
        self._socket.close()
#
########
#

class HeartbeatPump(gevent.Greenlet):
    """
    HeartbeatPump keeps theeyetribse sever alive.
    """
    
    get_heartbeat_rate={"category": "tracker", "request" : "get",
                        "values": [ "heartbeatinterval" ]
                        }
    heartbeat={ 'category' : 'heartbeat' }                    
    def __init__(self,transport_manager,sleep_interval=3.0):
        """
        HeartbeatPump is used by TheEyeTribe client class to keep the server
        running. 
        
        transport_manager the instance of the EyeTribeTransportManager created
        prior to creating the TheEyeTribe instance.
        
        sleep_interval is the time to delay between sending heartbeats
        
        HeartbeatPump will run until it is stopped.
        """
        gevent.Greenlet.__init__(self)
        self._transport_manager = transport_manager
        self._running = False
        self.sleep_interval = sleep_interval
        
        # Convert the class message dict constants to the associated json
        # strings that will actually be sent.
        #
        HeartbeatPump.get_heartbeat_rate=json.dumps(self.get_heartbeat_rate)
        HeartbeatPump.heartbeat=json.dumps(self.heartbeat)
        self.pump()
    
    def getHeartbeatRate(self):
        '''
        request the rate the server is expecting to receive heartbeats at.
        '''
        self._transport_manager.send(self.get_heartbeat_rate)  

    def pump(self):
        """
        Send a heartbeat msg to the server.
        """
        self._transport_manager.send(self.heartbeat)  
        
    def _run(self):
        self._running = True
        #self.getHeartbeatRate() # get the heartbeet interval. TODO : use the
                                # val returned to override the default
                                # sleep_interval.
        while self._running:
            gevent.sleep(self.sleep_interval)
            self.pump()
            
    def stop(self):
        """
        Stops the Greenlet from sending heartbeat msg's.
        """
        self._running=False