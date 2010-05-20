'''
the module for interfacing with an ioLan button box.
USBBox is the main class that should be used from this module
'''

# turn on logging so we can see what's going on
import logging
#format='%(asctime)s %(levelname)s %(message)s'
#logging.basicConfig(level=logging.INFO,format=format)

import time
import struct
from Queue import Queue, Empty
import hid

IO_LABS_VENDOR_ID=0x19BC
BUTTON_BOX_PRODUCT_ID=0x0001

def is_usb_bbox(device):
    return device.vendor == IO_LABS_VENDOR_ID and device.product == BUTTON_BOX_PRODUCT_ID

class dict_struct:
    '''simple class that takes keyword arguments and uses them to create fields on itself'''
    def __init__(self,**kw):
        self.__dict__.update(kw)
    
    def __str__(self):
        attribs=[]
        for key,value in self.__dict__.items():
            attribs.append('%s=%s'%(key,value))
        return ','.join(attribs)
    
    def __repr__(self):
        attribs=[]
        for key,value in self.__dict__.items():
            attribs.append('%s=%r'%(key,value))
        return "dict_struct(%s)" % ','.join(attribs)

# commands in form id : ('name','pack format','field names')
# formats ignore identity byte (it's assumed to always be there)
# see "struct" module documentation for details of pack format strings
COMMAND_SUMMARY={
    # SYSTEM commands
    0x21 : ('PACSET', 'BBBBBBB', ('data1','data2','data3','data4','data5','data6','data7') ),
    0x59 : ('VERGET', 'xxxxxxx', () ),
    0x5A : ('NUMGET', 'xxxxxxx', () ),
    0x52 : ('RESRTC', 'xxxxxxx', () ),
    0x54 : ('RTCGET', 'xxxxxxx', () ),
    0x48 : ('HBSET',  'Hxxxxx',  ('rate',) ),
    0x51 : ('QPURGE', 'xxxxxxx', () ),
    0x53 : ('SEROUT', 'BBBBBBB', ('nb_data','data1','data2','data3','data4','data5','data6') ),
    0x43 : ('VCKSET', 'BBBBBxx', ('action','data1','data2','data3','data4') ),
    0x56 : ('VCKGET', 'xxxxxxx', () ),
    # PRIMARY input commands
    0x4D : ('MSKSET', 'xBBxxxx', ('port3_bits','port1_bits') ),
    0x3F : ('MSKGET', 'xxxxxxx', () ),
    0x47 : ('KEYGET', 'xxxxxxx', () ),
    0x4A : ('DEBSET', 'xBBBBBB', ('port1_down','port1_up','int0_down','int0_up','int1_down','int1_up') ),
    0x46 : ('DEBGET', 'xxxxxxx', () ),
    # GENERAL purpose I/O commands
    0x57 : ('DIRSET', 'BBBxxxx', ('port2_mode','port2_bits','port0_bits') ),
    0x44 : ('DIRGET', 'xxxxxxx', () ),
    0x4C : ('LOGSET', 'xBBxxxx', ('port2_bits','port0_bits') ),
    0x42 : ('LOGGET', 'xxxxxxx', () ),
    0x30 : ('P0SET',  'Bxxxxxx', ('bits',) ),
    0x41 : ('P0AND',  'Bxxxxxx', ('bits',) ),
    0x4F : ('P0_OR',  'Bxxxxxx', ('bits',) ),
    0x58 : ('P0XOR',  'Bxxxxxx', ('bits',) ),
    0x32 : ('P2SET',  'Bxxxxxx', ('bits',) ),
    0x61 : ('P2AND',  'Bxxxxxx', ('bits',) ),
    0x6F : ('P2_OR',  'Bxxxxxx', ('bits',) ),
    0x78 : ('P2XOR',  'Bxxxxxx', ('bits',) ),
    0x3D : ('PXSET',  'xBBxxxx', ('port2_bits', 'port0_bits' ) ),
    0x26 : ('PXAND',  'xBBxxxx', ('port2_bits', 'port0_bits' ) ),
    0x2B : ('PX_OR',  'xBBxxxx', ('port2_bits', 'port0_bits' ) ),
    0x5E : ('PXXOR',  'xBBxxxx', ('port2_bits', 'port0_bits' ) ),
    0x50 : ('PXGET',  'xxxxxxx', () ),
    0x4E : ('PXPGET', 'xxxxxxx', () ),
}

