# -*- coding: utf-8 -*-
"""
ioHub Python Module
.. file: ioHub/devices/network/__init__.py

fileauthor: Sol Simpson <sol@isolver-software.com>

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License 
(GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com>
"""

import gevent
import zmq.green as zmq
import copy
import msgpack
try:
    import msgpack_numpy as m
    m.patch()
except Exception:
    pass

from .. import Computer, Device, DeviceEvent
from ...constants import DeviceConstants,EventConstants
from ... import print2err,printExceptionDetailsToStdErr

class EventPublisher(Device):
    """
    The ioHub EventPublisher Device can be used to publish events created by any locally 
    monitored ioHub Devices to remote subscribing computers using tcp/ip. 
    (a list of event types that the EventPublisher Device will publish can be specified
    in the EventPublisher device config settings). 
    
    Other than specifiying that a EventPublisher device is desired during the experiment
    by adding the device configuration to the experiment's iohub_config.yaml,
    nothing else needs to be done during the experiment runtime. The EventPublisher
    device automatically handles publishing all requested event types to any
    connected RemoteEventSubscriber devices that have indicated interest in the
    event type being dispatched.
    """
    _packer=msgpack.Packer()
    pack=_packer.pack
    _unpacker=msgpack.Unpacker(use_list=True)
    unpack=_unpacker.unpack      
    feed=_unpacker.feed

    _newDataTypes=[]    
    EVENT_CLASS_NAMES=[]    
    DEVICE_TYPE_ID=DeviceConstants.EVENTPUBLISHER
    DEVICE_LABEL = 'EVENTPUBLISHER'
    __slots__=[e[0] for e in _newDataTypes]+['_zmq_context','_pub_socket','_sub_listener','_publishing_protocal','_sub_protocal']
    def __init__(self, *args,**kwargs):
        self._pub_socket=None
        try:            
            Device.__init__(self,*args,**kwargs['dconfig'])
            device_config=self.getConfiguration()
            
            
            # setup publisher
            self._zmq_context = zmq.Context()
            self._pub_socket = self._zmq_context.socket(zmq.PUB)
            self._pub_socket.setsockopt(zmq.LINGER, 0)
            self._publishing_protocal=device_config.get('publishing_protocal',"tcp://127.0.0.1:5555")
            self._pub_socket.bind(self._publishing_protocal)
        except Exception, e:
            print2err("** Exception during EventPublisher.__init__: ",e)
            printExceptionDetailsToStdErr()
            
    def _handleEvent(self,e):
        """
        Publish the Event as long as it was generated locally"
        """
        if e[2]==0:
            #print2err("PUBLISHING: ",e[:8])
            e_id=e[DeviceEvent.EVENT_TYPE_ID_INDEX]
            
            # Format of received event data:
            #                        
            #                 data[0] = exp_id 
            #                 data[1] = sess_id, 
            #                 data[2] = device_id. For PubSubConnection device: 
            #                           0 == local exp process device, 
            #                           > 0 == Device id set in the /remote/ 
            #                                  PubSubConnection device config
            #                 data[3] = event_num, 
            #                 data[4] = event type id 
            #                 data[5] = device_time, 
            #                 data[6] = logged_time, 
            #                 data[7] = local ioHub time, 
            #                 data[8] = confidence_interval, 
            #                 data[9] = delay, 
            #                 data[10] = filter_id, # always 0, not used currently
    
            event_array=copy.deepcopy(e)
            event_array[0]=0
            event_array[1]=0
            event_array[2]=self.device_number
            event_array[3] = 0
            

            # send event to subscribers        
            # 
            self._pub_socket.send_multipart([EventConstants.getClass(e_id).__name__,self.pack(event_array)], 0)
 
    def _close(self):
        if self._pub_socket is not None:
            self._pub_socket.send_multipart([u'EXIT',''])
            self._pub_socket.close()
            self._pub_socket=None
            Device._close(self)

    def __del__(self):
       self._close()
       
