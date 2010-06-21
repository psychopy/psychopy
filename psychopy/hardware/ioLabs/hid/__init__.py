'''
pure python module for discovering HID devices attached to a computer
and interacting with those devices.
'''

import logging

import os

import logging
from threading import Thread 

__all__ = ['find_hid_devices','HIDDevice']

class HIDDevice:
    '''
    absract class representing a HID device on the host computer
    '''
    def __init__(self,vendor,product):
        self.vendor=vendor
        self.product=product
        self._callback=None
        self._running=False
        self._thread=None
    
    def __del__(self):
        '''
        closes the device
        '''
        self.close()
        
    def close(self):
        '''close the device and stop the callback thread'''
        self._running=False
        if self._thread:
            self._thread.join(1)
        self._thread=None
    
    def is_open(self):
        raise RuntimeError("not implemented")
    
    def open(self):
        '''
        open this HID device for use (must be called before setting callbacks
        or setting reports)
        '''
        raise RuntimeError("not implemented")
    
    def set_report(self,report_data,report_id=0):
        '''
        "set" a report - send the data to the device (which must have been opened previously)
        '''
        if not self.is_open():
            raise RuntimeError("device not open")
        
        logging.info('set_report(%r)',report_data)
    
    
    def set_interrupt_report_callback(self,callback,report_buffer_size=8):
        '''
        register a callback for events from the device
        callback should be of form:
        
        def mycallback(device,report_data):
            pass
        
        '''
        if not self.is_open():
            raise RuntimeError("device not open")
        
        self._callback=callback
        if not self._running:
            self._running=True
            
            class CallbackLoop(Thread):
                def __init__(self,device,report_buffer_size):
                    Thread.__init__(self)
                    self.device=device
                    self.report_buffer_size=report_buffer_size
                
                def run(self):
                    self.device._run_interrupt_callback_loop(self.report_buffer_size)
            
            self._thread=CallbackLoop(self,report_buffer_size)
            self._thread.setDaemon(True)
            self._thread.start()
    
    def _run_interrupt_callback_loop(self,report_buffer_size):
        raise RuntimeError("not implemented")
    
    def __str__(self):
        return "(vendor=0x%04x,product=0x%04x)" % (self.vendor,self.product)

module_names=['hid.win32','hid.osx']

find_hid_devices=None

for name in module_names:
    # try loading modules until we find one that works
    try:
        hid=__import__(name,globals(),locals(),['find_hid_devices'])
        logging.info("loading HID code from: %s" % name)
        find_hid_devices=hid.find_hid_devices
        break
    except:
        pass

if find_hid_devices is None:
    raise RuntimeError("could not find a module for this operating system")