REPORT_SUMMARY = {
    0x59 : ('VERREP', 'BBBBBxx', ('error_code','rel_main','rev_main','rel_dtvk','rev_dtvk') ),
    0x5A : ('NUMREP', 'Bx5s',    ('error_code','serial_num') ),
    0x54 : ('RTCREP', 'BxxI',    ('queue_len', 'rtc') ),
    0x48 : ('HBREP',  'BHI',     ('queue_len', 'rate', 'rtc' ) ),
    0x53 : ('SERIN',  'BBBBBBB', ('status_code','data1','data2','data3','data4','data5','data6') ),
    0x56 : ('VCKREP', 'BBBBBBB', ('status_code','min_duration','min_silence','trigger_level','peak_level','primary_gain','secondary_gain') ),
    0x4A : ('DEBREP', 'xBBBBBB', ('port1_down','port1_up','int0_down','int0_up','int1_down','int1_up') ),
    0x44 : ('KEYDN',  'xxBI',    ('key_code','rtc') ),
    0x55 : ('KEYUP',  'xxBI',    ('key_code','rtc') ),
    0x4B : ('KEYREP', 'xBBI',    ('port3_bits','port1_bits','rtc') ),
    0x50 : ('PXREP',  'xBBI',    ('port2_bits','port0_bits','rtc') ),
    0x4E : ('PXPREP', 'xBBI',    ('port2_bits','port0_bits','rtc') ),
    0x4D : ('MSKREP', 'xBBI',    ('port3_bits','port1_bits','rtc') ),
    0x57 : ('DIRREP', 'BBBI',    ('port2_mode','port2_bits','port0_bits','rtc') ),
    0x4C : ('LOGREP', 'xBBI',    ('port2_bits','port0_bits','rtc') ),
    0x45 : ('ERROR',  'BBBBBBB', ('data1','data2','data3','data4','data5','data6','data7') )
}

class messages:
    '''class to handle message id lookup, and packing message objects into binary'''
    def __init__(self,message_summaries):
        self.message_summaries=message_summaries
        for message_id,message_summary in message_summaries.items():
            # add field for the ID
            message_name=message_summary[0]
            self.__dict__[message_name]=message_id
            # add function to pack args
            self.__dict__[message_name.lower()]=self._create_packing_function(message_id,message_summary)
    
    def ALL_IDS(self):
        return self.message_summaries.keys()
    
    def _create_packing_function(self,message_id,message_summary):
        # always big endian format
        format='>B'+message_summary[1]
        expected_args=message_summary[2]
        def packing_function(*args):
            if len(args) != len(expected_args):
                raise RuntimeError("wrong number of args for: %s(), expected: %s" % (message_summary[0].lower(),expected_args))
            return struct.pack(format,message_id,*args)
        return packing_function
    
    def name_from_id(self,message_id):
        '''
        get the 'name' from the id of the message
        '''
        return self.message_summaries[message_id][0]
    
    def parse(self,message_data):
        '''
        convert raw binary data into a structure
        '''
        id_byte=struct.unpack('B',message_data[0])[0]
        # see if we know how to parse this message
        if self.message_summaries.has_key(id_byte):
            summary=self.message_summaries[id_byte]
        
            format='>B'+summary[1]
            unpacked=struct.unpack(format,message_data)
            msg_fields={'name':summary[0]}
            field_names=('id',)+summary[2]
            if len(field_names) != len(unpacked):
                raise RuntimeError("message did not unpack correctly: %r"%message_data)
            for name,value in zip(field_names,unpacked):
                msg_fields[name]=value
            return dict_struct(**msg_fields)
        else:
            # otherwise just return it in a raw format
            logging.info("unknown message id: %d",id_byte)
            return dict_struct(id=id_byte,message_data=message_data)

#################################
# objects for accessing commands and reports
# provides access to IDs and function for parsing and
# packing message
COMMAND=messages(COMMAND_SUMMARY)
REPORT=messages(REPORT_SUMMARY)

