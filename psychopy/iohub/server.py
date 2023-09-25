# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import os
import sys
from operator import itemgetter
from collections import deque, OrderedDict

import msgpack
import gevent
from gevent.server import DatagramServer
from gevent import Greenlet

import numpy

try:
    import msgpack_numpy
    msgpack_numpy.patch()
except ImportError:
    pass

from . import IOHUB_DIRECTORY, EXP_SCRIPT_DIRECTORY, _DATA_STORE_AVAILABLE
from .errors import print2err, printExceptionDetailsToStdErr, ioHubError
from .net import MAX_PACKET_SIZE
from .util import convertCamelToSnake, win32MessagePump
from .util import yload, yLoader
from .constants import DeviceConstants, EventConstants
from .devices import DeviceEvent, import_device
from .devices import Computer
from .devices.deviceConfigValidation import validateDeviceConfiguration
getTime = Computer.getTime
syncClock = Computer.syncClock

# pylint: disable=protected-access
# pylint: disable=broad-except

def convertByteStrings(rdict):
    if rdict is None or len(rdict)==0:
        return rdict
    result = dict()
    for k, i in rdict.items(): 
        if isinstance(k, bytes):
            k = k.decode('utf-8')
        if isinstance(i, bytes):
            i = i.decode('utf-8')
        result[k] = i
    return result

