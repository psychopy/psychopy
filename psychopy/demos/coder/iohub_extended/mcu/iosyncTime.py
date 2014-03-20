# -*- coding: utf-8 -*-
"""
Script can be used to test the offset and drift correction used to convert
iohub times -> ioSync times and visa versa.
"""

repetitions=100

import numpy as np    
import time
from pprint import pprint

from psychopy import core
from psychopy.iohub import launchHubServer,Computer,OrderedDict
getTime=core.getTime

psychopy_mon_name='testMonitor'
exp_code='events'
sess_code='S_{0}'.format(long(time.mktime(time.localtime())))

iohub_config={
"psychopy_monitor_name":psychopy_mon_name,
"mcu.iosync.MCU":dict(serial_port='COM8',monitor_event_types=[]),#['DigitalInputEvent']),
"experiment_code":exp_code, 
"session_code":sess_code
}

results=np.zeros((repetitions,5),dtype=np.float64)
io=launchHubServer(**iohub_config)

#Computer.enableHighPriority()
#io.enableHighPriority()

display=io.devices.display
mcu=io.devices.mcu
kb=io.devices.keyboard
experiment=io.devices.experiment
    
mcu.enableEventReporting(True)

print 'Running Test. Please wait.'
print   
old_stuff=mcu.getRequestResponse()
io.clearEvents("all")  

labels=(# 'offset' ,
        # 'drift',
        # 'sync_accuracy' ,
         'tx_time',
         'iohub_time',
         'rx_time',
         'rx_time - tx_time' ,
         'iohub_time - tx_time' ,
         'rx_time - iohub_time' ,
        # 'last_rtt' ,
        # 'last_local_dt' ,    
        # 'last_remote_dt' ,            
        # 'mean_rtt' ,
        # 'mean_local_dt' ,   
        # 'mean_remote_dt' ,              
        # 'stdev_rtt' ,  
        # 'stdev_local_dt' , 
        # 'stdev_remote_dt'
         )    
print '\t'.join(labels)
print

for i in range(repetitions):      
    r=mcu.requestTime()
    stime=getTime()
    time.sleep(0.1)
    hitFound=False
    while getTime()-stime < 0.5 and hitFound is False:
        responses = mcu.getRequestResponse()
        for r in responses:
            if r['iohub_time']:
                vals=(#r['offset']*1000.0,
                    #r['drift'],
                    #(r['sync_accuracy'])*1000.0,
                    (r['tx_time'])*1000.0,
                    (r['iohub_time'])*1000.0,
                    (r['rx_time'])*1000.0,
                    (r['rx_time']-r['tx_time'])*1000.0,
                    (r['iohub_time']-r['tx_time'])*1000.0,
                    (r['rx_time']-r['iohub_time'])*1000.0,
                    #r['last_rtt']*1000.0,
                    #r['last_local_dt']*1000.0,    
                    #r['last_remote_dt']*1000.0,            
                    #r['mean_rtt']*1000.0,
                    #r['mean_local_dt']*1000.0,   
                    #r['mean_remote_dt']*1000.0,              
                    #r['stdev_rtt']*1000.0,  
                    #r['stdev_local_dt']*1000.0, 
                    #r['stdev_remote_dt']*1000.0
                    )
                
                valstr=['%.3f'%(v) for v in vals]
                print '\t'.join(valstr)            
#            print '>>>>'
#            print 'ioSync Response:'            
#            pprint(resp)
#            print '<<<<'
            hitFound=True
            break
        
#print '----'                 
#core.wait(0.1,0.0)
#srtime=getTime()*1000.0
#responses = mcu.getRequestResponse()
#ertime=getTime()*1000.0
#for resp in responses:
#    results[i,2] = srtime
#    results[i,3] = ertime
#    results[i,4] = resp['time']/1000.0      
#    i+=1
mcu.enableEventReporting(False)  

io.quit() 

#print results

import matplotlib
import matplotlib.pyplot as plt

#common_params = dict(bins=16, 
#                     ##range=(-5, 5), 
#                     normed=1,
#                     #color=['crimson', 'burlywood', 'chartreuse'],
#                     label=['requestTime()', 'getRequestResponse()', 'Total']                    
#                     )
#
#plt.title('ioSync Request - Response Call Durations')
#request_dur=(results[:,1]-results[:,0])
#response_dur=(results[:,3]-results[:,2])
#total_dur=(results[:,3]-results[:,0])
#plt.hist((request_dur,response_dur,total_dur), **common_params)
#plt.legend()
#plt.xlabel("ioHub ioSync Call Durations (msec)")
##plt.hist((results[:,3]-results[:,0]))#,normed=True)
#plt.show()
#
#plt.clf()
#
#plt.title('ioSync vs ioHub Dt (msec). Colorbar is ioHub Time')
#iosync_time_dt=results[1:,4]-results[:-1,4]
#iohub_time=(results[:,3]+results[:,2])/2
#iohub_time_dt=iohub_time[1:]-iohub_time[:-1]
##data=np.column_stack((iosync_time_dt,iohub_time_dt))
##data=[iosync_time_dt,iohub_time_dt]
##plt.plot(iosync_time_dt,'b.',iohub_time_dt,'g.')
#T = iohub_time[1:]
#plt.scatter(iosync_time_dt,iohub_time_dt, s=75, c=T, alpha=.5)
#plt.colorbar()
#plt.xlabel('ioSync Msec Time Dt')
#plt.ylabel('ioHub Msec Time Dt')
#plt.show()