class Commands:
    '''
    class to handle sending reports to device and parsing incoming reports.
    dynamically looks up/creates method for sending reports when none is
    found on the class.  this will let us override the default behavior
    to make things friendlier when appropriate.
    all received messages are queued up and require a call to 'process_received_reports'
    to trigger the user's callbacks, so as to avoid thread issues.
    '''
    def __init__(self,device):
        self.device=device
        self.callbacks={}
        self.default_callbacks=set()
        self.queue=Queue()
        self.device.set_interrupt_report_callback(self._report_received)
    
    def _report_received(self,device,report_data):
        logging.info('%r',report_data)
        msg=REPORT.parse(report_data)
        logging.info('received msg: %r',msg)
        self.queue.put(msg)
    
    def process_received_reports(self,block=False,timeout=10):
        '''
        process all reports that have been received and call the
        relevant callbacks.
        by default this method returns immediately if no reports
        are on the queue, but can be made to block and wait for
        a report if needeed
        '''
        while block or not self.queue.empty():            
            report=self.queue.get(block,timeout)
            self._process_report(report)
            # we always stop blocking after we've received
            # at least one report
            block=False 
    
    def _process_report(self,report):
        callbacks=self.callbacks.get(report.id,self.default_callbacks)
        for callback in callbacks:
            callback(report)
    
    def get_received_reports(self):
        '''
        return a list of received reports (removes them from the queue)
        '''
        reports=[]
        while not self.queue.empty():
            msg=self.queue.get()
            reports.append(msg)
        return reports
    
    def clear_received_reports(self):
        '''remove all received reports from the queue'''
        while not self.queue.empty():
            self.queue.get()
    
    def add_callback(self,report_id,report_callback):
        '''
        add a callback function that will be called when
        a report with the given id arrives. callback
        should take a single value that is the report
        that was received
        '''
        callbacks=self.callbacks.get(report_id,set())
        callbacks.add(report_callback)
        self.callbacks[report_id]=callbacks
    
    def remove_callback(self,report_id,report_callback):
        callbacks=self.callbacks.get(report_id,set())
        callbacks.discard(report_callback) # remove if present
    
    def add_default_callback(self,report_callback):
        self.default_callbacks.add(report_callback)
    
    def remove_default_callback(self,report_callback):
        self.default_callbacks.discard(report_callback)
    
    def wait_for_report(self,report_id):
        '''
        blocks until we receive a report with the given id
        from the box and then returns it (may trigger other callbacks)
        '''
        # register a callback for the report we want
        reports=[]
        def callback(report):
            reports.append(report)
        self.add_callback(report_id,callback)
        
        # process reports, until we get the one we want
        try:
            try:
                while len(reports) == 0:
                    self.process_received_reports(block=True,timeout=2)
            except Empty:
                return None
        finally:
            # then remove the callback, as we don't need it anymore
            self.remove_callback(report_id,callback)
        
        # return the report we received
        return reports[0]
    
    def send_wait_reply(self,command_id,report_id,*args):
        '''
        send a command with the given arguments and wait for the reply
        '''
        command_name=COMMAND.name_from_id(command_id).lower()
        getattr(self,command_name)(*args) # send the command
        return self.wait_for_report(report_id)
    
    def send_wait_field(self,command_id,report_id,field_name,*args):
        '''
        send a command (with the args), wait for the report and return the field on the
        report
        '''
        return getattr(self.send_wait_reply(command_id,report_id,*args),field_name)
    
    def __getattr__(self,name):
        '''return a function to send the named command to the device'''
        packing_function=getattr(COMMAND,name,None)
        if packing_function:
            return lambda *arg: self.device.set_report(packing_function(*arg))
        raise AttributeError("couldn't find: %s" % name)


class Line(object):
    '''base class for Lines (individual parts of ports)'''
    def __init__(self,port,mask):
        self._port=port
        self._mask=mask
    
    def _bit_state(self,bits):
        '''return 1/0 depending on whether relevent bit set'''
        if (bits & self._mask) != 0:
            return 1
        else:
            return 0;
    
    def _set_bit_state(self,bits,high):
        if high:
            return bits | self._mask
        else:
            return bits & (self._mask ^ 0xFF)