class RemoteEventSubscriber(Device):
    """
    The RemoteEventSubscriber Device allows the ioHub Server it is running in
    to receive ioHub events from networked remote ioHub Server instances running on seperate 
    computers. The remote ioHub Server must be running an instance the
    EventPublisher device for RemoteEventSubscriber to receive events from that
    ioHub Server instance.
    
    When a RemoteEventSubscriber device is configured for an experiment, the
    ip address and port of the remote EventPublisher device is specified. A list
    of ioHub event types that the RemoteEventSubscriber wants to receive can also be specified.
    The RemoteEventSubscriber will then receive any events of the requested types, 
    which are also events that the remote EventPublisher is publishing, following
    the connection to the EventPublisher. ioHub events that occurred on the remote
    ioHub Server prior to the RemoteEventSubscriber connection being estabilshed 
    are not received by the subscriber.
    
    Events received by a RemoteEventSubscriber can be saved to the ioHub DataStore
    or provided to the psychoPy experiment runtime in the same way as any other device 
    events are. For example, if a RemoteEventSubscriber, labeled "evt_sub", has 
    subscribed to Keyboard events published by an EventPublisher device, those
    events can be received as follows::
    
        # Assuming the ioHubExperimentRuntime utility class is being used
        # and we are in the run() method of the class which defines the main 
        # experiment runtime script
        self.subscriber=self.devices.evt_sub
        
        remote_events_received=self.subscriber.getEvents()
        
        for event in remote_events_received:
            print "Received remote evt {evt_type}; with an event time of {evt_time},\\
            which has been adjusted to factor in a total event delay of {evt_delay}".format(
                evt_type=event.type,evt_time=event.time,evt_delay=event.delay)
            
    """
    _packer=msgpack.Packer()
    pack=_packer.pack
    _unpacker=msgpack.Unpacker(use_list=True)
    unpack=_unpacker.unpack      
    feed=_unpacker.feed

    _newDataTypes=[]    
    EVENT_CLASS_NAMES=[]    
    DEVICE_TYPE_ID=DeviceConstants.REMOTEEVENTSUBSCRIBER
    DEVICE_LABEL = 'REMOTEEVENTSUBSCRIBER'
    __slots__=[e[0] for e in _newDataTypes]+['_zmq_context','_sub_socket','_subscription_protocal','_subscription_filter','_time_sync_state','_time_sync_manager','_running']
    def __init__(self, *args,**kwargs):
        self._sub_socket=None
        self._time_sync_manager=None
        try:
            Device.__init__(self,*args,**kwargs['dconfig'])
            device_config=self.getConfiguration()
            self._subscription_protocal=device_config.get('subscription_protocal',None)
            if self._subscription_protocal:
                self._zmq_context = zmq.Context()
                self._sub_socket = self._zmq_context.socket(zmq.SUB)
            
                self._subscription_filter=device_config.get('monitor_event_types',[u''])
    
                # If sub channel is filtering by category / event type, then auto add
                # the EXIT category to the sub channels filter list of categories to include.
                #
                if len(self._subscription_filter)>0 and self._subscription_filter[0]!='':  
                    self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, u'EXIT')
            
                for sf in self._subscription_filter:
                    self._sub_socket.setsockopt_string(zmq.SUBSCRIBE, sf)
                self._sub_socket.connect(self._subscription_protocal)
    
                self._time_sync_manager=None
                if device_config.get('remote_iohub_address'):
                    from psychopy.iohub.net import TimeSyncState

                    self._time_sync_state=TimeSyncState()

                    from psychopy.iohub.net import ioHubTimeGreenSyncManager

                    self._time_sync_manager=ioHubTimeGreenSyncManager(device_config.get('remote_iohub_address'),self._time_sync_state)
                    self._time_sync_manager.start()   
                
                gevent.spawn(self._poll) # really like _run
        except Exception, e:
            print2err("** Exception during RemoteEventSubscriber.__init__: ",e)
            printExceptionDetailsToStdErr()
            
    def _handleEvent(self,e):
        """
        Handle the Event as long as it was generated remotely...."
        """        
        if e[2]>0:
            #print2err('SUB RX callback: ',e[0:8])
            Device._handleEvent(self,e)

    def _addEventListener(self,l,eventTypeIDs):
        from psychopy.iohub.server import ioServer
        if not isinstance(l,ioServer):
            Device._addEventListener(self,l,eventTypeIDs)        

    def _poll(self):
        while self._time_sync_manager is None:
            gevent.sleep(0.5)
        time_sync_manager=self._time_sync_manager
        time_sync_state=self._time_sync_state
        self._running=True
        while self._running is True and self._time_sync_manager:
            try:
                category,data=self._sub_socket.recv_multipart(0)
                logged_time=Computer.currentSec()
                if category == u'EXIT':
                    self._running=False
                    break
                self.feed(data)
                data=self.unpack()
                network_delay=0.0

                data[0]=0
                data[1]=0
                data[3]=Computer._getNextEventID() #set event id
                network_delay=0.0
                
                if time_sync_manager:
                    remote_logged_time=data[6]
                    data[6]=logged_time #update logged time
                    remote_hub_time=data[7]
                    data[7]=time_sync_state.remote2LocalTime(remote_hub_time)
                    data[8]=time_sync_state.getAccuracy()*2.0 
                    network_delay=time_sync_state.local2RemoteTime(logged_time)-remote_logged_time
                    data[9]+=network_delay

                self._nativeEventCallback(data)
                gevent.sleep(0)
            except zmq.ZMQError,z:
                break
            except Exception:
                printExceptionDetailsToStdErr()
            
        self._close()
            
    def _nativeEventCallback(self,native_event_data):
        if self.isReportingEvents():
            notifiedTime=Computer.currentSec()  
            self._addNativeEventToBuffer(native_event_data)
            self._last_callback_time=notifiedTime
        
    def _close(self):
        self._running=False    
        if self._sub_socket:
            self._sub_socket.close()
            self._sub_socket=None            
            Device._close(self)
        if self._time_sync_manager:
            self._time_sync_manager._close()
            self._time_sync_state=None
            self._time_sync_manager=None