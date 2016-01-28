# -*- coding: utf-8 -*-
"""
Created on Wed May 01 06:30:07 2013

@author: Sol
"""
import gevent
import json
import os,sys

import psychopy.iohub
from psychopy.iohub import Computer
Computer.is_iohub_process = True
from psychopy.iohub.server import ioServer

from psychopy.iohub import updateDict,printExceptionDetailsToStdErr, print2err, MonotonicClock, load, Loader

def run(rootScriptPathDir,configFilePath):
    psychopy.iohub.EXP_SCRIPT_DIRECTORY = rootScriptPathDir

    import tempfile
    tdir=tempfile.gettempdir()
    cdir,cfile=os.path.split(configFilePath)
    if tdir==cdir:
        tf=open(configFilePath)
        ioHubConfig=json.loads(tf.read())
        tf.close()
        os.remove(configFilePath)
    else:
        ioHubConfig=load(file(configFilePath,'r'), Loader=Loader)

    hub_defaults_config=load(file(os.path.join(psychopy.iohub.IO_HUB_DIRECTORY,'default_config.yaml'),'r'), Loader=Loader)
    updateDict(ioHubConfig,hub_defaults_config)
    try:
        s = ioServer(rootScriptPathDir, ioHubConfig)
    except Exception,e:
        printExceptionDetailsToStdErr()
        sys.stdout.flush()
        
        try:
            s.shutdown()
        except Exception:
            pass
        
        return -1
    
    try:
        s.log('Receiving datagrams on :9000')
        s.udpService.start()


        if Computer.system == 'win32':
            gevent.spawn(s.pumpMsgTasklet, s.config.get('windows_msgpump_interval', 0.00375))

        if hasattr(gevent,'run'):
            for m in s.deviceMonitors:
                m.start()
    
            gevent.spawn(s.processEventsTasklet, 0.01)

            sys.stdout.write("IOHUB_READY\n\r\n\r")

            #print2err("Computer.psychopy_process: ", Computer.psychopy_process)
            if Computer.psychopy_process:
                gevent.spawn(s.checkForPsychopyProcess, 0.5)

            sys.stdout.flush()
            
            gevent.run()
        else:
            glets=[]
            if Computer.system == 'win32':
                glets.append(gevent.spawn(s.pumpMsgTasklet, s.config.get('windows_msgpump_interval', 0.00375)))

            for m in s.deviceMonitors:
                m.start()
                glets.append(m)
            glets.append(gevent.spawn(s.processEventsTasklet,0.01))
    
            sys.stdout.write("IOHUB_READY\n\r\n\r")
            sys.stdout.flush()

            #print2err("Computer.psychopy_process: ", Computer.psychopy_process)
            if Computer.psychopy_process:
                 glets.append(gevent.spawn(s.checkForPsychopyProcess, 0.5))

            gevent.joinall(glets)
            

        s.log("Server END Time Offset: {0}".format(Computer.global_clock.getLastResetTime()),'DEBUG')

    except Exception as e:
        print2err("Error occurred during ioServer.start(): ",str(e))
        printExceptionDetailsToStdErr()
        print2err("------------------------------")

        sys.stdout.write("IOHUB_FAILED\n\r\n\r")
        sys.stdout.flush()
        
        try:
            s.shutdown()
        except Exception:
            pass
    
    return -1
    
if __name__ == '__main__':
    prog=sys.argv[0]
    if len(sys.argv)>=2:
        initial_offset=float(sys.argv[1])
    if len(sys.argv)>=3:
        rootScriptPathDir=sys.argv[2]
    if len(sys.argv)>=4:        
        configFileName=sys.argv[3]        
    if len(sys.argv)>=5:
        psychopy_pid = int(sys.argv[4])
        #ioHub.print2err("ioServer initial_offset: ",initial_offset)
    if len(sys.argv)<2:
        psychopy_pid=None
        configFileName=None
        rootScriptPathDir=None
        initial_offset=psychopy.iohub.getTime()

    try:
        import psutil
        if psychopy_pid:
            Computer.psychopy_process = psutil.Process(psychopy_pid)
    except Exception:
        pass

    Computer.global_clock=MonotonicClock(initial_offset)

    run(rootScriptPathDir=rootScriptPathDir, configFilePath=configFileName)