class Port0_2(object):
    '''
    class representing ports 0 and 2 (leds)
    '''
    def __init__(self,commands,port_num):
        self._commands=commands
        self._port_num=port_num
        self._port_bits='port%d_bits'%port_num
    
    
    # direction property
    def _get_direction(self):
        return self._commands.send_wait_field(COMMAND.DIRGET,REPORT.DIRREP,self._port_bits)
    
    def _set_direction(self,bits):
        # get original state
        rep=self._commands.send_wait_reply(COMMAND.DIRGET,REPORT.DIRREP)
        setattr(rep,self._port_bits,bits) # update bits for this port
        # send set command and wait for reply
        self._commands.send_wait_reply(COMMAND.DIRSET,REPORT.DIRREP,0,rep.port2_bits,rep.port0_bits)
    
    direction=property(_get_direction,_set_direction)
    '''get/set the direction of the port'''
    
    # logic property
    def _get_logic(self):
        return self._commands.send_wait_field(COMMAND.LOGGET,REPORT.LOGREP,self._port_bits)
        
    def _set_logic(self,bits):
        rep=self._commands.send_wait_reply(COMMAND.LOGGET,REPORT.LOGREP)
        setattr(rep,self._port_bits,bits)
        self._commands.send_wait_reply(COMMAND.LOGSET,REPORT.LOGREP,rep.port2_bits,rep.port0_bits)
    
    logic=property(_get_logic,_set_logic)
    '''get/set the logic on the port'''
    
    # state property
    def _get_state(self):
        return self._commands.send_wait_field(COMMAND.PXGET,REPORT.PXREP,self._port_bits)
    
    def _set_state(self,bits):
        port_set=getattr(self._commands,'p%dset'%self._port_num)
        port_set(bits) # either p0set or p2set
        # then wait for reply (to avoid messing things up)
        self._commands.wait_for_report(REPORT.PXREP)
    
    state=property(_get_state,_set_state)
    '''get/set the port state'''
    
    
    # logic methods (and/or/xor)
    def _logic_state(self,logic_bits,command_format):
        port_logic=getattr(self._commands,command_format%self._port_num)
        port_logic(logic_bits)
        return getattr(self._commands.wait_for_report(REPORT.PXREP),self._port_bits)
        
    def and_state(self,and_bits):
        '''logically 'and' the value on the port, returns the port state'''
        return self._logic_state(and_bits,'p%dand')
    
    def or_state(self,or_bits):
        '''logically 'or' the value on the port, returns the port state'''
        return self._logic_state(or_bits,'p%d_or')
    
    def xor_state(self,xor_bits):
        '''logically 'xor' the value on the port, returns the port state'''
        return self._logic_state(xor_bits,'p%dxor')
    
    def _get_line(self,line_no):
        '''
        return an object that let's the user modify/query values
        on a single line of the port (1-bit)
        '''
        #inner class for individual lines
        class PortLine(Line):            
            # state property
            def _get_state(self):
                return self._bit_state(self._port.state)
            
            def _set_state(self,high):
                if high:
                    self._port.or_state(self._mask)
                else:
                    self._port.and_state(self._mask ^ 0xFF) # invert mask
            
            state=property(_get_state,_set_state)
            
            # direction property
            def _get_direction(self):
                return self._bit_state(self._port.direction)
            
            def _set_direction(self,high):
                self._port.direction=self._set_bit_state(self._port.direction,high)
            
            direction=property(_get_direction,_set_direction)
            
            # logic property
            def _get_logic(self):
                return self._bit_state(self._port.logic)
            
            def _set_logic(self,high):
                self._port.logic=self._set_bit_state(self._port.logic,high)
            
            logic=property(_get_logic,_set_logic)
        
        mask=1<<line_no
        # return new PortLine object
        return PortLine(self,mask)
    
    # properties for each individual line
    line0=property(lambda self: self._get_line(0))
    line1=property(lambda self: self._get_line(1))
    line2=property(lambda self: self._get_line(2))
    line3=property(lambda self: self._get_line(3))
    line4=property(lambda self: self._get_line(4))
    line5=property(lambda self: self._get_line(5))
    line6=property(lambda self: self._get_line(6))
    line7=property(lambda self: self._get_line(7))
    
    # property for all 8 lines
    lines=property(lambda self: [self._get_line(i) for i in range(8)])
    '''
    list of individual lines.
    each line has properties for state, direction and logic
    that can be used to alter the individual bits/lines on the whole
    port
    '''



def _set_debounce(commands,port1_down=None,port1_up=None,int0_down=None,int0_up=None,int1_down=None,int1_up=None):
    '''helper for setting debounce of a single field'''
    rep=commands.send_wait_reply(COMMAND.DEBGET,REPORT.DEBREP)
    
    if port1_down is not None:
        rep.port1_down=port1_down
    if port1_up is not None:
        rep.port1_up=port1_up
    if int0_down is not None:
        rep.int0_down=int0_down
    if int0_up is not None:
        rep.int0_up=int0_up
    if int1_down is not None:
        rep.int1_down=int1_down
    if int1_up is not None:
        rep.int1_up=int1_up
    
    commands.send_wait_reply(
        COMMAND.DEBSET,
        REPORT.DEBREP,
        rep.port1_down,rep.port1_up,
        rep.int0_down,rep.int0_up,
        rep.int1_down,rep.int1_up)