class udpServer(DatagramServer):
    client_proc_init_req = None
    def __init__(self, ioHubServer, address):
        self.iohub = ioHubServer
        self.feed = None
        self._running = True
        self.iohub.log('ioHub Server configuring msgpack...')
        self.coder = msgpack
        self.packer = msgpack.Packer()
        self.pack = self.packer.pack
        self.unpacker = msgpack.Unpacker(use_list=True)
        self.unpack = self.unpacker.unpack
        self.feed = self.unpacker.feed
        self.multipacket_reads = 0
        DatagramServer.__init__(self, address)

    def handle(self, request, replyTo):
        if self._running is False:
            return False

        self.feed(request)

        if self.multipacket_reads > 0:
            # Multi packet request handling...
            self.multipacket_reads -= 1
            if self.multipacket_reads > 0:
                # If reading part of multi packet request, just return and wait for next part of request
                return False

        request = self.unpack()

        if request[0] == 'IOHUB_MULTIPACKET_REQUEST':
            # setup multi packet request read
            self.multipacket_reads = request[1]
            return False
        else:
            self.multipacket_reads = 0

        request_type = request.pop(0)
        if not isinstance(request_type, str):
            request_type = str(request_type, 'utf-8') # convert bytes to string for compatibility

        if request_type == 'SYNC_REQ':
            self.sendResponse(['SYNC_REPLY', getTime()], replyTo)
            return True
        elif request_type == 'PING':
            _ = request.pop(0) #client time
            msg_id = request.pop(0)
            payload = request.pop(0)
            ctime = getTime()
            self.sendResponse(['PING_BACK', ctime, msg_id,
                               payload, replyTo], replyTo)
            return True
        elif request_type == 'GET_EVENTS':
            return self.handleGetEvents(replyTo)
        elif request_type == 'EXP_DEVICE':
            return self.handleExperimentDeviceRequest(request, replyTo)
        elif request_type == 'CUSTOM_TASK':
            return self.handleCustomTaskRequest(request, replyTo)
        elif request_type == 'RPC':
            callable_name = request.pop(0)
            args = None
            kwargs = None
            if len(request) == 1:
                args = request.pop(0)
            if len(request) == 1:
                kwargs = request.pop(0)

            result = None
            try:
                if isinstance(callable_name, bytes):
                    callable_name = callable_name.decode('utf-8')
                result = getattr(self, callable_name)
            except Exception:
                print2err('RPC_ATTRIBUTE_ERROR')
                printExceptionDetailsToStdErr()
                self.sendResponse('RPC_ATTRIBUTE_ERROR', replyTo)
                return False

            if result and callable(result):
                funcPtr = result
                nargs = []
                if args:
                    for a in args:
                        if isinstance(a, bytes):
                            nargs.append(a.decode('utf-8'))
                        else:
                            nargs.append(a)
                    args = nargs
                    
                try:
                    if args is None and kwargs is None:
                        result = funcPtr()
                    elif args and kwargs:
                        result = funcPtr(*args, **convertByteStrings(kwargs))
                    elif args and not kwargs:
                        result = funcPtr(*args)
                    elif not args and kwargs:
                        result = funcPtr(**convertByteStrings(kwargs))
                    edata = ('RPC_RESULT', callable_name, result)
                    self.sendResponse(edata, replyTo)
                    return True
                except Exception:
                    print2err('RPC_RUNTIME_ERROR')
                    printExceptionDetailsToStdErr()
                    self.sendResponse('RPC_RUNTIME_ERROR', replyTo)
                    return False
            else:
                print2err('RPC_NOT_CALLABLE_ERROR')
                printExceptionDetailsToStdErr()
                self.sendResponse('RPC_NOT_CALLABLE_ERROR', replyTo)
                return False
        elif request_type == 'GET_IOHUB_STATUS':
            self.sendResponse((request_type, self.iohub.getStatus()), replyTo)
            return True
        elif request_type == 'STOP_IOHUB_SERVER':
            self.shutDown()
        else:
            print2err('RPC_NOT_CALLABLE_ERROR')
            printExceptionDetailsToStdErr()
            self.sendResponse('RPC_NOT_CALLABLE_ERROR', replyTo)
            return False

    def handleCustomTaskRequest(self, request, replyTo):
        custom_tasks = self.iohub.custom_tasks
        subtype = request.pop(0)
        tasklet_label = request.pop(0)
        print2err('REQUEST: {}'.format(request))
        if subtype == 'START':
            import importlib
            try:
                print2err('EXP_SCRIPT_DIRECTORY: ', EXP_SCRIPT_DIRECTORY)
                task_class_path = request.pop(0)
                if EXP_SCRIPT_DIRECTORY not in sys.path:
                    sys.path.append(EXP_SCRIPT_DIRECTORY)
                mod_name, class_name = task_class_path.rsplit('.', 1)
                mod = importlib.import_module(mod_name)
                task_cls = getattr(mod, class_name)
                if custom_tasks.get(tasklet_label):
                    custom_tasks.get(tasklet_label).stop()
                    del custom_tasks[tasklet_label]

                class_kwargs = {}
                if len(request):
                    class_kwargs = request.pop(0)
                custom_tasks[tasklet_label] = task_cls(**convertByteStrings(class_kwargs))
                custom_tasks[tasklet_label].start()
            except Exception:
                print2err(
                    'ioHub Start CustomTask Error: could not load '
                    'TASK START function: ', task_class_path)
                printExceptionDetailsToStdErr()
            print2err('Received CUSTOM TASK START: {}'.format(request))
        elif subtype == 'STOP':
            tcls = custom_tasks.get(tasklet_label)
            if tcls:
                tcls.stop()
                del custom_tasks[tasklet_label]
            print2err('Received CUSTOM TASK STOP: {}'.format(request))
        else:
            print2err(
                'Received UNKNOWN CUSTOM TASK SUBTYPE: {}'.format(subtype))

        edata = ('CUSTOM_TASK_REPLY', request)
        self.sendResponse(edata, replyTo)

    def handleGetEvents(self, replyTo):
        try:
            self.iohub.processDeviceEvents()
            currentEvents = list(self.iohub.eventBuffer)
            self.iohub.eventBuffer.clear()

            if len(currentEvents) > 0:
                currentEvents = sorted(
                    currentEvents, key=itemgetter(
                        DeviceEvent.EVENT_HUB_TIME_INDEX))
                self.sendResponse(
                    ('GET_EVENTS_RESULT', currentEvents), replyTo)
            else:
                self.sendResponse(('GET_EVENTS_RESULT', None), replyTo)
            return True
        except Exception:
            print2err('IOHUB_GET_EVENTS_ERROR')
            printExceptionDetailsToStdErr()
            self.sendResponse('IOHUB_GET_EVENTS_ERROR', replyTo)
            return False

    def handleExperimentDeviceRequest(self, request, replyTo):
        request_type = request.pop(0)
        if not isinstance(request_type, str):
            request_type = str(request_type, 'utf-8') # convert bytes to string for compatibility
        io_dev_dict = ioServer.deviceDict
        if request_type == 'EVENT_TX':
            exp_events = request.pop(0)
            exp_dev_cb = io_dev_dict['Experiment']._nativeEventCallback
            for eventAsTuple in exp_events:
                exp_dev_cb(eventAsTuple)
            self.sendResponse(('EVENT_TX_RESULT', len(exp_events)), replyTo)
            return True
        elif request_type == 'DEV_RPC':
            dclass = request.pop(0)
            if not isinstance(dclass, str):
                dclass = str(dclass, 'utf-8')
            dmethod = request.pop(0)
            if not isinstance(dmethod, str):
                dmethod = str(dmethod, 'utf-8')
            args = None
            kwargs = None
            if len(request) == 1:
                args = request[0]
            elif len(request) == 2:
                args = request[0]
                kwargs = request[1]
                if len(kwargs) == 0:
                    kwargs = None

            dev = None
            if dclass.find('.') > 0:
                for dname, dev in ioServer.deviceDict.items():
                    if dname.endswith(dclass):
                        dev = ioServer.deviceDict.get(dname, None)
                        break
            else:
                dev = ioServer.deviceDict.get(dclass, None)

            if dev is None:
                print2err('IOHUB_DEVICE_ERROR')
                printExceptionDetailsToStdErr()
                self.sendResponse('IOHUB_DEVICE_ERROR', replyTo)
                return False

            try:
                method = getattr(dev, dmethod)
            except Exception:
                print2err('IOHUB_DEVICE_METHOD_ERROR')
                printExceptionDetailsToStdErr()
                self.sendResponse('IOHUB_DEVICE_METHOD_ERROR', replyTo)
                return False

            result = []
            try:
                if args and kwargs:
                    result = method(*args, **convertByteStrings(kwargs))
                elif args:
                    result = method(*args)
                elif kwargs:
                    result = method(**convertByteStrings(kwargs))
                else:
                    result = method()
                #print2err("DEV_RPC_RESULT: ", result)
                self.sendResponse(('DEV_RPC_RESULT', result), replyTo)
                return True
            except Exception:
                print2err('RPC_DEVICE_RUNTIME_ERROR')
                printExceptionDetailsToStdErr()
                self.sendResponse('RPC_DEVICE_RUNTIME_ERROR', replyTo)
                return False

        elif request_type == 'GET_DEVICE_LIST':
            try:
                dev_list = []
                for d in self.iohub.devices:
                    dev_list.append((d.name, d.__class__.__name__))
                self.sendResponse(
                    ('GET_DEV_LIST_RESULT', len(dev_list), dev_list), replyTo)
                return True
            except Exception:
                print2err('RPC_DEVICE_RUNTIME_ERROR')
                printExceptionDetailsToStdErr()
                self.sendResponse('RPC_DEVICE_RUNTIME_ERROR', replyTo)
                return False

        elif request_type == 'GET_DEV_INTERFACE':
            dclass = request.pop(0)
            if not isinstance(dclass, str):
                dclass = str(dclass, 'utf-8')
            data = None
            if dclass in ['EyeTracker', 'DAQ']:
                for dname, hdevice in ioServer.deviceDict.items():
                    if dname.endswith(dclass):
                        data = hdevice._getRPCInterface()
                        break
            else:
                dev = ioServer.deviceDict.get(dclass, None)
                if dev:
                    data = dev._getRPCInterface()

            if data:
                self.sendResponse(('GET_DEV_INTERFACE', data), replyTo)
                return True
            else:
                print2err('GET_DEV_INTERFACE_ERROR: ',
                          '_getRPCInterface returned: ', data)
                self.sendResponse('GET_DEV_INTERFACE_ERROR', replyTo)
                return False

        elif request_type == 'ADD_DEVICE':
            cls_name = request.pop(0)
            dev_cfg = request.pop(1)
            data = self.iohub.createNewMonitoredDevice(cls_name, dev_cfg)

            if data:
                self.sendResponse(('ADD_DEVICE', data), replyTo)
                return True
            else:
                print2err('ADD_DEVICE_ERROR: createNewMonitoredDevice ',
                          'returned: ', data)
                self.sendResponse('ADD_DEVICE_ERROR', replyTo)
                return False
        else:
            print2err('DEVICE_RPC_TYPE_NOT_SUPPORTED_ERROR: ',
                      'Unknown Request Type: ', request_type)
            self.sendResponse('DEVICE_RPC_TYPE_NOT_SUPPORTED_ERROR', replyTo)
            return False

    def sendResponse(self, data, address):
        reply_data_sz = -1
        max_pkt_sz = int(MAX_PACKET_SIZE / 2 - 20)
        pkt_cnt = -1
        p = si = -1
        try:
            reply_data = self.pack(data)
            reply_data_sz = len(reply_data)
            if reply_data_sz >= max_pkt_sz:
                pkt_cnt = int(reply_data_sz // max_pkt_sz) + 1
                mpr_payload = ('IOHUB_MULTIPACKET_RESPONSE', pkt_cnt)
                self.sendResponse(mpr_payload, address)
                gevent.sleep(0.0001)
                for p in range(pkt_cnt - 1):
                    si = p*max_pkt_sz
                    self.socket.sendto(reply_data[si:si+max_pkt_sz], address)
                    # macOS hangs if we do not sleep gevent between each msg packet
                    gevent.sleep(0.0001)
                si = (p+1)*max_pkt_sz
                self.socket.sendto(reply_data[si:reply_data_sz], address)
            else:
                self.socket.sendto(reply_data, address)
        except Exception:
            print2err('=============================')
            print2err('Error trying to send data to experiment process:')
            print2err('max_pkt_sz: ', max_pkt_sz)
            print2err('reply_data_sz: ', reply_data_sz)
            print2err('pkt_cnt: ', pkt_cnt)
            print2err('packet index, byte index: ', p, si)
            printExceptionDetailsToStdErr()
            print2err('=============================')
            pktdata = self.pack('IOHUB_SERVER_RESPONSE_ERROR')
            self.socket.sendto(pktdata, address)

    def setExperimentInfo(self, exp_info_list):
        self.iohub.experimentInfoList = exp_info_list
        dsfile = self.iohub.dsfile
        if dsfile:
            exp_id = dsfile.createOrUpdateExperimentEntry(exp_info_list)
            self.iohub._experiment_id = exp_id
            self.iohub.log('Current Experiment ID: {}'.format(exp_id))
            return exp_id
        return False

    def checkIfSessionCodeExists(self, sessionCode):
        try:
            dsfile = self.iohub.dsfile
            if dsfile:
                return dsfile.checkIfSessionCodeExists(sessionCode)
            return False
        except Exception:
            printExceptionDetailsToStdErr()

    def registerWindowHandles(self, *win_hwhds):
        if self.iohub:
            for wh in win_hwhds:
                if wh['handle'] not in self.iohub._psychopy_windows.keys():
                    self.iohub._psychopy_windows[wh['handle']] = wh
                    wh['size'] = numpy.asarray(wh['size'])
                    wh['pos'] = numpy.asarray(wh['pos'])
                    if wh['monitor']:
                        from psychopy import monitors
                        monitor = wh['monitor']
                        monitor['monitor'] = monitors.Monitor('{}'.format(wh['handle']))
                        monitor['monitor'].setDistance(monitor['distance'])
                        monitor['monitor'].setWidth(monitor['width'])
                        monitor['monitor'].setSizePix(monitor['resolution'])
                    self.iohub.log('Registered Win: {}'.format(wh))

    def unregisterWindowHandles(self, *win_hwhds):
        if self.iohub:
            for wh in win_hwhds:
                if wh in self.iohub._psychopy_windows.keys():
                    del self.iohub._psychopy_windows[wh]
                    self.iohub.log('Removed Win: {}'.format(wh))

    def updateWindowPos(self, win_hwhd, pos):
        """
        Update stored psychopy window position.
        :param win_hwhd:
        :param pos:
        :return:
        """
        winfo = self.iohub._psychopy_windows.get(win_hwhd)
        if winfo:
            winfo['pos'] = pos
            self.iohub.log('Update Win: {}'.format(winfo))
        else:
            print2err('warning: win_hwhd {} not registered with iohub server.'.format(win_hwhd))
            self.iohub.log('updateWindowPos warning: win_hwhd {} not registered with iohub server.'.format(win_hwhd))

    def createExperimentSessionEntry(self, sessionInfoDict):
        sessionInfoDict = convertByteStrings(sessionInfoDict)
        self.iohub.sessionInfoDict = sessionInfoDict
        dsfile = self.iohub.dsfile
        if dsfile:
            sess_id = dsfile.createExperimentSessionEntry(sessionInfoDict)
            self.iohub._session_id = sess_id
            self.iohub.log('Current Session ID: %d' % (self.iohub._session_id))
            return sess_id
        return False

    def initConditionVariableTable(self, exp_id, sess_id, numpy_dtype):
        dsfile = self.iohub.dsfile
        if dsfile:
            output = []
            for a in numpy_dtype:
                if isinstance(a[1], str):
                    output.append(tuple(a))
                else:
                    temp = [a[0], []]
                    for i in a[1]:
                        temp[1].append(tuple(i))
                    output.append(tuple(temp))

            return dsfile.initConditionVariableTable(exp_id, sess_id, output)
        return False

    def extendConditionVariableTable(self, exp_id, sess_id, data):
        dsfile = self.iohub.dsfile
        if dsfile:
            return dsfile.extendConditionVariableTable(exp_id, sess_id, data)
        return False

    def clearEventBuffer(self, clear_device_level_buffers=False):
        """

        :param clear_device_level_buffers:
        :return:
        """
        self.iohub.clearEventBuffer()
        if clear_device_level_buffers is True:
            for device in self.iohub.devices:
                try:
                    device.clearEvents(call_proc_events=False)
                except Exception:
                    pass

    @staticmethod
    def getTime():
        """See Computer.getTime documentation, where current process will be
        the ioHub Server process."""
        return getTime()

    @staticmethod
    def syncClock(params):
        """
        Sync parameters between Computer.global_clock and a given dict.

        Parameters
        ----------
        params : dict
            Dict of attributes and values to apply to the computer's global clock. See
            `psychopy.clock.MonotonicClock` for what attributes to include.
        """
        return syncClock(params)

    @staticmethod
    def setPriority(level='normal', disable_gc=False):
        """See Computer.setPriority documentation, where current process will
        be the ioHub Server process."""
        return Computer.setPriority(level, disable_gc)

    @staticmethod
    def getPriority():
        """See Computer.getPriority documentation, where current process will
        be the ioHub Server process."""
        return Computer.getPriority()

    @staticmethod
    def getProcessAffinity():
        return Computer.getCurrentProcessAffinity()

    @staticmethod
    def setProcessAffinity(processorList):
        return Computer.setCurrentProcessAffinity(processorList)

    def flushIODataStoreFile(self):
        dsfile = self.iohub.dsfile
        if dsfile:
            dsfile.emrtFile.flush()
            return True
        return False

    def shutDown(self):
        try:
            self.setPriority('normal')
            self.iohub.shutdown()
            self._running = False
            self.stop()
        except Exception:
            print2err('Error in ioSever.shutdown():')
            printExceptionDetailsToStdErr()
            sys.exit(1)


class DeviceMonitor(Greenlet):
    def __init__(self, device, sleep_interval):
        Greenlet.__init__(self)
        self.device = device
        self.sleep_interval = sleep_interval
        self.running = False

    def _run(self):
        self.running = True
        ctime = Computer.getTime
        while self.running is True:
            stime = ctime()
            self.device._poll()
            i = self.sleep_interval - (ctime() - stime)
            gevent.sleep(max(0,i))

    def __del__(self):
        self.device = None


class ioServer():
    eventBuffer = None
    deviceDict = {}
    _logMessageBuffer = deque(maxlen=128)
    _psychopy_windows = {}
    status = 'OFFLINE'
    def __init__(self, rootScriptPathDir, config=None):
        self._session_id = None
        self._experiment_id = None

        self.log('Server Time Offset: {0}'.format(
            Computer.global_clock.getLastResetTime()))

        self._hookManager = None
        self.dsfile = None
        self.config = config
        self.devices = []
        self.deviceMonitors = []
        self.custom_tasks = OrderedDict()
        self.sessionInfoDict = None
        self.experimentInfoList = None
        self.filterLookupByInput = {}
        self.filterLookupByOutput = {}
        self.filterLookupByName = {}
        self._hookDevice = None
        self._all_dev_conf_errors = []
        ebuf_sz = config.get('global_event_buffer', 2048)
        ioServer.eventBuffer = deque(maxlen=ebuf_sz)

        self._running = True
        # start UDP service
        self.udpService = udpServer(self, ':%d' % config.get('udp_port', 9000))
        self._initDataStore(config, rootScriptPathDir)

        self._addDevices(config)

        self._addPubSubListeners()

    def _initDataStore(self, config, script_dir):
        try:
            # initial dataStore setup
            if 'data_store' in config and _DATA_STORE_AVAILABLE:
                ds_conf = config.get('data_store')
                def_ds_conf_path = os.path.join(IOHUB_DIRECTORY,
                                                'datastore',
                                                'default_datastore.yaml')
                _, def_ds_conf = yload(open(def_ds_conf_path, 'r'),
                                       Loader=yLoader).popitem()
                for dkey, dvalue in def_ds_conf.items():
                    if dkey not in ds_conf:
                        ds_conf[dkey] = dvalue

                if ds_conf.get('enable', True):
                    ds_dir = script_dir
                    hdf_name = ds_conf.get('filename', 'events') + '.hdf5'
                    hdf_parent_folder = ds_conf.get('parent_dir', '.')
                    if os.path.isabs(hdf_parent_folder):
                        ds_dir = hdf_parent_folder
                    else:
                        ds_dir = os.path.abspath(script_dir)
                        ds_dir = os.path.normpath(os.path.join(ds_dir, hdf_parent_folder))

                    if not os.path.exists(ds_dir):
                        os.makedirs(ds_dir)
                    self.createDataStoreFile(hdf_name, ds_dir, 'a', ds_conf)
        except Exception:
            print2err('Error during ioDataStore creation....')
            printExceptionDetailsToStdErr()

    def _addDevices(self, config):
        # built device list and config from initial yaml config settings
        try:
            for iodevice in config.get('monitor_devices', ()):
                for dev_cls_name, dev_conf in iodevice.items():
                    self.createNewMonitoredDevice(dev_cls_name, dev_conf)
        except Exception:
            print2err('Error during device creation ....')
            printExceptionDetailsToStdErr()

    def _addPubSubListeners(self):
        # Add PubSub device listeners to other event types
        try:
            for d in self.devices:
                if d.__class__.__name__ == 'EventPublisher':
                    monitored_event_ids = d._event_listeners.keys()
                    for eid in monitored_event_ids:
                        evt_cls = EventConstants.getClass(eid)
                        evt_dev_cls = evt_cls.PARENT_DEVICE
                        for ed in self.devices:
                            if ed.__class__ == evt_dev_cls:
                                ed._addEventListener(d, [eid, ])
                                break
        except Exception:
            print2err('Error PubSub Device listener association ....')
            printExceptionDetailsToStdErr()

    def processDeviceConfigDictionary(self, dev_mod_path, dev_cls_name, dev_conf, def_dev_conf):
        for dparam, dvalue in def_dev_conf.items():
            if dparam in dev_conf:
                if isinstance(dvalue, (dict, OrderedDict)):
                    self.processDeviceConfigDictionary(None, None, dev_conf.get(dparam), dvalue)
            elif dparam not in dev_conf:
                if isinstance(dvalue, (dict, OrderedDict)):
                    sub_param = dict()
                    self.processDeviceConfigDictionary(None, None, sub_param, dvalue)
                    dev_conf[dparam] = sub_param
                else:
                    dev_conf[dparam] = dvalue

        # Start device config verification.
        if dev_mod_path and dev_cls_name:
            dev_conf_errors = validateDeviceConfiguration(dev_mod_path,
                                                          dev_cls_name,
                                                          dev_conf)

            for err_type, err_list in dev_conf_errors.items():
                if len(err_list) > 0:
                    device_errors = self._all_dev_conf_errors.get(dev_mod_path,
                                                                  {})
                    device_errors[err_type] = err_list
                    self._all_dev_conf_errors[dev_mod_path] = device_errors

    def pumpMsgTasklet(self, sleep_interval):
        while self._running:
            stime = Computer.getTime()
            try:
                win32MessagePump()
            except KeyboardInterrupt:
                self._running = False
                break
            dur = sleep_interval - (Computer.getTime() - stime)
            gevent.sleep(max(0.0, dur))

    def createNewMonitoredDevice(self, dev_cls_name, dev_conf):
        self._all_dev_conf_errors = dict()
        try:
            dinstance = None
            dconf = None
            devt_ids = None
            devt_classes = None
            dev_data = self.addDeviceToMonitor(dev_cls_name, dev_conf)
            if dev_data:
                dinstance, dconf, devt_ids, devt_classes = dev_data
                DeviceConstants.addClassMapping(dinstance.__class__)
                EventConstants.addClassMappings(devt_ids, devt_classes)
            else:
                print2err('## Device was not started by the ioHub Server: ',
                          dev_cls_name)
                raise ioHubError('Device config validation failed')

        except Exception:
            print2err('Error during device creation ....')
            printExceptionDetailsToStdErr()
            raise ioHubError('Error during device creation ....')

        # Update DataStore Structure if required.
        if _DATA_STORE_AVAILABLE:
            try:
                if self.dsfile is not None:
                    self.dsfile.updateDataStoreStructure(dinstance,
                                                         devt_classes)
            except Exception:
                print2err('Error updating data store for device addition:',
                          dinstance, devt_ids)
                printExceptionDetailsToStdErr()
        self.log('Adding ioServer and DataStore event listeners......')

        # add event listeners for saving events
        if _DATA_STORE_AVAILABLE and self.dsfile is not None:
            dcls_name = dinstance.__class__.__name__
            if dconf['save_events']:
                dinstance._addEventListener(self.dsfile, devt_ids)
                lstr = 'Added Device DS Listener: {}, {}'.format(dcls_name,
                                                                 devt_ids)
                self.log(lstr)
            else:
                self.log('DS Disabled for Device: %s'%(dcls_name))
        else:
            self.log('DataStore Not Enabled. No events will be saved.')

        # Add Device Monitor for Keyboard or Mouse device type
        deviceDict = ioServer.deviceDict
        iohub = self
        hookManager = self._hookManager
        if dev_cls_name in ('Mouse', 'Keyboard'):
            if Computer.platform == 'win32':
                try:
                    import pyHook
                except ImportError:
                    import pyWinhook as pyHook
                if hookManager is None:
                    iohub.log('Creating pyHook HookManager....')
                    hookManager = self._hookManager = pyHook.HookManager()
                    hookManager.keyboard_hook = False
                if dev_cls_name == 'Mouse':
                    if hookManager.mouse_hook is False:
                        dmouse = deviceDict['Mouse']
                        hookManager.MouseAll = dmouse._nativeEventCallback
                        hookManager.HookMouse()
                elif dev_cls_name == 'Keyboard':
                    if hookManager.keyboard_hook is False:
                        dkeyboard = deviceDict['Keyboard']
                        hookManager.KeyAll = dkeyboard._nativeEventCallback
                        hookManager.HookKeyboard()

            elif Computer.platform.startswith('linux'):
                from .devices import pyXHook
                if hookManager is None:
                    log_evt = self.config.get('log_raw_kb_mouse_events', False)
                    self._hookManager = pyXHook.HookManager(log_evt)
                    hookManager = self._hookManager
                    hookManager._mouseHooked = False
                    hookManager._keyboardHooked = False
                if dev_cls_name == 'Keyboard':
                    if hookManager._keyboardHooked is False:
                        hookManager.HookKeyboard()
                        kbcb_func = deviceDict['Keyboard']._nativeEventCallback
                        hookManager.KeyDown = kbcb_func
                        hookManager.KeyUp = kbcb_func
                        hookManager._keyboardHooked = True
                elif dev_cls_name == 'Mouse':
                    if hookManager._mouseHooked is False:
                        hookManager.HookMouse()
                        mcb_func = deviceDict['Mouse']._nativeEventCallback
                        hookManager.MouseAllButtonsDown = mcb_func
                        hookManager.MouseAllButtonsUp = mcb_func
                        hookManager.MouseAllMotion = mcb_func
                        hookManager._mouseHooked = True
                if hookManager._running is False:
                    hookManager.start()

            else:  # OSX
                if self._hookDevice is None:
                    self._hookDevice = []
                if dev_cls_name not in self._hookDevice:
                    msgpump_interval = self.config.get('msgpump_interval', 0.001)
                    if dev_cls_name == 'Mouse':
                        dmouse = deviceDict['Mouse']
                        self.deviceMonitors.append(DeviceMonitor(dmouse, msgpump_interval))
                        dmouse._CGEventTapEnable(dmouse._tap, True)
                        self._hookDevice.append('Mouse')
                    if dev_cls_name == 'Keyboard':
                        dkeyboard = deviceDict['Keyboard']
                        kbHookMonitor = DeviceMonitor(dkeyboard, 0.001)
                        self.deviceMonitors.append(kbHookMonitor)
                        dkeyboard._CGEventTapEnable(dkeyboard._tap, True)
                        self._hookDevice.append('Keyboard')

            return [dev_cls_name, dconf['name'], dinstance._getRPCInterface()]

    def addDeviceToMonitor(self, dev_cls_name, dev_conf):
        dev_cls_name = str(dev_cls_name)
        self.log('Handling Device: %s' % (dev_cls_name,))

        DeviceClass = None
        cls_name_start = dev_cls_name.rfind('.')
        iohub_submod = 'psychopy.iohub.'
        iohub_submod_len = len(iohub_submod)
        dev_mod_pth = iohub_submod + 'devices.'
        if cls_name_start > 0:
            dev_mod_pth += dev_cls_name[:cls_name_start].lower()
            dev_cls_name = dev_cls_name[cls_name_start + 1:]
        else:
            dev_mod_pth += dev_cls_name.lower()

        dev_file_pth = dev_mod_pth[iohub_submod_len:].replace('.', os.path.sep)

        dev_conf_pth = os.path.join(IOHUB_DIRECTORY, dev_file_pth,
                                    'default_%s.yaml' % (dev_cls_name.lower()))

        self.log('Loading Device Defaults file: %s' % (dev_cls_name,))

        _dconf = yload(open(dev_conf_pth, 'r'), Loader=yLoader)
        _, def_dev_conf = _dconf.popitem()

        self.processDeviceConfigDictionary(dev_mod_pth, dev_cls_name, dev_conf,
                                           def_dev_conf)

        if dev_mod_pth in self._all_dev_conf_errors:
            # Complete device config verification.
            print2err('ERROR: DEVICE CONFIG ERRORS FOUND! ',
                      'IOHUB NOT LOADING DEVICE: ', dev_mod_pth)
            dev_conf_errors = self._all_dev_conf_errors[dev_mod_pth]
            for err_type, errors in dev_conf_errors.items():
                print2err('%s count %d:' % (err_type, len(errors)))
                for error in errors:
                    print2err('\t{0}'.format(error))
                print2err('\n')
            return None

        DeviceClass, dev_cls_name, evt_classes = import_device(dev_mod_pth,
                                                               dev_cls_name)
        deviceDict = ioServer.deviceDict

        if dev_conf.get('enable', True):
            self.log('Searching Device Path: %s' % (dev_cls_name,))
            self.log('Creating Device: %s' % (dev_cls_name,))
            # print2err("Creating Device: %s"%(device_class_name,))

            if DeviceClass._iohub_server is None:
                DeviceClass._iohub_server = self

            if dev_cls_name != 'Display':
                if DeviceClass._display_device is None:
                    DeviceClass._display_device = deviceDict['Display']

            dev_instance = DeviceClass(dconfig=dev_conf)
            self.devices.append(dev_instance)
            deviceDict[dev_cls_name] = dev_instance
            self.log('Device Instance Created: %s' % (dev_cls_name,))

            if 'device_timer' in dev_conf:
                interval = dev_conf['device_timer'].get('interval', 0.001)
                dPoller = DeviceMonitor(dev_instance, interval)
                self.deviceMonitors.append(dPoller)
                ltxt = '%s timer period: %.3f' % (dev_cls_name, interval)
                self.log(ltxt)

            monitor_evt_ids = []
            monitor_evt_list = dev_conf.get('monitor_event_types', [])
            if isinstance(monitor_evt_list, (list, tuple)):
                for evt_name in monitor_evt_list:
                    evt_cls_name = convertCamelToSnake(evt_name[:-5], False)
                    event_id = getattr(EventConstants, evt_cls_name)
                    monitor_evt_ids.append(event_id)
            self.log('{0} Monitoring Events: {1}'.format(dev_cls_name,
                                                         monitor_evt_ids))

            # add event listeners for streaming events
            if dev_conf.get('stream_events') is True:
                self.log('%s: Streaming Events are Enabled.' % dev_cls_name)
                # add listener for global event queue
                dev_instance._addEventListener(self, monitor_evt_ids)
                self.log('ioServer Event Listener: {}'.format(monitor_evt_ids))

                # add listener for device event queue
                dev_instance._addEventListener(dev_instance, monitor_evt_ids)
                self.log('{} Event Listener: {}'.format(dev_cls_name,
                                                        monitor_evt_ids))

            return dev_instance, dev_conf, monitor_evt_ids, evt_classes

    def log(self, text, level=None):
        try:
            log_time = getTime()
            exp = self.deviceDict.get('Experiment', None)
            if exp and self._session_id and self._experiment_id:
                while len(self._logMessageBuffer):
                    lm = self._logMessageBuffer.popleft()
                    exp.log(*lm)
                exp.log(text, level, log_time)
            else:
                self._logMessageBuffer.append((text, level, log_time))
        except Exception:
            printExceptionDetailsToStdErr()

    def createDataStoreFile(self, fname, fpath, fmode, iohub_settings):
        if _DATA_STORE_AVAILABLE:
            from .datastore import DataStoreFile
            self.closeDataStoreFile()
            self.dsfile = DataStoreFile(fname, fpath, fmode, iohub_settings)

    def closeDataStoreFile(self):
        if self.dsfile:
            pytablesfile = self.dsfile
            self.dsfile = None
            pytablesfile.flush()
            pytablesfile.close()

    def processEventsTasklet(self, sleep_interval):
        while self._running:
            stime = Computer.getTime()
            self.processDeviceEvents()
            dur = sleep_interval - (Computer.getTime() - stime)
            gevent.sleep(max(0, dur))

    def processDeviceEvents(self):
        for device in self.devices:
            evt = []
            try:
                events = device._getNativeEventBuffer()
                while events:
                    evt = device._getIOHubEventObject(events.popleft())
                    if evt:
                        etype = evt[DeviceEvent.EVENT_TYPE_ID_INDEX]
                        for l in device._getEventListeners(etype):
                            l._handleEvent(evt)

                filtered_events = []
                for efilter in device._filters.values():
                    filtered_events.extend(efilter._removeOutputEvents())
                for evt in filtered_events:
                    etype = evt[DeviceEvent.EVENT_TYPE_ID_INDEX]
                    for l in device._getEventListeners(etype):
                        l._handleEvent(evt)

            except Exception:
                print2err('Error in processDeviceEvents: ', device,
                          ' : ', len(events))
                if evt:
                    etype = evt[DeviceEvent.EVENT_TYPE_ID_INDEX]
                    ename = EventConstants.getName(etype)
                    print2err('Event type ID: ', etype, ' : ', ename)
                printExceptionDetailsToStdErr()
                print2err('--------------------------------------')

    def _handleEvent(self, event):
        self.eventBuffer.append(event)

    def clearEventBuffer(self, call_proc_events=True):
        if call_proc_events is True:
            self.processDeviceEvents()
        l = len(self.eventBuffer)
        self.eventBuffer.clear()
        return l

    def checkForPsychopyProcess(self, sleep_interval):
        while self._running:
            if Computer.psychopy_process:
                if Computer.psychopy_process.is_running() is False:
                    Computer.psychopy_process = None
                    self.shutdown()
                    break
                else:
                    gevent.sleep(sleep_interval)

    @classmethod
    def getStatus(cls):
        return cls.status

    @classmethod
    def setStatus(cls, s):
        cls.status = s
        return s

    def shutdown(self):
        try:
            self._running = False

            if Computer.platform.startswith('linux'):
                if self._hookManager:
                    self._hookManager.cancel()

            elif Computer.platform == 'win32':
                del self._hookManager
                # if self._hookManager:
                #    self._hookManager.UnhookMouse()
                #    self._hookManager.UnhookKeyboard()

            while self.deviceMonitors:
                self.deviceMonitors.pop(0).running = False

            if self.eventBuffer:
                self.clearEventBuffer()

            self.closeDataStoreFile()

            while self.devices:
                self.devices.pop(0)._close()
        except Exception:
            print2err('Error in ioSever.shutdown():')
            printExceptionDetailsToStdErr()

    def __del__(self):
        self.shutdown()

# pylint: enable=protected-access
# pylint: enable=broad-except
