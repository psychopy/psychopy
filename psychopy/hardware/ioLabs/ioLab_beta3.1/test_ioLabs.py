from ioLabs import *

import random
import unittest

def test_plugged_in():
    '''check box is plugged in'''
    try:
        usbbox=USBBox()
    except:
        assert False

def test_synonyms():
    '''make sure we have the correct port
    synonyms setup
    '''
    usbbox=USBBox()
    assert usbbox.port1 == usbbox.buttons
    assert usbbox.port2 == usbbox.leds
    assert usbbox.int0  == usbbox.voice_key
    assert usbbox.int1  == usbbox.optic_key


def test_attributes():
    usbbox=USBBox()
    assert hasattr(usbbox,'port0')
    assert hasattr(usbbox,'port1')
    assert hasattr(usbbox,'port2')
    assert hasattr(usbbox,'int0')
    assert hasattr(usbbox,'int1')
    assert hasattr(usbbox,'serial')


class TestUSBBox(unittest.TestCase):
    
    def setUp(self):
        self.usbbox=USBBox()
        # set sensible initial values
        self.usbbox.port0.direction=0
        self.usbbox.port0.logic=0
        self.usbbox.port0.state=0
        
        # enable all buttons
        self.usbbox.port1.enabled=0xff
        # set default debounce values
        self.usbbox.port1.debounce_down=20
        self.usbbox.port1.debounce_up=5
        
        self.usbbox.int0.debounce_down=20
        self.usbbox.int0.debounce_up=5
        
        self.usbbox.port2.direction=0
        self.usbbox.port2.logic=0
        self.usbbox.port2.state=0
        
        # run these to at least verify they
        # don't throw exceptions
        self.usbbox.enable_loopback()
        self.usbbox.disable_loopback()
        self.usbbox.purge_queue()
        
    
    def tearDown(self):
        del self.usbbox
    
    def test_reset_clock(self):
        rep=self.usbbox.reset_clock()
        assert rep.port1_bits == 0x00 # no keys pressed
        assert hasattr(rep,'port3_bits') # unsure what value should be so check it exists
        assert rep.rtc == 0
    
    def _check_port(self,port,field):
        assert hasattr(port,field)
        
        # only test sub-set of values to speed up testing a bit
        for i in random.sample(range(0,256),16):
            setattr(port,field,i)
            assert getattr(port,field) == i
    
    def test_port1_enabled(self):
        self._check_port(self.usbbox.port1,'enabled')
    
    def test_port1_debounce_down(self):
        self._check_port(self.usbbox.port1,'debounce_down')
    
    def test_port1_debounce_up(self):
        self._check_port(self.usbbox.port1,'debounce_up')
    
    def test_port1_state(self):
        # TODO find out whether we can set the key state somehow (loop-back?)
        assert hasattr(self.usbbox.port1,'state')
        assert self.usbbox.port1.state == 0x00 # no buttons being pressed
    
    def test_port0_state(self):
        self._check_port(self.usbbox.port0,'state')
    
    def test_port2_state(self):
        self._check_port(self.usbbox.port2,'state')
    
    def test_port0_logic(self):
        self._check_port(self.usbbox.port0,'logic')
    
    def test_port2_logic(self):
        self._check_port(self.usbbox.port2,'logic')
    
    def test_port0_direction(self):
        self._check_port(self.usbbox.port0,'direction')
    
    def test_port2_direction(self):
        self._check_port(self.usbbox.port2,'direction')
    
    def test_int0_debounce_down(self):
        self._check_port(self.usbbox.int0,'debounce_down')
    
    def test_int0_debounce_up(self):
        self._check_port(self.usbbox.int0,'debounce_up')
    
    def test_int0_primary_gain(self):
        self._check_port(self.usbbox.int0,'primary_gain')
    
    def test_int0_secondary_gain(self):
        self._check_port(self.usbbox.int0,'secondary_gain')
    
    def test_int0_min_duration(self):
        self._check_port(self.usbbox.int0,'min_duration')
    
    def test_int0_min_silence(self):
        self._check_port(self.usbbox.int0,'min_silence')

    def test_int0_trigger_level(self):
        self._check_port(self.usbbox.int0,'trigger_level')
            
    def test_int0_mic_pass_thru(self):
        # only has 0/1
        for i in [0,1]:
            self.usbbox.int0.mic_pass_thru=i
            assert self.usbbox.int0.mic_pass_thru == i
                
    def test_int1_debounce_down(self):
        self._check_port(self.usbbox.int1,'debounce_down')
    
    def test_int1_debounce_up(self):
        self._check_port(self.usbbox.int1,'debounce_up')
    
    
    def _check_port_and_state(self,port):
        for i in random.sample(range(0,256),16):
            port.state=i
            mask = random.randint(0,255)
            state = port.and_state(mask)
            assert state == (mask & i)
            assert state == port.state
    
    def test_port0_and_state(self):
        self._check_port_and_state(self.usbbox.port0)
    
    def test_port2_and_state(self):
        self._check_port_and_state(self.usbbox.port2)
    
    
    def _check_port_or_state(self,port):
        for i in random.sample(range(0,256),16):
            port.state=i
            mask = random.randint(0,255)
            state = port.or_state(mask)
            assert state == (mask | i)
            assert state == port.state
    
    def test_port0_or_state(self):
        self._check_port_or_state(self.usbbox.port0)
    
    def test_port2_or_state(self):
        self._check_port_or_state(self.usbbox.port2)
    
    
    def _check_port_xor_state(self,port):
        for i in random.sample(range(0,256),16):
            port.state=i
            mask = random.randint(0,255)
            state = port.xor_state(mask)
            assert state == (mask ^ i)
            assert state == port.state
    
    def test_port0_xor_state(self):
        self._check_port_xor_state(self.usbbox.port0)
    
    def test_port2_xor_state(self):
        self._check_port_xor_state(self.usbbox.port2)
    
    
    def _check_lines_defined(self,port):
        lines=port.lines
        assert lines[0]._mask == port.line0._mask
        assert lines[1]._mask == port.line1._mask
        assert lines[2]._mask == port.line2._mask
        assert lines[3]._mask == port.line3._mask
        assert lines[4]._mask == port.line4._mask
        assert lines[5]._mask == port.line5._mask
        assert lines[6]._mask == port.line6._mask
        assert lines[7]._mask == port.line7._mask
    
    def test_port0_lines_defined(self):
        self._check_lines_defined(self.usbbox.port0)
    
    def test_port1_lines_defined(self):
        self._check_lines_defined(self.usbbox.port1)
    
    def test_port2_lines_defined(self):
        self._check_lines_defined(self.usbbox.port2)
    
    
    def _check_port_line(self,port,field):
        '''check that setting individual line affects the
        same field on the port'''
        for i,line in enumerate(port.lines):
            setattr(port,field,0)
            setattr(line,field,1)
            assert getattr(line,field) == 1
            assert getattr(port,field) == (1 << i)
            setattr(line,field,0)
            assert getattr(line,field) == 0
            assert getattr(port,field) == 0
    
    def test_port0_line_state(self):
        self._check_port_line(self.usbbox.port0,'state')
    
    def test_port0_line_direction(self):
        self._check_port_line(self.usbbox.port0,'direction')
    
    def test_port0_line_logic(self):
        self._check_port_line(self.usbbox.port0,'logic')

    def test_port1_line_enabled(self):
        self._check_port_line(self.usbbox.port1,'enabled')
    
    def test_port1_line_state(self):
        # TODO can't set port1 state, so this is more checking we exercise the code
        for line in self.usbbox.port1.lines:
            assert line.state == 0
    
    def test_port2_line_state(self):
        self._check_port_line(self.usbbox.port2,'state')

    def test_port2_line_direction(self):
        self._check_port_line(self.usbbox.port2,'direction')

    def test_port2_line_logic(self):
        self._check_port_line(self.usbbox.port2,'logic')
    
    
    def _check_port_line_random(self,port,field):
        '''check that if we set the field on the port, we
        get matching field values on the lines'''
        value=random.randint(0,255)
        setattr(port,field,value)
        expected=(
            (getattr(port.line7,field) << 7)
        |   (getattr(port.line6,field) << 6)
        |   (getattr(port.line5,field) << 5)
        |   (getattr(port.line4,field) << 4)
        |   (getattr(port.line3,field) << 3)
        |   (getattr(port.line2,field) << 2)
        |   (getattr(port.line1,field) << 1)
        |   (getattr(port.line0,field))
        )
        assert expected == value
    
    def test_port0_line_state_random(self):
        self._check_port_line_random(self.usbbox.port0,'state')
    
    def test_port0_line_direction_random(self):
        self._check_port_line_random(self.usbbox.port0,'direction')
    
    def test_port0_line_logic_random(self):
        self._check_port_line_random(self.usbbox.port0,'logic')

    def test_port1_line_enabled_random(self):
        self._check_port_line_random(self.usbbox.port1,'enabled')
    
    def test_port2_line_state_random(self):
        self._check_port_line_random(self.usbbox.port2,'state')
    
    def test_port2_line_direction_random(self):
        self._check_port_line_random(self.usbbox.port2,'direction')
    
    def test_port2_line_logic_random(self):
        self._check_port_line_random(self.usbbox.port2,'logic')
    
    
    def _check_interrupt_enabled(self,interrupt):
        assert hasattr(interrupt,'enabled')
        interrupt.enabled=0
        assert interrupt.enabled == 0
        interrupt.enabled=1
        assert interrupt.enabled == 1
    
    def test_int0_enabled(self):
        self._check_interrupt_enabled(self.usbbox.int0)
    
    def test_int1_enabled(self):
        self._check_interrupt_enabled(self.usbbox.int1)
    
    
    def test_enabling(self):
        # check everything is enabled/disabled properly
        for i in range(0,16):
            port1_enabled=random.randint(0,255)
            self.usbbox.port1.enabled=port1_enabled
            
            int0_enabled=random.randint(0,1)
            self.usbbox.int0.enabled=int0_enabled
            int1_enabled=random.randint(0,1)
            self.usbbox.int1.enabled=int1_enabled
            
            # now send MSKGET to get MSKREP and check it's as we expect
            rep=self.usbbox.commands.send_wait_reply(COMMAND.MSKGET,REPORT.MSKREP)
            assert rep.port1_bits == port1_enabled
            
            port3_enabled=(int0_enabled<<2) | (int1_enabled<<3)
            assert rep.port3_bits == port3_enabled
    
    def test_setting_voice_key(self):
        '''check setting voice key properties does not affect
        each other when set individually
        '''
        self.usbbox.int0.min_duration=10
        self.usbbox.int0.min_silence=20
        self.usbbox.int0.trigger_level=100
        self.usbbox.int0.mic_pass_thru=1 # pass thru isn't sent from box
        
        assert self.usbbox.int0.min_duration == 10
        assert self.usbbox.int0.min_silence  == 20
        assert self.usbbox.int0.trigger_level== 100
    
    def test_wait_for_keyup(self):
        '''make sure it timesout ok'''
        rep=self.usbbox.wait_for_keyup()
        assert rep is None
    
    def test_wait_for_keydown(self):
        '''make sure it timesout ok'''
        rep=self.usbbox.wait_for_keydown()
        assert rep is None
    
    def test_write_serial(self):
        '''verify we can write to the serial port'''
        self.usbbox.serial.write('hello world')
    
    def test_read_serial(self):
        '''check we get back an empty string (as nothing else writing to serial port)'''
        bytes=self.usbbox.serial.read()
        assert bytes == ''
    
    def test_send_command(self):
        '''check we can manually send a command'''
        self.usbbox.send_command(COMMAND.RTCGET)
        rep=self.usbbox.commands.wait_for_report(REPORT.RTCREP)
        assert rep is not None
    
    def test_send_command2(self):
        '''check we can send a command with data'''
        import struct
        p0=random.randint(0,255)
        bytes=struct.pack('B',p0)
        self.usbbox.send_command(COMMAND.P0SET,bytes)
        rep=self.usbbox.commands.wait_for_report(REPORT.PXREP)
        assert rep is not None
        assert self.usbbox.port0.state == p0