class Buttons(object):
    '''class that represents the buttons on the USBBox'''
    def __init__(self,commands):
        self._commands=commands
    
    def _get_enabled(self):
         return self._commands.send_wait_field(COMMAND.MSKGET,REPORT.MSKREP,'port1_bits')
    
    def _set_enabled(self,enabled):
        # get previous value
        rep=self._commands.send_wait_reply(COMMAND.MSKGET,REPORT.MSKREP)
        # update port 1
        rep.port1_bits=enabled
        # set mask - keeping old port3 value
        self._commands.send_wait_reply(COMMAND.MSKSET,REPORT.MSKREP,rep.port3_bits,rep.port1_bits)
    
    enabled=property(_get_enabled,_set_enabled)
    '''get/set enable/disabled status of all buttons'''
    
    def _get_debounce_down(self):
        return self._commands.send_wait_field(COMMAND.DEBGET,REPORT.DEBREP,'port1_down')
    
    def _set_debounce_down(self,debounce):
        _set_debounce(self._commands,port1_down=debounce)
    
    debounce_down=property(_get_debounce_down,_set_debounce_down)
    
    def _get_debounce_up(self):
        return self._commands.send_wait_field(COMMAND.DEBGET,REPORT.DEBREP,'port1_up')
    
    def _set_debounce_up(self,debounce):
        _set_debounce(self._commands,port1_up=debounce)

    debounce_up=property(_get_debounce_up,_set_debounce_up)
    
    def _get_state(self):
        return self._commands.send_wait_field(COMMAND.KEYGET,REPORT.KEYREP,'port1_bits')
    
    state=property(_get_state)
    '''get the state of all buttons (key report port1_bits value)'''
    
    def _get_line(self,line_no):
        '''
        return an object that let's the user modify/query values
        on a single line of the port (1-bit)
        '''
        #inner class for individual lines
        class ButtonLine(Line):            
            # state property
            def _get_state(self):
                return self._bit_state(self._port.state)
            
            state=property(_get_state)
            '''state of the line'''
            
            # enabled property
            def _get_enabled(self):
                return self._bit_state(self._port.enabled)
            
            def _set_enabled(self,high):
                self._port.enabled=self._set_bit_state(self._port.enabled,high)
            
            enabled=property(_get_enabled,_set_enabled)
            '''get/set whether the line/button is enable or not'''
            
        mask=1<<line_no
        # return new ButtonLine object
        return ButtonLine(self,mask)
    
    # properties for each individual line
    line0=property(lambda self: self._get_line(0))
    '''individual line (one button)'''
    line1=property(lambda self: self._get_line(1))
    line2=property(lambda self: self._get_line(2))
    line3=property(lambda self: self._get_line(3))
    line4=property(lambda self: self._get_line(4))
    line5=property(lambda self: self._get_line(5))
    line6=property(lambda self: self._get_line(6))
    line7=property(lambda self: self._get_line(7))
    
    lines=property(lambda self: [self._get_line(i) for i in range(8)])
    '''property for all 8 lines.
    each line (button) has a state and enabled property
    so each button can be queried/modified separately
    '''


class Interrupt(object):
    '''either int0 or int1 on the USBBox'''
    def __init__(self,commands,mask,int_num):
        self._commands=commands
        self._mask=mask
        self._int_num=int_num # interrupt number
    
    def _get_enabled(self):
        bits=self._commands.send_wait_field(COMMAND.MSKGET,REPORT.MSKREP,'port3_bits')
        if bits & self._mask != 0: # if bit set
            return 1
        else:
            return 0
    
    def _set_enabled(self,enabled):
        # get previous value
        rep=self._commands.send_wait_reply(COMMAND.MSKGET,REPORT.MSKREP)
        # update port 3 value
        if enabled:
            rep.port3_bits=rep.port3_bits | self._mask
        else:
            rep.port3_bits=rep.port3_bits & (self._mask ^ 0xFF)
        self._commands.send_wait_reply(COMMAND.MSKSET,REPORT.MSKREP,rep.port3_bits,rep.port1_bits)
    
    enabled=property(_get_enabled,_set_enabled)
    '''enable/disable the interrupt'''
    
    def _get_debounce_down(self):
        return self._commands.send_wait_field(COMMAND.DEBGET,REPORT.DEBREP,'int%d_down'%self._int_num)
    
    def _set_debounce_down(self,debounce):
        # use keyword expansion to expand this
        args={}
        args['int%d_down'%self._int_num]=debounce
        _set_debounce(self._commands,**args)
    
    debounce_down=property(_get_debounce_down,_set_debounce_down)
    
    
    def _get_debounce_up(self):
        return self._commands.send_wait_field(COMMAND.DEBGET,REPORT.DEBREP,'int%d_up'%self._int_num)
    
    def _set_debounce_up(self,debounce):
         # use keyword expansion to expand this
        args={}
        args['int%d_up'%self._int_num]=debounce
        _set_debounce(self._commands,**args)

    debounce_up=property(_get_debounce_up,_set_debounce_up)


def _get_voice_key(commands,field):
    while True:
        rep=commands.send_wait_reply(COMMAND.VCKGET,REPORT.VCKREP)
        if rep.status_code in [0x58,0x28]:
            break # got reply back ok
        if rep.status_code == 0x48: # basic NAK error is ok
            # sleep a little bit to let the value finish getting written
            # then we'll try again
            time.sleep(0.005)
        else:
            raise RuntimeError("error getting voice key code: 0x%x"%rep.status_code)
    
    return getattr(rep,field)

