# -*- coding: utf-8 -*-
"""
Testing the iohub.client.quickStartHubServer function.
"""

from psychopy.iohub import quickStartHubServer

     
def testWithNoKwargs():
    io=quickStartHubServer()
    
    keyboard=io.devices.keyboard
    
    print "Press any Key to Exit Example....."

    while not keyboard.getEvents():
        io.wait(0.25)
    
    print "A Keyboard Event was Detected; exiting Test."

    io.quit()

def testUsingPsychoPyMonitorConfig():
    io=quickStartHubServer(psychopy_monitor_name='testMonitor')
    
    display=io.devices.display
    
    print 'Display Psychopy Monitor Name: ', display.getPsychopyMonitorName()        
    print 'Display Default Eye Distance: ', display.getDefaultEyeDistance()        
    print 'Display Physical Dimensions: ', display.getPhysicalDimensions()        

    io.quit()


def testEnabledDataStore():
        psychopy_mon_name='testMonitor'
        exp_code='gap_endo_que'
        io=quickStartHubServer(psychopy_monitor_name=psychopy_mon_name, experiment_code=exp_code)
        
        display=io.devices.display
        
        print 'Display Psychopy Monitor Name: ', display.getPsychopyMonitorName()        
        print 'Display Default Eye Distance: ', display.getDefaultEyeDistance()        
        print 'Display Physical Dimensions: ', display.getPhysicalDimensions()        
    
        from pprint import pprint
        
        print 'Experiment Metadata: '
        pprint(io.getExperimentMetaData())
        print '\nSession Metadata: '
        pprint(io.getSessionMetaData())
        
        io.quit()
        

def testEnabledDataStoreAutoSessionCode():
        import time

        psychopy_mon_name='testMonitor'
        exp_code='gap_endo_que'
        sess_code='S_{0}'.format(long(time.mktime(time.localtime())))
        print 'Current Session Code will be: ', sess_code    
        
        io=quickStartHubServer(psychopy_monitor_name=psychopy_mon_name, experiment_code=exp_code, session_code=sess_code)
        
        display=io.devices.display
        
        print 'Display Psychopy Monitor Name: ', display.getPsychopyMonitorName()        
        print 'Display Default Eye Distance: ', display.getDefaultEyeDistance()        
        print 'Display Physical Dimensions: ', display.getPhysicalDimensions()        
    
        from pprint import pprint
        
        print 'Experiment Metadata: '
        pprint(io.getExperimentMetaData())
        print '\nSession Metadata: '
        pprint(io.getSessionMetaData())
        
        io.quit()


test_list=['testWithNoKwargs','testUsingPsychoPyMonitorConfig','testEnabledDataStore','testEnabledDataStoreAutoSessionCode']

if __name__ == '__main__':
    for test in test_list:
        print '\n------------------------------------\n'
        print 'Running %s Test:'%(test)

        for namespace in (locals(),globals()):    
            if test in namespace:
               result = namespace[test]()
               print 'Test Result: ', result
               break 
    
 


#myWin = FullScreenWindow(display)