def _set_voice_key(commands,min_duration=None,min_silence=None,trigger_level=None,mic_pass_thru=0):
    '''helper for setting voice_key setting of a single field'''
    rep=commands.send_wait_reply(COMMAND.VCKGET,REPORT.VCKREP)
    
    if min_duration is not None:
        rep.min_duration=min_duration
    if min_silence is not None:
        rep.min_silence=min_silence
    if trigger_level is not None:
        rep.trigger_level=trigger_level
    
    rep=commands.send_wait_reply(
        COMMAND.VCKSET,
        REPORT.VCKREP,
        0xB8,
        rep.min_duration,
        rep.min_silence,
        rep.trigger_level,
        mic_pass_thru)
    
    if not rep.status_code in [0x58,0x28]:
        raise RuntimeError("error setting voice key code: 0x%x"%rep.status_code)
    
    # artificial delay to let values be written
    time.sleep(0.005)

class VoiceKey(Interrupt):
    '''object representing the voice input on the USBBox'''
    def __init__(self,commands):
        Interrupt.__init__(self,commands,mask=(1<<2),int_num=0)
        self._mic_pass_thru=0 # can't get pass thru state from box, so have to remember it
    
    # primary gain property
    def _get_primary_gain(self):
        return self._commands.send_wait_field(COMMAND.VCKGET,REPORT.VCKREP,'primary_gain')
    
    def _set_primary_gain(self,gain):
        self._commands.send_wait_reply(COMMAND.VCKSET,REPORT.VCKREP,0xA9,gain,0,0,0)
    
    primary_gain=property(_get_primary_gain,_set_primary_gain)
    
    # secondary_gain property
    def _get_secondary_gain(self):
        return self._commands.send_wait_field(COMMAND.VCKGET,REPORT.VCKREP,'secondary_gain')
    
    def _set_secondary_gain(self,gain):
        self._commands.send_wait_reply(COMMAND.VCKSET,REPORT.VCKREP,0xAA,gain,0,0,0)
    
    secondary_gain=property(_get_secondary_gain,_set_secondary_gain)
    
    # min_duration property
    def _get_min_duration(self):
        return _get_voice_key(self._commands,'min_duration')
    
    def _set_min_duration(self,duration):
        _set_voice_key(self._commands,min_duration=duration,mic_pass_thru=self._mic_pass_thru)
    
    min_duration=property(_get_min_duration,_set_min_duration)
    
    # min_silence property
    def _get_min_silence(self):
        return _get_voice_key(self._commands,'min_silence')
    
    def _set_min_silence(self,duration):
        _set_voice_key(self._commands,min_silence=duration,mic_pass_thru=self._mic_pass_thru)
    
    min_silence=property(_get_min_silence,_set_min_silence)
    
    # trigger_level property
    def _get_trigger_level(self):
        return _get_voice_key(self._commands,'trigger_level')
    
    def _set_trigger_level(self,level):
        _set_voice_key(self._commands,trigger_level=level,mic_pass_thru=self._mic_pass_thru)
    
    trigger_level=property(_get_trigger_level,_set_trigger_level)
    '''get/set trigger level'''
    
    
    # mic_pass_thru property
    def _get_mic_pass_thru(self):
        return self._mic_pass_thru
    
    def _set_mic_pass_thru(self,mic_pass_thru):
        if mic_pass_thru:
            self._mic_pass_thru=1
        else:
            self._mic_pass_thru=0
        _set_voice_key(self._commands,mic_pass_thru=self._mic_pass_thru)
    
    mic_pass_thru=property(_get_mic_pass_thru,_set_mic_pass_thru)
    '''get/set mic pass through state'''


class Serial(object):
    '''serial port on the USBBox'''
    def __init__(self,commands):
        self._commands=commands
        # add object as callback to 
        # receive incoming packets
        self._commands.add_callback(
            REPORT.SERIN,
            self._serial_in
        )
        self._bytes_received=[]
    
    def _serial_in(self,report):
        num_bytes=report.status_code
        if num_bytes <= 6:
            # we've received bytes written to the serial port
            for i in range(0,num_bytes):
                # save data1-data6 as appropriate
                self._bytes_received.append(getattr(report,'data%d'%(i+1)))
        elif report.status_code in ['0xFF','0xFE','0xF7']:
            raise RuntimeError("error reading from serial port: 0x%x"%report.status_code)
    
    def write(self,bytes):
        '''write bytes to the serial port'''
        for i in range(0,len(bytes),6):
            b=list(bytes[i:i+6]) # no more than six bytes at a time
            # convert into ints
            b=[struct.unpack('B',byte)[0] for byte in b]
            num_b=len(b)
            while len(b) < 6:
                b.append(0) # add padding bytes
            
            # might be receiving bytes at same time, so should loop until we get something
            # that isn't receiving bytes (those will be dealt with in callback on _serial_in)
            while True:
                rep=self._commands.send_wait_reply(COMMAND.SEROUT,REPORT.SERIN,num_b,*b)
                if rep.status_code == 0xF0:
                    break # got confirmation we've transmitted ok
    
    def read(self):
        '''
        wait for input on the serial port. blocks for a while, but times
        out if nothing received and returns an empty string
        '''
        self._commands.wait_for_report(REPORT.SERIN)
        # return what we've received so far (which may be nothing)
        bytes = ''.join([struct.pack('B',byte) for byte in self._bytes_received])
        self._bytes_received[:]=[] # clear received bytes
        return bytes
        
            

class USBBox(object):
    '''the USBBox itself'''
    
    def __init__(self,do_reset=True):
        self._device=None
        for dev in hid.find_hid_devices():
            if is_usb_bbox(dev):
                logging.info("found USB button box")
                self._device=dev
                break
        
        if self._device is None:
            raise RuntimeError("could not find button box - check it's plugged in")
        
        self._device.open()
        
        self._commands=Commands(self._device)
        
        self.recording=False
        self.recording_callback=None
        self.report_ids=None
        
        self._port0=Port0_2(self.commands,0)
        self._port1=Buttons(self.commands)
        self._port2=Port0_2(self.commands,2)
        
        self._int0=VoiceKey(self.commands)
        self._int1=Interrupt(self.commands,(1<<3),int_num=1)
        
        self._serial=Serial(self.commands)
        
        if do_reset:
            self.reset_box()
    
    def __del__(self):
        if self.device is not None:
            self.device.close()
    
    device = property(lambda self: self._device)
    '''the HIDDevice (the physical box itself)'''
    
    commands = property(lambda self: self._commands)
    '''Commands object for low-level API'''

    port0 = property(lambda self: self._port0)
    '''Port0_2 object for "port 0" on the box'''
    
    port1 = property(lambda self: self._port1)
    '''Buttons object for "port 1" on the box'''
    
    port2 = property(lambda self: self._port2)
    '''Port0_2 object for "port 2" on the box'''

    int0 = property(lambda self: self._int0)
    '''VoiceKey object for "interrupt 0" on the box'''
    
    int1 = property(lambda self: self._int1)
    '''Interrupt object for "interrupt 1" on the box'''

    serial = property(lambda self: self._serial)
    '''Serial object for the serial port on the box'''
    
    # add synonyms
    leds=port2
    '''synonym for port2'''
    buttons=port1
    '''synonym for port1'''
    voice_key=int0
    '''synonym for int0'''
    optic_key=int1
    '''synonym for int1'''

    
    def send_command(self,command_id,bytes=''):
        '''send a command to the box (one command_id byte and 7 data bytes)'''
        self.device.set_report(struct.pack("B7s",command_id,bytes))
    
    def process_received_reports(self):
        '''process any received reports and call registered callbacks'''
        self.commands.process_received_reports()
    
    def clear_received_reports(self):
        self.commands.clear_received_reports()
    
    def start_recording(self,report_ids,out_file):
        '''
        whenever we read a report write it to the given
        file (if the id is in report_ids)
        '''
        if self._recording:
            raise RuntimeError("sorry already recording, please stop_recording() first")
        self._recording=True
        # save report to file
        self._recording_callback=lambda report: out_file.write("%s\n"%report)
        self._report_ids=set(report_ids)
        for report_id in self._report_ids:
            self.commands.add_callback(report_id,self._recording_callback)
    
    def stop_recording(self):
        '''removes the callbacks we had in place for recording'''
        if self._recording:
            # make sure we process any remaing reports
            self.process_received_reports()
            self._recording=False
            self._out_file=None
            for report_id in self._report_ids:
                self.commands.remove_callback(report_id,self._recording_callback)
            self._report_ids=None
    
    # serial_num property
    def _get_serial_num(self):
        return self.commands.send_wait_field(COMMAND.NUMGET,REPORT.NUMREP,'serial_num')
    serial_num=property(_get_serial_num)
    '''read the serial number of the box'''
    
    # PAC property
    def _set_PAC(self,value):
        # this will expand value into separate arguments
        # so we can pass a string for the PAC code, rather
        # than individual bytes
        self.commands.pacset(*value)
    PAC=property(fset=_set_PAC)
    ''' set the PAC code (write only) '''
    
    # version property (main board)
    def _get_version(self):
        rep=self.commands.send_wait_reply(COMMAND.VERGET,REPORT.VERREP)
        return (rep.rel_main,rep.rev_main)
    version=property(_get_version)
    '''get the main board version number'''
    
    # voice_version property
    def _get_voice_version(self):
        rep=self.commands.send_wait_reply(COMMAND.VERGET,REPORT.VERREP)
        return (rep.rel_dtvk,rep.rev_dtvk)
    voice_version=property(_get_voice_version)
    '''get the version number of the voice board'''
    
    # clock property
    def _get_clock(self):
        return self.commands.send_wait_field(COMMAND.RTCGET,REPORT.RTCREP,'rtc')
    clock=property(_get_clock)
    '''get the current clock value'''
    
    # heartbeat property (write only)
    def _set_heartbeat(self,value):
        self.commands.hbset(value)
    heartbeat=property(fset=_set_heartbeat)
    '''set the heartbeat rate (write only)'''
    
    def purge_queue(self):
        '''purge the event queue on the box'''
        self.commands.qpurge()
    
    def reset_clock(self):
        '''reset the clock on the box (returns a key report)'''
        return self.commands.send_wait_reply(COMMAND.RESRTC,REPORT.KEYREP)
    
    def enable_loopback(self):
        '''enable loopback (LEDs on/off with button presses)'''
        rep=self.commands.send_wait_reply(COMMAND.DIRGET,REPORT.DIRREP)
        self.commands.send_wait_reply(COMMAND.DIRSET,REPORT.DIRREP,1,rep.port2_bits,rep.port0_bits)
    
    def disable_loopback(self):
        rep=self.commands.send_wait_reply(COMMAND.DIRGET,REPORT.DIRREP)
        self.commands.send_wait_reply(COMMAND.DIRSET,REPORT.DIRREP,0,rep.port2_bits,rep.port0_bits)
    
    def wait_for_keydown(self):
        '''wait for a key to be pressed and returns the report'''
        return self.commands.wait_for_report(REPORT.KEYDN)

    def wait_for_keyup(self):
        '''wait for a key to be released and returns the report'''
        return self.commands.wait_for_report(REPORT.KEYUP)
    
    def reset_box(self):
        '''set box to some known values'''
        self.disable_loopback()
        
        self.heartbeat=30000 # 30 seconds
        
        self.buttons.debounce_up=5 # ms
        self.buttons.debounce_down=20 # ms
        self.int0.debounce_up=5 # ms
        self.int0.debounce_down=20 # ms
        self.int1.debounce_up=5 # ms
        self.int1.debounce_down=20 # ms
        
        self.port0.logic=0
        self.port0.state=0xff
        
        self.port2.logic=0
        self.port2.state=0xff
        
        self.buttons.enabled=0xff
        self.int0.enabled=1
        self.int1.enabled=1
        
        self.reset_clock()
        
        self.purge_queue()

if __name__ == '__main__':
    import sys
    
    usbbox=USBBox()
    
    print "USBBox connected"
    print "serial #:",usbbox.serial_num
    print "version:",usbbox.version
    print "voice version:", usbbox.voice_version
    
    # attached a callback for every report type
    def report_callback(msg):
        print "received:",msg
    for command_id in REPORT.ALL_IDS():
        usbbox.commands.add_callback(command_id,report_callback)
        
    from StringIO import StringIO
    outfile=StringIO()
    # record all incoming reports
    usbbox.start_recording(REPORT_SUMMARY.keys(),outfile)
    
    import re
    
    while True:
        time.sleep(0.5) # sleep a little to let any reports get received
        usbbox.process_received_reports()
        command=raw_input("command: ").strip()
        if command == 'exit':
            break
        elif command == '':
            continue
        elif command == 'help':
            # print list of available commands
            print "commands:"
            print " exit"
            print " help"
            for command_id in COMMAND_SUMMARY.keys():
                command_name=COMMAND_SUMMARY[command_id][0].lower()
                command_args=COMMAND_SUMMARY[command_id][2]
                command_args=['<%s>' % arg for arg in command_args]
                print " %s %s" % (command_name,' '.join(command_args))
        else:
            try:
                command_parts=command.split()
                command_name,command_args=command_parts[0],command_parts[1:]
                # check command is known
                known=False
                for command_id in COMMAND_SUMMARY.keys():
                    if COMMAND_SUMMARY[command_id][0].lower() == command_name:
                        known=True
                        break
                if not known:
                    print "error, unknown command: " + command_name
                else:
                    command_fn=getattr(usbbox.commands,command_name)
                    # turn all arguments into int's
                    command_args=[int(arg) for arg in command_args]
                    command_fn(*command_args)
            except:
                print "error running: " + command
    
    # make sure we process any remaining reports
    usbbox.process_received_reports()
    usbbox.stop_recording()
    
    print "recorded reports:"
    print outfile.getvalue()
