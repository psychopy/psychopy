# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/devices/touch/hw/elo/elo_serial.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com>
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

from .... import Computer
from ..... import print2err
getTime=Computer.getTime


# Elo Serial Packet Definitions
class SmartSetPacket(object):
    LEAD_IN_BYTE='U'
    PACKET_TYPE_CHAR=''
    def __init__(self,time,packet_bytes):
        self.time=time
        if isinstance(packet_bytes,bytearray): 
            self._packet_bytes=packet_bytes
        else:
            self._packet_bytes=bytearray(packet_bytes)
            
    def calculateCheckSum(self):
        chksum=0xAA
        for b in self._packet_bytes[:-1]:
           chksum+=b 
        chksum=chksum%256   
        return chksum   

class QueryPacket(SmartSetPacket):        
    def __init__(self,b2=0,b3=0,b4=0,b5=0,b6=0,b7=0,b8=0):                 
        SmartSetPacket.__init__(self,getTime(),bytearray([self.LEAD_IN_BYTE,self.PACKET_TYPE_CHAR,b2,b3,b4,b5,b6,b7,b8,0])) 
        chksum=self.calculateCheckSum()
        self._packet_bytes[-1]=chksum
        
    def __str__(self):
        return '%s : %s'%(self.__class__.__name__,str(self._packet_bytes))
        
class CommandPacket(QueryPacket):        
    def __init__(self,b2=0,b3=0,b4=0,b5=0,b6=0,b7=0,b8=0):
        QueryPacket.__init__(self,b2,b3,b4,b5,b6,b7,b8)    

class ResponsePacket(SmartSetPacket):       
    def __init__(self,time,_packet_bytes):
        SmartSetPacket.__init__(self,time,_packet_bytes)   
        self._valid_response=True
        if len(_packet_bytes) != 10:
            self.valid_respons=False
            print2err('Warning: ResponsePacket _packet_bytes must be 10 bytes in length: %s'%str(self._packet_bytes))           
        if _packet_bytes[1] != ord(self.PACKET_TYPE_CHAR):
            self.valid_respons=False
            print2err('Warning: ResponsePacket PACKET_TYPE_CHAR must equal %s: %s'%(self.PACKET_TYPE_CHAR,str(self._packet_bytes)))
        if self.validPacket() is False:
            self.valid_respons=False
            print2err("ERROR: checksum %s %d (%d != %d)\n"%(str([b for b in self._packet_bytes]),len(self._packet_bytes),self.calculateCheckSum(),self._packet_bytes[-1]))

    def validPacket(self):
        if self.calculateCheckSum() == self._packet_bytes[-1]:
            return True
        return False

    def asdict(self):
        rd=dict()
        for k,v in self.__dict__.iteritems():
            if k[0]!='_':
                rd[k]=v
        return rd
        
QUERY_PACKET_TYPES=dict()
COMMAND_PACKET_TYPES=dict()
RESPONSE_PACKET_TYPES=dict()

###############################################################################

#
# Acknowledge Packets
#

# Query Packet
class QueryAcknowledge(QueryPacket):
    PACKET_TYPE_CHAR='a'
    def __init__(self):
        QueryPacket.__init__(self)
QUERY_PACKET_TYPES[QueryAcknowledge.PACKET_TYPE_CHAR]=QueryAcknowledge

# Command Packet
# Acknowledge can not be set.

# Response Packet
class ResponseAcknowledge(ResponsePacket):
    PACKET_TYPE_CHAR='A'
    warning_types={
                    '0' :'No warning',
                    '1' :'Divide by zero',
                    '2' :'Bad input packet',
                    '3' :'Bad input checksum',
                    '4' :'Input packet overrun',
                    '5' :'Illegal command',
                    '6' :'Calibration command cancelled',
                    '7' :'Reserved (contact Elo)',
                    '8' :'Bad serial setup combination',
                    '9' :'NVRAM not valid - initializing',
                    ':' :'3ah Reserved',
                    ';' :'3bh Reserved',
                    '<' :'3ch Reserved',
                    '=' :'3dh Reserved',
                    '>' :'3eh Reserved',
                    '?' :'3fh Reserved',
                    '@' :'40h Reserved',
                    'A' :'No set available for this command',
                    'B' :'Unsupported in the firmware version',
                    'C' :'Illegal subcommand',
                    'D' :'Operand out of range',
                    'E' :'Invalid type',
                    'F' :'Fatal error condition exists',
                    'G' :'No query available for this command',
                    'H' :'Invalid Interrupt number',
                    'I' :'NVRAM failure',
                    'J' :'Invalid address number',
                    'K' :'Power-on self-test failed',
                    'L' :'Operation Failed',
                    'M' :'Measurement Warning',
                    'N' :'Measurement Error',
                    }
                    
    def __init__(self,rx_time,packet_bytes):
        ResponsePacket.__init__(self,rx_time,packet_bytes)
        self.error1=chr(packet_bytes[2])
        self.error2=chr(packet_bytes[3])
        self.error3=chr(packet_bytes[4])
        self.error4=chr(packet_bytes[5])
        
        no_error=True
        if self.error1!='0':
            print 'WARNING: Acknowledge Error1:',self.error1,self.warning_types.get(self.error1,'UNKNOWN ACQ ERROR CODE')
            no_error=False
        if self.error2!='0':
            print 'WARNING: Acknowledge Error2:',self.error2,self.warning_types.get(self.error2,'UNKNOWN ACQ ERROR CODE')
            no_error=False
        if self.error3!='0':
            print 'WARNING: Acknowledge Error3:',self.error3,self.warning_types.get(self.error3,'UNKNOWN ACQ ERROR CODE')
            no_error=False
        if self.error4!='0':
            print 'WARNING: Acknowledge Error4:',self.error4,self.warning_types.get(self.error4,'UNKNOWN ACQ ERROR CODE')
            no_error=False       
        if  no_error:
            pass#print 'AckResponse OK'           
RESPONSE_PACKET_TYPES[ResponseAcknowledge.PACKET_TYPE_CHAR]=ResponseAcknowledge

###############################################################################

#
# Report Packets
#

# Query Packet
class QueryReport(QueryPacket):
    PACKET_TYPE_CHAR='b'
    def __init__(self):
        QueryPacket.__init__(self)
QUERY_PACKET_TYPES[QueryReport.PACKET_TYPE_CHAR]=QueryReport

# Command Packet
class CommandReport(CommandPacket):
    """
    The Untouch byte specifies the number (0 - 15) of 10ms time increments to delay
    before reporting an untouch condition. Increasing this value allows the controller
    to filter out accidental untouches due to skips while sliding the finger. The factory
    default value is 0.
    
    The RepDelay byte specifies a delay (0-255) in 10ms time increments between the
    transmission of touch packets. This is used to slow the output rate of the controller
    without changing other filtering or interface characteristics such as the baud rate.
    The factory default value is 2.    
    """
    PACKET_TYPE_CHAR='B'
    def __init__(self,untouch_delay,touch_pkt_delay):
        CommandPacket.__init__(self,chr(untouch_delay),chr(touch_pkt_delay))
        self.untouch_delay=self._packet_bytes[2]*10
        self.touch_pkt_delay=self._packet_bytes[3]*10
COMMAND_PACKET_TYPES[CommandReport.PACKET_TYPE_CHAR]=CommandReport 

# Response Packet
class ResponseReport(ResponsePacket):
    """
    The Untouch byte specifies the number (0 15) of 10ms time increments to delay
    before reporting an untouch condition. Increasing this value allows the controller
    to filter out accidental untouches due to skips while sliding the finger. The factory
    default value is 0.
    
    The RepDelay byte specifies a delay (0-255) in 10ms time increments between the
    transmission of touch packets. This is used to slow the output rate of the controller
    without changing other filtering or interface characteristics such as the baud rate.
    The factory default value is 2.    
    """
    PACKET_TYPE_CHAR='B'
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,time,packet_bytes)
        self.untouch_delay=self._packet_bytes[2]*10
        self.touch_pkt_delay=self._packet_bytes[3]*10
RESPONSE_PACKET_TYPES[ResponseReport.PACKET_TYPE_CHAR]=ResponseReport 

###############################################################################

#
# Calibration Packets
#

# Query Packet
class QueryCalibration(QueryPacket):
    """
    QueryCalibration Bytes
    
    0       c 
    1       axis (x,y, or z) 
    2-7     0
    
    axis specifies the coordinate axis by using lower-case ASCII characters 
    'x','y', or 'z'.     
    """
    PACKET_TYPE_CHAR='c'
    def __init__(self,axis=0,swap_flag=False):
        if axis and swap_flag is True:
            print2err('Warning: QueryCalibration axis and swap_flag args can not be used at the same time.')
        if axis:
            QueryPacket.__init__(self,axis.lower())
            self.axis=axis
        elif swap_flag is True:
            QueryPacket.__init__(self,'S')
            
QUERY_PACKET_TYPES[QueryCalibration.PACKET_TYPE_CHAR]=QueryCalibration

# Command Packet
class CommandCalibration(CommandPacket):
    """
    Calibration can be performed by a host-driven calibration program or a controller
    driven calibration sequence. 
        
    # Setting the Calibration Points Acquired by a Host-Driven Calibration Program
    
    Calibration is typically accomplished by a host-driven calibration program which
    determines the raw touchscreen coordinates at the extremes of the display image.
    These coordinates are then communicated to the controller, which converts them
    into an **internal Offset**, **Numerator**, and **Denominator** format.
    
    ## Setting the Calibration Parameters By Range
    
    A host-driven calibration sequence must first disable the Calibration and 
    Scaling Modes, acquire the low and high calibration points, transmit them 
    to the controller with the CX and CY commands, then restore the modes. 
    
    Host-driven calibration sequences are more flexible in that calibration points
    can be extrapolated to the edges, multiple samples acquired and averaged, etc.

    CommandCalibration Bytes (when setting by range)
    
    0       C 
    1       AXIS (X,Y, or Z) 
    2-3     LowPoint 
    4-5     HighPoint
    6       0
    7       0
    
    AXIS specifies the coordinate axis to calibrate by using upper-case ASCII
    characters 'X','Y', or 'Z'. LowPoint and HighPoint are unsigned words (two bytes each) 
    specifying an axis range. For example, if two calibration points are specified 
    as (XLow,YLow) and (XHigh,YHigh), LowPoint = XLow and HighPoint = XHigh 
    for the X-axis. If a HighPoint value is greater than a LowPoint value, 
    hardware axis inversion is performed.
    
    ## Setting the Calibration Parameters as Offset, Numerator, and Denominator
    
    This command is used to restore calibration parameters previously queried from
    the controller.
    
    CommandCalibration Bytes (when setting by Offset, Numerator, and Denominator)
    
    0       C 
    1       axis (x,y, or z) 
    2-3     Offset 
    4-5     Numerator
    6-7     Denominator
    
    axis specifies the coordinate axis to calibrate by using lower-case ASCII
    characters 'x','y', or 'z'. Offset, Numerator, and Denominator are the values
    returned from a previous calibration query or return.    

    # Z-Axis Calibration

    Z-axis calibration is typically not required as no Z data is available with
    resistive touchscreens. The controller defaults to 0-255, but always returns
    the HighPoint value.

    # Setting or Querying the Swap Axes Flag

    Swapped axes can be detected by a three-point host-driven calibration 
    sequence.

    This can correct inverted cabling or touchscreens rotated 90°. 
    If the coordinates of the third corner change in what should be the constant
    axis, then the axes are swapped. The controller can then be informed to swap
    the axes through the Swap Axes Flag. See EXAMPLE2.C, page 60.

    Enable is a byte value where the least significant bit is 1 to swap axes
    or 0 for normal operation.

    Calibration and Axis Swapping are disabled by factory default.    
    """
    PACKET_TYPE_CHAR='C'
    def __init__(self,axis=0,low_point=0,high_point=0,
                 offset=0,numerator=0,denominator=0,
                 enable_swap=False):
        if axis and enable_swap is True:
            print2err('Warning: CommandCalibration axis and enable_swap args can not be used at the same time.')
        if axis:
            if low_point is not None and high_point is not None:
                low_point_chr1=int(low_point) & 0b11111111 # get first byte of lowpoint 2-bytes and convert to chr
                low_point_chr2=int(low_point) >> 8 # get second byte of lowpoint 2-bytes and convert to chr
                high_point_chr1=int(high_point) & 0b11111111 # get first byte of highpoint 2-bytes and convert to chr
                high_point_chr2=int(high_point) >> 8 # get second byte of highpoint 2-bytes and convert to chr
                CommandPacket.__init__(self,axis.upper(),low_point_chr1,low_point_chr2,high_point_chr1,high_point_chr2)
            elif offset is not None and numerator is not None and denominator is not None:
                offset_chr1=int(offset) & 0b11111111 # get first byte of offset 2-bytes and convert to chr
                offset_chr2=int(offset) >> 8 # get second byte of offset 2-bytes and convert to chr
                numerator_chr1=int(numerator) & 0b11111111 # get first byte of numerator 2-bytes and convert to chr
                numerator_chr2=int(numerator) >> 8 # get second byte of numerator 2-bytes and convert to chr
                denominator_chr1=int(denominator) & 0b11111111 # get first byte of denominator 2-bytes and convert to chr
                denominator_chr2=int(denominator) >> 8 # get second byte of denominator 2-bytes and convert to chr
                CommandPacket.__init__(self,axis.lower(),offset_chr1,offset_chr2,numerator_chr1,numerator_chr2,denominator_chr1,denominator_chr2)
            else:
                print2err("Warning: Calibration must be set using low_point and high_point, OR offset, numerator, and denominator.")
        else:
            CommandPacket.__init__(self,'S',enable_swap)
COMMAND_PACKET_TYPES[CommandCalibration.PACKET_TYPE_CHAR]=CommandCalibration 


##------------------------
# Response Packet
class ResponseCalibration(ResponsePacket):
    """
    Calibration parameters are returned in the controller's internal Offset, 
    Numerator, and Denominator format. These values can be saved and later restored
    directly in this format.
    
    Note there is no way to directly query the LowPoint and HighPoint values. These
    values can be calculated by the following formulas:
    
        LowPoint = Offset
        HighPoint = LowPoint + Denominator
        CommandCalibration Bytes (when setting by Offset, Numerator, and Denominator)
    
    ResponseCalibration Bytes
    
    0       C 
    1       axis (x,y, or z) 
    2-3     Offset 
    4-5     Numerator
    6-7     Denominator
    """
    PACKET_TYPE_CHAR='C'
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,time,packet_bytes)
        self.axis=chr(self._packet_bytes[2])        
        self.offset=int(self._packet_bytes[4]<<8+self._packet_bytes[3])
        self.numerator=int(self._packet_bytes[6]<<8+self._packet_bytes[5])
        self.denominator=int(self._packet_bytes[8]<<8+self._packet_bytes[7])  
RESPONSE_PACKET_TYPES[ResponseCalibration.PACKET_TYPE_CHAR]=ResponseCalibration

###############################################################################

#
# Diagnostics Packets
#
 
# Query Packet
class QueryDiagnostics(QueryPacket):
    """
    The results of the previous diagnostics can be queried at any time. Since the
    controller executes its on-board diagnostics at power-on, the results can be 
    queried without running them again. 
    """
    PACKET_TYPE_CHAR='d'
    def __init__(self):
        QueryPacket.__init__(self)
QUERY_PACKET_TYPES[QueryDiagnostics.PACKET_TYPE_CHAR]=QueryDiagnostics

# Command Packet
class CommandDiagnostics(CommandPacket):
    """
    The DMask byte has the following bit positions:

    Bit         Test            Description

    0           ID Test         Checks to see that the firmware and hardware
                                are compatible.

    1           CPU Test        Exercises the CPU to verify that the instruction
                                set and registers are working.

    2           ROM Test        Verifies the checksum for the ROM.

    3           RAM Test        Performs an extensive read/write RAM test.
                                Checks for and tests optional external RAM.
                                Testing may take up to 45 seconds depending
                                on the memory configuration of the controller.

    4           NVRAM Test      Verifies the checksum of the nonvolatile RAM.

    5           Drive Test      Verifies the touchscreen drive hardware. With
                                1.2 or later firmware, a failure may indicate the
                                touchscreen is not connected.

    6           CHOP Test       If a controller expansion board is installed via
                                the controller's CHOP connector, this test allows
                                the expansion board to perform its diagnostics.

    7           Reserved

    When the set Diagnostic command is sent to the controller, the DMask bitmap
    specifies the individual tests to run. A 1 bit will run the corresponding 
    test while a 0 bit will skip the test.    
    """
    PACKET_TYPE_CHAR='D'
    def __init__(self,id_test=False,cpu_test=False,rom_test=False,ram_test=False,nvram_test=False,drive_test=False,chop_test=False):
        self.id_test=id_test*1
        self.cpu_test=cpu_test*2
        self.rom_test=rom_test*4
        self.ram_test=ram_test*8
        self.nvram_test=nvram_test*16
        self.drive_test=drive_test*32
        self.chop_test=chop_test*64
        self.reserved=0
        
        diag_mask=self.id_test+self.cpu_test+self.rom_test+self.ram_test+self.nvram_test+self.drive_test+self.chop_test
        
        CommandPacket.__init__(self,chr(diag_mask))

COMMAND_PACKET_TYPES[CommandDiagnostics.PACKET_TYPE_CHAR]=CommandDiagnostics 


# Response Packet
class ResponseDiagnostics(ResponsePacket):
    """
    The DMask byte has the following bit positions:

    Bit         Test            Description

    0           ID Test         Checks to see that the firmware and hardware
                                are compatible.

    1           CPU Test        Exercises the CPU to verify that the instruction
                                set and registers are working.

    2           ROM Test        Verifies the checksum for the ROM.

    3           RAM Test        Performs an extensive read/write RAM test.
                                Checks for and tests optional external RAM.
                                Testing may take up to 45 seconds depending
                                on the memory configuration of the controller.

    4           NVRAM Test      Verifies the checksum of the nonvolatile RAM.

    5           Drive Test      Verifies the touchscreen drive hardware. With
                                1.2 or later firmware, a failure may indicate the
                                touchscreen is not connected.

    6           CHOP Test       If a controller expansion board is installed via
                                the controller's CHOP connector, this test allows
                                the expansion board to perform its diagnostics.

    7           Reserved
    
    The results of the diagnostics are returned as a response packet before the 
    Acknowledge packet. DMask will have bits set where the corresponding test 
    failed and bits cleared where the tests passed or were not run.    
    """
    PACKET_TYPE_CHAR='D'
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,time,packet_bytes)
        diag_mask=self._packet_bytes[2]
        self.diag_mask=diag_mask
        
        # True means test FAILED
        # False means test passed or was not run.
        #
        self.id_test=diag_mask&1 == 0
        self.cpu_test=diag_mask&2 == 0
        self.rom_test=diag_mask&4 == 0
        self.ram_test=diag_mask&8 == 0
        self.nvram_test=diag_mask&16 == 0
        self.drive_test=diag_mask&32 == 0
        self.chop_test=diag_mask&64 == 0
        self.reserved=diag_mask&128 == 0
        
RESPONSE_PACKET_TYPES[ResponseDiagnostics.PACKET_TYPE_CHAR]=ResponseDiagnostics  

###############################################################################

#
# Emulate Packets
#      

# Query Packet
# TODO: Add Emulate Query Packet Class

# Command Packet
# TODO: Add Emulate Command Packet Class

# Response Packet  
# TODO: Add Emulate Response Packet Class

###############################################################################

#
# Filter Packets
#
 
# Query Packet
class QueryFilter(QueryPacket):
    """
    Used to request information about various aspects of the firmware 
    filtering algorithms used in the controller.
    """
    PACKET_TYPE_CHAR='f'
    def __init__(self):
        QueryPacket.__init__(self)
QUERY_PACKET_TYPES[QueryFilter.PACKET_TYPE_CHAR]=QueryFilter

# Command Packet
class CommandFilter(CommandPacket):
    """   
    Used to control various aspects of the firmware filtering algorithms
    used in the controller.
    
    ## AccuTouch Filtering
    
    ### Filter Command Packet Bytes:
    
    0   'F'                     Packet Type
    1   Type                    elo_type (READ ONLY:  ASCII '0' for AccuTouch, 
                                '1' for DuraTouch, '2' for IntelliTouch, 
                                and '3' for CarrollTouch)
    2   SLen                    sample_avg_count (1-255)
    3   Width                   sample_dev_thresh (1-255)
    4   States                  samples_before_state_change (1-255)
    5   Control (high 4 bytes)  press_detection_thresh (0-15)
    5   Control (low 4 bytes)   drive_sig_change_delay (0-15)
    6   0
    7   0

    ## IntelliTouch Filtering
    
    ### Filter Command Packet Bytes:
    
    0   'F'         Packet Type

    1   Type        elo_type (READ ONLY:  ASCII '0' for AccuTouch, 
                    '1' for DuraTouch, '2' for IntelliTouch, 
                    and '3' for CarrollTouch)

    2   Rep                    

    3   Ofs         amount (0-255) of surface wave energy absorption that is 
                    recognized as a touch. A small value increases touch 
                    sensitivity. A large value increases noise rejection. 
                    The factory default value is 1.          

    4   MinLen      The minimum width of a touch (0-255). As with the previous 
                    argument, a small value increases the sensitivity and a 
                    large value increases noise rejection. 
                    The factory default is 2.            

    5   MaxLen      The maximum width of a touch (0-255). This parameter controls
                    the rejection of multiple touches and splattered contaminants.
                    The factory default is 22.

    6   0

    7   0

    See ResponseFilter class for description of each bytes value.
    """
    PACKET_TYPE_CHAR='F'
    def __init__(self,sample_avg_count=4,sample_dev_thresh=8,
                 samples_before_state_change=8,press_detection_thresh=9,
                 drive_sig_change_delay=0):        
        self.sample_avg_count=sample_avg_count
        self.sample_dev_thresh=sample_dev_thresh
        self.samples_before_state_change=samples_before_state_change
        self.press_detection_thresh=press_detection_thresh
        self.drive_sig_change_delay=drive_sig_change_delay
        
        state=(samples_before_state_change<<4)+drive_sig_change_delay
        CommandPacket.__init__(self,'0',chr(sample_avg_count),chr(sample_dev_thresh),
                                chr(samples_before_state_change),chr(state))
COMMAND_PACKET_TYPES[CommandFilter.PACKET_TYPE_CHAR]=CommandFilter 

# Response Packet
class ResponseFilter(ResponsePacket):
    """
    Used to provide information about various aspects of the firmware 
    filtering algorithms used in the controller.

    ## Filter Response Packet Bytes:
    
    0   'F'                     Packet Type
    1   Type                    elo_type (READ ONLY: '0', '1', or '2')
    2   SLen                    sample_avg_count (1-255)
    3   Width                   sample_dev_thresh (1-255)
    4   States                  samples_before_state_change (1-255)
    5   Control (high 4 bytes)  press_detection_thresh (0-15)
    5   Control (low 4 bytes)   drive_sig_change_delay (0-15)
    6   0
    7   0

    The **Type** byte indicates the touchscreen type selected by the jumpers on the
    controller as follows: an ASCII '0' for AccuTouch, '1' for DuraTouch, 
    and '2' for IntelliTouch. The Type field cannot be changed.

    The **SLen** byte specifies the number of coordinate samples (1-255) to average
    before reporting the results. The factory default value is 4.
    
    The **Width** byte specifies the allowable deviation (±1-255) in validating a touch
    coordinate measurement. All touches within an averaging cycle (number specified
    by SLen) must be within this specified window or the coordinate is discarded. The
    factory default value is 32 for the E271-2210 controller and 8 for all other
    controllers.
    
    The **States** byte specifies the number (1-255) of valid touch detections (or
    untouch detections) to signify a change in the state Z-Axisof the touch event. For
    example, a value of 8 sets the state detection function to require that 8 contiguous
    touch measurements be made to cause the controller to process an initial touch.
    Similarly, 8 contiguous untouches must be measured to cause the controller to end
    the touch event. The factory default is 8.

    The **Control** byte comprises two 4-bit numeric values:

    The *high order* 4 bits specify a touch-down detection threshold (0-15), related to
    voltage. A value which is too low can cause the controller to report erroneous
    untouch coordinates. A value too high may prevent valid touches from being
    recognized. The factory default value is 9.
    
    The *low order* 4 bits specify the number of additional 0.5ms delays to use when
    changing the drive signals to the touchscreen (0-15). A value of 0 specifies a delay
    of 0.5ms, with each increment specifying an additional 0.5ms delay. The factory
    default value is 1 for the E271-2210 controller and 0 for all other controllers.    

    """
    PACKET_TYPE_CHAR='F'
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,time,packet_bytes)
        
        self.elo_type=chr(self._packet_bytes[2])
        self.sample_avg_count=self._packet_bytes[3]
        self.sample_dev_thresh=self._packet_bytes[4]
        self.samples_before_state_change=self._packet_bytes[5]
        self.press_detection_thresh=self._packet_bytes[6]&0b11110000
        self.drive_sig_change_delay=((self._packet_bytes[6]&0b00001111)+1)*.5
RESPONSE_PACKET_TYPES[ResponseFilter.PACKET_TYPE_CHAR]=ResponseFilter

###############################################################################

#
# Configuration Packets ('g')
#      

# Query Packet
class QueryConfiguration(QueryPacket):
    """
    Requests a complete dump of the controller's configuration for
    saving and restoring controller settings when switching between
    applications.
    
    The order and number of packets returned may change in future revisions of the
    controllers. Storage requirements may be queried with the ID command, (see page
    85). The number of packets in the transfer is returned in the P byte.
    
    The packets may be sent back to the controller as individual commands to restore
    (set) all controller parameters.
    """
    PACKET_TYPE_CHAR='g'
    def __init__(self):
        QueryPacket.__init__(self)
QUERY_PACKET_TYPES[QueryConfiguration.PACKET_TYPE_CHAR]=QueryConfiguration

# Command Packet
# Configuration Command Packet not supported.

# Response Packet  
# TODO: Add Configuration Response Packet Class

###############################################################################

#
# Timer Packets ('H','h')
#      

# Query Packet
class QueryTimer(QueryPacket):
    """
    Queries the User Timer functions of the controller.
    """
    PACKET_TYPE_CHAR='h'
    def __init__(self):
        QueryPacket.__init__(self)
QUERY_PACKET_TYPES[QueryTimer.PACKET_TYPE_CHAR]=QueryTimer

# Command Packet
class CommandTimer(CommandPacket):
    """   
    Controls the User Timer functions of the controller.

    Timer packet bytes (inferred from below text, actual byte table not in manual)
    TODO: Test that byte order assumed is correct.
    
    Byte    Name        Description
    
    0       'H'       
    1       Enable      1=Enable, 0=Disable
    2       TMode       1=Continuous Mode, 0=One-shot Mode
    3       0
    4-5     Interval    Timer expiration in 10ms increments. (1-65535)
    6-7     0

    **Enable** is a byte value where the least significant bit is 1 to enable the Timer or 0 to
    disable the Timer. Timer packet transmission must also be Un-Quieted with the
    Quiet command, described on page 98. The factory default for the Timer is
    disabled.

    The **TMode** byte determines the action taken upon the expiration of the Timer,
    either One-shot or Continuous. If the least significant bit is 1 (Continuous Mode),
    the Timer is automatically restarted using the specified Interval value. If it is 0
    (One-shot Mode), the Timer is disabled when it expires. The factory default for the
    TMode is One-shot.

    The **Interval** word specifies the number of Timer ticks (in 10ms increments) before
    the expiration of the Timer. The factory default is 100 (1 second).

    The **Current** word contains zero when the Timer expires and a Timer packet is sent
    to the host. If queried prior to expiration or while the Timer is Quieted, Current
    will contain the amount of time remaining before expiration.
    
    **NOTE:**
        Specifying an Interval of 0 (or 1 on slow computers) will flood the 
        host with Timer packets so that communication with the controller may 
        become impossible.
    """
    PACKET_TYPE_CHAR='H'
    def __init__(self,enable=1,mode=0,interval=1000):     
        """
        Defaults: Enable a single shot Timer that has a duration of 1 second.
        """
        self.enable=enable
        self.mode=mode
        self.interval=interval//10        
        interval_high_byte=self.interval & 0xFF00
        interval_low_byte=self.interval & 0x00FF        
        CommandPacket.__init__(self,chr(enable),chr(mode),chr(0),chr(interval_low_byte),chr(interval_high_byte))
COMMAND_PACKET_TYPES[CommandTimer.PACKET_TYPE_CHAR]=CommandTimer 

# Response Packet
class ResponseTimer(ResponsePacket):
    """
    Provides information for the User Timer of the controller. Automatically 
    returned by controller when the Timer expires. 
    
    Timer packet bytes (inferred actual byte table not in manual)
    TODO: Test that byte order assumed is correct.
    
    Byte    Name        Description
    
    0       'H'       
    1       Enable      1=Enable, 0=Disable
    2       TMode       1=Continuous Mode, 0=One-shot Mode
    3       0
    4-5     Interval    Timer expiration in 10ms increments. (1-65535)
    6-7     Current     Remaining Timer Time in 10msec intervals. 
                        0 when Timer has expired.

    See ControlTimer class description for details on bytes returned in packet.
    """
    PACKET_TYPE_CHAR='H'
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,time,packet_bytes)
        interval=self._packet_bytes[4:6]
        current=self._packet_bytes[6:8]
        self.enable=self._packet_bytes[2]
        self.mode=self._packet_bytes[3]     
        self.interval= ((interval[1] << 8) + interval[0])*10.0
        self.current= ((current[1] << 8) + current[0])*10.0

RESPONSE_PACKET_TYPES[ResponseTimer.PACKET_TYPE_CHAR]=ResponseTimer

###############################################################################

#
# ID Packets('i')
#      

# Query Packet
class QueryID(QueryPacket):
    """
    Queries various information about the controller and touchscreen.

    See ResponseID class description for details on bytes returned by ResponseID
    packet.
    """
    PACKET_TYPE_CHAR='i'
    def __init__(self):
        QueryPacket.__init__(self)
QUERY_PACKET_TYPES[QueryID.PACKET_TYPE_CHAR]=QueryID

# Command Packet
# ID Command Packet Not Supported

# Response Packet  
class ResponseID(ResponsePacket):
    """
    Returns various information about the controller and touchscreen.

    ID packet bytes (inferred, actual byte table not in manual)
    TODO: Test that byte order assumed is correct.
    
    Byte    Name        Description
    
    0       Type        Touchscreen type ('0','1', or '2')
    1       IO          Communication interface type in use ('0' for Serial)
    2       Features    Installed features of the controller (8 bits)
    3       Minor       Minor firmware revision level
    4       Major       Major firmware revision level
    5       P           Num packets returned when 'g' query is made.
    5       IFlag       1=E271-2210, 0=E271-2200.
                    
    The **Type** byte indicates the touchscreen type selected by the jumpers on the
    controller as follows: an ASCII '0' for AccuTouch, '1' for DuraTouch, and '2' for
    IntelliTouch.

    The **IO** byte indicates the type of communication interface that is in use by the
    controller as follows: an ASCII '0' for serial, '1' for PC-Bus, and '2' for Micro
    Channel.

    The **Features** byte indicates installed features of the controller and has the
    following bit positions:

        Bit     Feature
    
        0       Reserved
        1       Reserved
        2       Reserved
        3       Reserved
        4       Reserved - External A/D converter
        5       Reserved - RAM is 32K bytes
        6       Reserved - RAM available
        7       Reserved - Z-axis available
    
    The **Minor** byte reports the minor firmware revision level. 
    The **Major** byte reports the major firmware revision level. 
    The Minor and Major bytes may be treated as an integer.
    
    The P byte reports the number of packets to expect when querying the 
    configuration with the 'g' command, not including the Acknowledge packet 
    that follows. P may change with future firmware revisions.

    The Class byte indicates the model of the controller as follows:

    Value   Controller

    00h     E271-2200
    01h     E271-2210
    03h     E281-2310
    04h     Reserved
    05h     E281-2310B
    06h     2500S
    07h     2500U
    08h     3000U
    09h     4000U
    0Ah     4000S
    0Bh     Reserved
    0Ch     Reserved
    0Dh     Reserved
    0Eh     COACh IIs™

    ## E271-2210 vs. E271-2200 Controllers

    The E271-2210 controller is software compatible with the obsolete 
    E271-2200 with the following exceptions:

        1. Low Power Mode is not supported. See Low Power command.
        2. 38,400 Baud is not supported. See Parameter command.
        3. Filtering parameters are slightly different. See Filter command.
    """
    PACKET_TYPE_CHAR='I'
    typeChar2ModelType={'0':'Accutouch','1':'DuraTouch','2':'IntelliTouch','3':'CarrollTouch'}
    ioChar2CommType={'0':'Serial','1':'PC-Bus','2':'Micro Channel','3':'ADB','4':'USB'}
    ctrlByte2CtrlType={0:'E271-2200',1:'E271-2210',3:'E281-2310',5:'E281-2310B',6:'2500S',7:'2500U',8:'3000U',9:'4000U',10:'4000S',14:'COACh IIs'}
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,time,packet_bytes)        
        self.screen_type=self.typeChar2ModelType.get(chr(self._packet_bytes[2]),'UNKNOWN')
        self.comm_interface=self.ioChar2CommType.get(chr(self._packet_bytes[3]),'UNKNOWN')
        self._features=self._packet_bytes[4]
        features=self._features
        self._reserved1=features&1 != 0
        self._reserved2=features&2 != 0
        self._reserved3=features&4 != 0
        self._reserved4=features&8 != 0
        self.extern_a2d=features&16 != 0
        self.ram_32K_bytes=features&32 != 0
        self.ram_available=features&64 != 0
        self.z_axis_available=features&128 != 0
        self._minor=self._packet_bytes[5]
        self._major=self._packet_bytes[6]
        self.firmware_version=u'{0}.{1}'.format(self._major,self._minor)
        self.p=self._packet_bytes[7]
        self.controller_model=self.ctrlByte2CtrlType.get(int(self._packet_bytes[8]),'UNKNOWN')      
RESPONSE_PACKET_TYPES[ResponseID.PACKET_TYPE_CHAR]=ResponseID

###############################################################################

#
# Jumpers Packets ('j')
#      

# Query Packet
class QueryJumpers(QueryPacket):
    """
    Requests the jumper settings on the controller.

    See ResponseJumpers class description for details on bytes returned by 
    ResponseJumpers packet.
    """
    PACKET_TYPE_CHAR='j'
    def __init__(self):
        QueryPacket.__init__(self)
QUERY_PACKET_TYPES[QueryJumpers.PACKET_TYPE_CHAR]=QueryJumpers

# Command Packet
# Jumpers packet can not be set.

# Response Packet  
class ResponseJumpers(ResponsePacket):
    """
    Returns the jumper settings on the controller.
    
    The **Type** byte indicates the touchscreen type selected by the jumpers on the
    controller as follows: an ASCII '0' for AccuTouch, '1' for DuraTouch, and '2' for
    IntelliTouch (reserved). Controllers are shipped jumpered for AccuTouch (J5
    installed).
    
    The **IO** byte indicates the type of communication interface that is in use by the
    controller as follows: an ASCII '0' for serial, '1' for PC-Bus, and '2' for Micro
    Channel.
    
    The **X1** Byte is an ASCII '0' if the controller's setup jumper (J7) is present and the
    controller is booting from the jumper settings. It is a '1' if the controller is booting
    from settings in NVRAM, and all jumper settings are ignored. Controllers are
    shipped jumpered to boot from jumpers (J7 installed).
    
    The **X2** byte is an ASCII '0' if the controller is jumpered for Single-Point Mode on
    power-on. It is a '1' for Stream Mode. Controllers are shipped jumpered for Stream
    Mode (J4 not installed).
    
    The **S1** byte indicates the jumper-selected baud rate as follows:
    
        Value   Baud Rate
        0       300
        1       600
        2       1200
        3       2400
        4       4800
        5       9600
        6       19200
        7       38400
    
    Serial controllers are shipped jumpered for 9600 baud. The values for the S1 byte
    correspond to those used in the Parameter command (page 95). Not all of the
    above baud rates are available through jumper settings.
    
    The **S2** byte is an ASCII '0' if serial Hardware Handshaking is disabled by the J3
    jumper on power-on. It is a '1' if Hardware Handshaking is enabled. Serial
    controllers are shipped jumpered for Hardware Handshaking enabled (J3 not
    installed).
    
    The **S3** byte is an ASCII '0' if the SmartSet ASCII Mode is selected on power-on
    by the J2 jumper. A '1' indicates the SmartSet Binary Mode. Serial controllers are
    shipped jumpered for Binary Mode (J2 not installed).
    """
    PACKET_TYPE_CHAR='J'
    ELO_TYPES={'0':'AccuTouch','1':'DuraTouch','2':'IntelliTouch','3':'CarrollTouch'}
    IO_TYPES={'0':'Serial','1':'PC-Bus','2':'Micro Channel','3':'ADB','4':'USB'}
    BAUD_MAPPING={0:300,
                  1:600,
                  2:1200,
                  3:2400,
                  4:4800,
                  5:9600,
                  6:19200,
                  7:38400
                  }
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,time,packet_bytes)        
        self.type=self.ELO_TYPES.get(chr(self._packet_bytes[2]),'UNKNOWN')
        self.io=self.IO_TYPES.get(chr(self._packet_bytes[3]),'UNKNOWN') 
        if self.type == 'AccuTouch':
            self.nvram_boot=chr(self._packet_bytes[4]) == '1'
            self.stream_mode=chr(self._packet_bytes[5]) == '1'  
        else:
            self.nvram_boot=True 

        if self.type == 'AccuTouch':
            self.nvram_boot=chr(self._packet_bytes[4]) == '1'
            self.hardware_handshaking=chr(self._packet_bytes[7]) == '1'  
            self.smartset_binary_mode=chr(self._packet_bytes[8]) == '1'            
        else:
            self.nvram_boot=True 
            self.stream_mode=True  
            self.hardware_handshaking=True  
            self.smartset_binary_mode=True           
 
        self.baud_rate=self.BAUD_MAPPING.get(self._packet_bytes[6],0)     

RESPONSE_PACKET_TYPES[ResponseJumpers.PACKET_TYPE_CHAR]=ResponseJumpers

###############################################################################

#
# Key Packets ('K','k')
#      

# Query Packet
class QueryKey(QueryPacket):
    """
    Query the Key Byte value. The Key Byte may be used for multiplexing 
    multiple controllers on a common serial line.
    """
    PACKET_TYPE_CHAR='k'
    def __init__(self):
        QueryPacket.__init__(self)
QUERY_PACKET_TYPES[QueryKey.PACKET_TYPE_CHAR]=QueryKey

# Command Packet
class CommandKey(CommandPacket):
    """
    Used to set the Key Byte value. The Key Byte may be
    used for multiplexing multiple controllers on a common serial line.
    
    The KeyValue byte may be from 1 255. A 0 value disables this function.
    
    When the Key command is issued, the Acknowledge packet and all subsequent
    packets will be in the new format.
    
    Keyed packets are disabled by factory default.
    
    Keyed packets are discussed on page 52.
    """
    PACKET_TYPE_CHAR='K'
    def __init__(self,key_value=0): 
        self.key_value=key_value
        CommandPacket.__init__(self,chr(key_value))
COMMAND_PACKET_TYPES[CommandKey.PACKET_TYPE_CHAR]=CommandKey 

# Response Packet  
class ResponseKey(ResponsePacket):
    """
    Return the Key Byte value. The Key Byte may be used for multiplexing 
    multiple controllers on a common serial line.
    
    The KeyValue byte may be from 1 255. A 0 value means the Key function is
    disabled.
    """
    PACKET_TYPE_CHAR='K'
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,time,packet_bytes)        
        self.key_value=self._packet_bytes[2]
RESPONSE_PACKET_TYPES[ResponseKey.PACKET_TYPE_CHAR]=ResponseKey

###############################################################################

#
# Low Power Packets ('L','l')
#      

# Query Packet
class QueryLowPower(QueryPacket):
    """
    Requests whether Low Power Mode is enabled or not.
    """
    PACKET_TYPE_CHAR='l'
    def __init__(self):
        QueryPacket.__init__(self)
QUERY_PACKET_TYPES[QueryLowPower.PACKET_TYPE_CHAR]=QueryLowPower

# Command Packet
class CommandLowPower(CommandPacket):
    """
    Controls the Low Power Mode of the controller.
    
    During times when processing in the controller is minimal (no touch and no
    communications in progress), the controller can enter a Lower Power Mode. 
    Upon receipt of data from the host or the event of a touch, the controller
    exits this mode and normal processing continues until the next idle period. 
    
    Low Power Mode is useful with battery-powered computers.
    
    The least significant bit of the Enable byte is 1 for Low Power Mode 
    or 0 for normal mode.
    
    Low Power Mode is disabled by factory default.

    Low Power Mode is not supported by the E271-2210 controller.   
    """
    PACKET_TYPE_CHAR='L'
    def __init__(self,enable_low_power=False): 
        self.enable_low_power=enable_low_power
        CommandPacket.__init__(self,chr(enable_low_power))
COMMAND_PACKET_TYPES[CommandLowPower.PACKET_TYPE_CHAR]=CommandLowPower 

# Response Packet  
class ResponseLowPower(ResponsePacket):
    """
    Returns whether Low Power Mode is enabled or not.

    The least significant bit of the Enable byte is 1 for Low Power Mode 
    or 0 for normal mode.
    """
    PACKET_TYPE_CHAR='L'
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,time,packet_bytes)        
        self.enable_low_power=self._packet_bytes[2]>0
RESPONSE_PACKET_TYPES[ResponseLowPower.PACKET_TYPE_CHAR]=ResponseLowPower

###############################################################################

#
# Mode Packets ('M','m')
#      

# Query Packet
class QueryMode(QueryPacket):
    """
    Requests the various operating modes of the controller.
    """
    PACKET_TYPE_CHAR='m'
    def __init__(self):
        QueryPacket.__init__(self)
QUERY_PACKET_TYPES[QueryMode.PACKET_TYPE_CHAR]=QueryMode

# Command Packet
class CommandMode(CommandPacket):
    """
    Sets the various operating modes of the controller.
    
    The Mode command offers two methods of setting the various operating modes;
    Binary and ASCII. Modes are discussed in the tutorial in Chapter 4.
    
    ## Binary Mode Setting

    The binary method uses two bitmapped bytes to set the mode. 
    The binary method is indicated by the presence of a null byte in position 1.
    The ASCII method uses a string of ASCII letters to set the mode, useful if 
    the controller is connected to a terminal for evaluation purposes. 
    
    The Mode1 byte has the following bit positions, corresponding to bit 
    positions in the Status byte in the Touch packet:
    
    Bit     Function            Description
    0       Initial Touch Mode  If 1, a Touch packet will be transmitted on
                                initial touch. Bit 0 in the Status byte of the
                                Touch packet will be set indicating an Initial
                                touch.

    1       Stream Mode         If 1, Touch Packets will be transmitted
                                continuously while the touchscreen is being
                                touched. Bit 1 in the Status byte of the Touch
                                packet will be set indicating Stream touches.
                                When Stream Mode is disabled, the controller
                                is in Single-Point Mode.

    2       Untouch Mode        If 1, a Touch Packet will be transmitted on
                                untouch (release). Bit 2 in the Status byte of
                                the Touch packet will be set indicating an
                                Untouch.

    3       Reserved

    4       Warning Pending     If 1, an Acknowledge query should be issued
                                to receive non-command-related warning(s).
                                This bit is only valid on a Mode query.

    5       Reserved

    6       Range Checking      If 1, Range Checking Mode is enabled. Bit 6
                                in the Status byte of the Touch packet will be
                                set indicating a touch is outside the
                                calibration points. Calibration Mode must also
                                be enabled (bit 2 of Mode2 below) and
                                Calibration Points set with the Calibration
                                command. Range Checking Mode is typically
                                combined with Trim Mode (bit 1 of Mode2
                                below). 

    7       Reserved            Always 1. Reserved for Z-axis Disable.
    
    The Mode2 byte has the following bit positions:
    
    Bit     Function            Description
    
    0       Reserved
    
    1       Trim Mode           If 1, Trim Mode is enabled. Touches outside
                                the calibration points will have their
                                coordinates adjusted to the edge of the
                                calibrated area. This mode effectively
                                expands all touch zones on the edge of the
                                image to include the associated overscan
                                area. Trim Mode requires Range Checking
                                Mode to be enabled (bit 6 of Mode1 above).

    2       Calibration Mode    If 1, Calibration Mode is enabled. Touch
                                coordinates will be mapped to the display
                                image using the calibration points acquired at
                                the edges of the image. Coordinates will be
                                scaled 0-4095 by default within the calibrated
                                area unless Scaling Mode (bit 3 below) is
                                also enabled and other Scaling Points
                                defined. Coordinates will be scaled beyond
                                these ranges if a touch is outside the
                                calibration points and Trim Mode is disabled.
                                Calibration Points must set with the
                                Calibration command.

    3       Scaling Mode        If 1, Scaling Mode is enabled. Touch
                                coordinates will be scaled to the signed
                                ranges specified with the Scaling command. If
                                Scaling Mode is disabled, coordinates will be
                                scaled 0-4095 by default. Scaling Mode is
                                typically used with Calibration Mode. Scaling
                                Mode may be used without Calibration Mode
                                to emulate coordinate ranges returned by
                                other controllers.

    4       Reserved
    
    5       Reserved
    
    6       Tracking Mode       If 1, Tracking Mode is enabled. In Tracking
                                Mode, Stream touches which repeat the same
                                coordinate will not be transmitted to the host.
                                This mode is only useful if coordinate scaling
                                is set below the natural variation of
                                coordinates for a constant touch. Tracking
                                Mode requires Stream Mode (bit 1 of Mode1
                                above).
    7       Reserved
    
    ## ASCII Mode Setting
    
    The controller modes may also be configured with an ASCII packet. 
    XXXXXX represents any of the following values in string form.

    'I'     Report Initial Touches
    'S'     Report Stream Touches
    'U'     Report Untouches
    'T'     Enable Tracking Mode
    'P'     Enable Trim Mode
    'C'     Enable Calibration (automatic if 'P' selected)
    'M'     Enable Scaling
    'B'     Enable Range Checking (automatic if 'P' selected)
    
    If an invalid character is present in the string, the remainder of the 
    string is ignored.
    
    When the ASCII version of the Mode command is received, it starts by 
    disabling all modes and reporting options. The ASCII codes that follow then
    enable the specified modes and reporting options. Because the XXXXXXX string
    may be a maximum of 7 characters, and more than 7 modes are available, 
    the 'P' character also enables the Calibration and Range Checking Modes.
    
    If the Initial Touch, Stream, and Untouch Modes are disabled, no Touch packets
    will be transmitted unless a Touch query is issued. See Touch command, page 102.
    
    The factory default mode has Initial Touches, Stream Touches, and Untouches
    enabled. The Single-Point Mode jumper (J4) disables Stream Touches and
    Untouches when installed.
    """
    PACKET_TYPE_CHAR='M'
    def __init__(self,mode1_byte=0,mode2_byte=0):
        self.mode1_byte=mode1_byte
        self.mode2_byte=mode2_byte         
        CommandPacket.__init__(self,*(0,mode1_byte,mode2_byte))
COMMAND_PACKET_TYPES[CommandMode.PACKET_TYPE_CHAR]=CommandMode 

# Response Packet  
class ResponseMode(ResponsePacket):
    """
    Returns the various operating modes of the controller.   
    See CommandMode Class for details on the returned data bytes.
    """
    PACKET_TYPE_CHAR='M'
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,time,packet_bytes)
        #TODO: Parse returned data.
RESPONSE_PACKET_TYPES[ResponseMode.PACKET_TYPE_CHAR]=ResponseMode

###############################################################################

#
# Nonvolatile RAM (NVRAM) Packets ('N')
#      

# Query Packet
# Query packet type not supported for NVRAM

# Command Packet
class CommandNVRAM(CommandPacket):
    """
    Saves/restores controller settings in the on-board nonvolatile
    memory (NVRAM). NVRAM can be used to store power-on defaults.

    Power-on defaults are from NVRAM if the J7 jumper is installed. The use of
    NVRAM is discussed on page 8 and in Chapter 4—SmartSet Tutorial.

    The least significant bit of the Direction byte is 1 to save the settings 
    in NVRAM, or 0 to restore the settings from NVRAM.

    The Areas byte has the following bit positions:

        Bit     Area
        0       Setup Area
        1       Calibration
        2       Scaling

    The Setup Area consists of all parameters except the Calibration and Scaling
    parameters. All three areas may be saved or restored in any combination 
    by setting the appropriate bits.

    The least significant bit of the Page byte is 0 for the primary area, 
    or 1 for the secondary area. The Page is only required if setting the 
    Calibration or Scaling parameters, as the controller only has one Setup Area.
    """
    PACKET_TYPE_CHAR='N'
    def __init__(self,save_settings=True,active_areas=0,use_secondary_area=False):
        self.save_settings=save_settings # 0 or 1
        self.active_areas=active_areas # 0, 1, 2, or 3
        self.use_secondary_area=use_secondary_area # 0 or 1
        CommandPacket.__init__(self,save_settings,active_areas,use_secondary_area)
COMMAND_PACKET_TYPES[CommandNVRAM.PACKET_TYPE_CHAR]=CommandNVRAM 

# Response Packet  
class ResponseNVRAM(ResponsePacket):
    """
    Returns the what controller settings were saved / restored in the on-board
    nonvolatile memory (NVRAM)
    
    See CommandNVRAM Class for details on the returned data bytes.
    """
    PACKET_TYPE_CHAR='N'
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,time,packet_bytes)
        self.save_settings=self._packet_bytes[2] # 0 or 1
        self.active_areas=self._packet_bytes[3] # 0, 1, 2, or 3
        self.use_secondary_area=self._packet_bytes[4] # 0 or 1
RESPONSE_PACKET_TYPES[ResponseNVRAM.PACKET_TYPE_CHAR]=ResponseNVRAM

###############################################################################

#
# Owner Packets ('o','O')
#      

# Query Packet
class QueryOwner(QueryPacket):
    """
    Reserved for identifying custom firmware.
    """
    PACKET_TYPE_CHAR='o'
    def __init__(self):
        QueryPacket.__init__(self)
QUERY_PACKET_TYPES[QueryOwner.PACKET_TYPE_CHAR]=QueryOwner

# Command Packet
# Command Owner Packet is not supported.

# Response Packet 
class ResponseOwner(ResponsePacket):
    """
    Reserved for identifying custom firmware.
    """
    PACKET_TYPE_CHAR='O'
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,time,packet_bytes)
        self.name=''.join([chr(b) for b in self._packet_bytes[2:8]])
        
RESPONSE_PACKET_TYPES[ResponseOwner.PACKET_TYPE_CHAR]=ResponseOwner

###############################################################################

#
# Parameter Packets ('P','p')
#      

# Query Packet
class QueryParameter(QueryPacket):
    """
    Requests controller communication parameters.
    
    See CommandParameter class for details on bytes returned in the ResponseParameter
    packet.
    """
    PACKET_TYPE_CHAR='p'
    def __init__(self):
        QueryPacket.__init__(self)
QUERY_PACKET_TYPES[QueryParameter.PACKET_TYPE_CHAR]=QueryParameter

# Command Packet
class CommandParameter(CommandPacket):
    """
    Changes controller communication parameters.

        Byte    Description
    
        0       'P'
        1       IO byte
        2       Ser1 byte
        3       Ser2 byte
        4-7     0
    
    When the parameters are set with this command, the Acknowledge packet is
    returned using the new communication parameters. Therefore, the host
    communication parameters must be changed immediately after issuing the
    Parameter command.

    The IO byte indicates the type of communication interface that is in use by 
    the controller as follows: 

        '0'     serial
        '1'     PC-Bus
        '2'     Micro Channel. 
        
    The IO field cannot be changed.
    
    ##Serial Controllers

    The **Ser1** byte has the following bit definitions:

    Bit     Description
    0       Baud Rate (see table below)
    1       Baud Rate (see table below)
    2       Baud Rate (see table below)
    3       0 = 8 bit data, 1 = 7 bit data
    4       0 = 1 stop bit, 1 = 2 stop bits
    5       1 = parity enabled as per bits 6 7
    6       Parity Type (see table below)
    7       Parity Type (see table below)

    The **Ser2** byte has the following bit definitions:

    Bit     Description
    0       1 = Checksum required
    1       1 = Software Handshaking enabled
    2       1 = Hardware Handshaking enabled
    3       1 = Invert Hardware Handshaking
    4       Reserved
    5       Reserved
    6       Reserved
    7       1 = Full Duplex (echo enabled)
    

    Bits    Baud Rate

    000     300
    001     600
    010     1200
    011     2400
    100     4800
    101     9600
    110     19200
    111     38400 (E271-2200 only)

    Bits    Parity Type
    
    00      Even
    01      Odd
    10      Space
    11      Mark
    
    ## Checksum Bit
    
    If the Checksum Bit is 0, the controller does not check the validity of received
    commands. If the Checksum Bit is 1, and the Checksum is incorrect in a received
    command, error code '3' will be returned in the Acknowledge packet. Checksums
    are always calculated and transmitted by the controller to the host. The host may
    choose to ignore the Checksum or request the controller to retransmit corrupted
    packets. See Checksum Byte, page 51.
    
    ## Software Handshaking Bit
    
    If the Software Handshaking Bit is 1, the controller will recognize the software
    flow control convention of XON/XOFF (ASCII 'Control Q' and 'Control S').
    
    If the Software Handshaking Bit is 0, software flow control is disabled. The
    controller will not send ^S/^Q characters, and ^S/^Q characters received by the
    controller outside a packet will generate an error.
    
    Software Handshaking is disabled by factory default. For more information, see
    Software Handshaking, page 53.

    ## Hardware Handshaking Bit

    If the Hardware Handshaking Bit is 1, the controller will support hardware
    handshake signals typically implemented in EIA RS-232 communications.
    Hardware Handshaking is enabled by factory default. To ease troubleshooting of
    the initial installation, jumper J3 can be installed to force the controller to ignore
    Hardware Handshaking. For more information, see Hardware Handshaking, page
    53.
    
    ## Invert Hardware Handshaking Bit
    
    If the Invert Hardware Handshaking Bit is 1, the sense of the handshaking signals
    are inverted (except DSR). This feature is provided as a tool for use in installations
    where the controller may be forced to share a serial link with another device.
    Hardware Handshaking is not inverted by factory default.
    
    ## Full-Duplex Bit

    If the Full-Duplex Bit is 1, each character sent to the controller is echoed. When
    Half-Duplex Mode is selected (Full-Duplex Bit is 0), the controller does not
    retransmit each received character.

    The factory default is Half-Duplex. For more information, see Duplex, page 54.

    ## Other Communication Parameters

    Setting the controller to 7-Bit Mode will make many commands unusable. As the
    SmartSet command set requires 8-bit binary data, 7-Bit Mode can only be used
    when the controller is in a Partial Emulation Mode and is transmitting ASCII data.
    
    The total number of serial bits must be between 7 and 10 inclusive. For example, 8
    Data Bits, 2 Stop Bits, and Even Parity is illegal.
    
    The factory defaults for serial controllers when booting from Nchr(mode1_byte)VRAM are 9600
    Baud, 8 Data Bits, 1 Stop Bit, No Parity, normal Hardware Handshaking enabled,
    Software Handshaking disabled, Half Duplex, and correct Checksum not required.

    The Baud Rate and Hardware Handshaking options may be overridden if the
    controller boots from jumper settings.
    """
    PACKET_TYPE_CHAR='P'
    baud_mapping={300:0,
                  600:1,
                  1200:2,
                  2400:3,
                  4800:4,
                  9600:5,
                  19200:6,
                  38400:7
                  }
    parity_mapping={
                'Even':0,
                'Odd':64,
                'Space':128,
                'Mark':192
                 }
    def __init__(self,baud_rate=9600, data_7bit=False, stop_bits_2=False,
                 parity_enabled=False, parity_type=None,
                 checksum_enabled=True,sw_hshk=False,hw_hshk=True,invert_hw_hshk=False,
                 full_duplex=False
                 ):
        self.io_type='0' # Serial = '0'
        self.serial_settings1=self.baud_mapping.get(baud_rate,0)+(8*data_7bit)+(16*stop_bits_2)+(32*parity_enabled)+self.parity_mapping.get(parity_type,0)
        self.serial_settings2=checksum_enabled+(2*sw_hshk)+(4*hw_hshk)+(8*invert_hw_hshk)+(128+full_duplex)
        CommandPacket.__init__(self,self.io_type,self.serial_settings1,self.serial_settings2)
COMMAND_PACKET_TYPES[CommandParameter.PACKET_TYPE_CHAR]=CommandParameter 


# Response Packet 
class ResponseParameter(ResponsePacket):
    """
    Returns the current controller communication parameters.
    
    See CommandParameter class for details on bytes returned.
    """
    PACKET_TYPE_CHAR='P'
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,time,packet_bytes)
        self.io_type=chr(self._packet_bytes[2])
        self.serial_settings1=self._packet_bytes[3]
        self.serial_settings2=self._packet_bytes[4]
RESPONSE_PACKET_TYPES[ResponseParameter.PACKET_TYPE_CHAR]=ResponseParameter

###############################################################################
#
# Scaling Packets ('S','s')
#      

# Query Packet
class QueryScaling(QueryPacket):
    """
    Scaling is discussed in the tutorial in Chapter 4, and an example is given 
    in Chapter 5.

    Querying the Scaling Parameters

    axis specifies the coordinate axis by using lower-case ASCII characters 
    'x','y', or 'z'. Scaling parameters are returned in the controller's 
    internal Offset, Numerator, and Denominator format. These values can be 
    saved and later restored directly in this format.

    Note there is no way to directly query the LowPoint and HighPoint values. 
    These values can be calculated by the following formulas:

        LowPoint = Offset
        HighPoint = LowPoint + Numerator
    """
    PACKET_TYPE_CHAR='s'
    def __init__(self,axis):
        QueryPacket.__init__(self,axis)
QUERY_PACKET_TYPES[QueryScaling.PACKET_TYPE_CHAR]=QueryScaling

# Command Packet
class CommandScaling(CommandPacket):
    """
    Setting the Scaling Points from the Host

    Scaling is accomplished by the host transmitting a range of coordinates, 
    typically equivalent to the display resolution. These coordinates are then 
    converted by the controller into an internal Offset, Numerator, and 
    Denominator format.

    AXIS specifies the coordinate axis to be scaled by using upper-case 
    ASCII characters 'X','Y', or 'Z'.

    LowPoint and HighPoint are signed integers specifying an axis range. 
    For example, if two scaling points are specified as (XLow,YLow) 
    and (XHigh,YHigh), LowPoint = XLow and HighPoint = XHigh for the X-axis. 
    If a HighPoint value is greater than a LowPoint value, 
    software axis inversion is performed.


    Setting the Scaling Parameters as Offset, Numerator, and Denominator

    This command is used to restore scaling parameters previously queried 
    from the controller.

    axis specifies the coordinate axis to be scaled by using lower-case ASCII 
    characters 'x','y', or 'z'.

    Z-Axis Scaling

    On AccuTouch touchscreen controllers, Z-axis scaling is typically not 
    required as no Z data is available. The controller defaults to 0-255, 
    but always returns the HighPoint value.

    Z-axis scaling is supported on the IntelliTouch 2500S controller.

    Setting or Querying the Invert Axes Flags

    Axes may be inverted by using these flags, or preferably, by swapping 
    the LowPoint and HighPoint scaling values.

    IMask is a byte value where the least significant 3 bits specify 
    which axes to invert as follows:

        Bit Axis
    
        0   Invert X Axis
        1   Invert Y Axis
        2   Invert Z Axis

    Scaling and Axis Inversion are disabled by factory default.
    """
    PACKET_TYPE_CHAR='S'
    def __init__(self,axis=0,low_point=None,high_point=None,
                 offset=None,numerator=None,denominator=None):
        if axis:
            if low_point is not None and high_point is not None:
                low_point_chr1=int(low_point) & 0b11111111 # get first byte of lowpoint 2-bytes and convert to chr
                low_point_chr2=int(low_point) >> 8 # get second byte of lowpoint 2-bytes and convert to chr
                high_point_chr1=int(high_point) & 0b11111111 # get first byte of highpoint 2-bytes and convert to chr
                high_point_chr2=int(high_point) >> 8 # get second byte of highpoint 2-bytes and convert to chr
                CommandPacket.__init__(self,axis.upper(),low_point_chr1,low_point_chr2,high_point_chr1,high_point_chr2)
            elif offset is not None and numerator is not None and denominator is not None:
                offset_chr1=int(offset) & 0b11111111 # get first byte of offset 2-bytes and convert to chr
                offset_chr2=int(offset) >> 8 # get second byte of offset 2-bytes and convert to chr
                numerator_chr1=int(numerator) & 0b11111111 # get first byte of numerator 2-bytes and convert to chr
                numerator_chr2=int(numerator) >> 8 # get second byte of numerator 2-bytes and convert to chr
                denominator_chr1=int(denominator) & 0b11111111 # get first byte of denominator 2-bytes and convert to chr
                denominator_chr2=int(denominator) >> 8 # get second byte of denominator 2-bytes and convert to chr
                CommandPacket.__init__(self,axis.lower(),offset_chr1,offset_chr2,numerator_chr1,numerator_chr2,denominator_chr1,denominator_chr2)
            else:
                print2err("Warning: Calibration must be set using low_point and high_point, OR offset, numerator, and denominator.")
COMMAND_PACKET_TYPES[CommandScaling.PACKET_TYPE_CHAR]=CommandScaling 


# Response Packet 
class ResponseScaling (ResponsePacket):
    """
    Returns the current controller scaling settings.
    
    See CommandScaling  class for details on bytes returned.
    """
    PACKET_TYPE_CHAR='S'
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,packet_bytes)
        self.axis=chr(self._packet_bytes[2])        
        self.offset=self._packet_bytes[4]<<8+self._packet_bytes[3]
        self.numerator=self._packet_bytes[6]<<8+self._packet_bytes[5]
        self.denominator=self._packet_bytes[8]<<8+self._packet_bytes[7]        
        
RESPONSE_PACKET_TYPES[ResponseScaling.PACKET_TYPE_CHAR]=ResponseScaling


###############################################################################
#
# Touch Packets
#      

# Query Packet
class QueryTouch(QueryPacket):
    """
    """
    PACKET_TYPE_CHAR='t'
    def __init__(self):
        QueryPacket.__init__(self)
QUERY_PACKET_TYPES[QueryTouch.PACKET_TYPE_CHAR]=QueryTouch

# Command Packet
# Touch can not be set.

# Response Packet 
class ResponseTouch(ResponsePacket):
    TOUCH_PRESS=1
    TOUCH_MOVE=2
    TOUCH_RELEASE=4
    RESERVED1=8
    WARNINGS_PENDING=16
    RESERVED2=32
    OUT_OF_RANGE=64
    Z_SUPPORTED=128
    """
    Each Touch event has the following 10 byte signature:
    
    Byte    Description
    
    0       'U' packet delimiter  
    1       'T' Touch packet type identifier 
    2       Status byte  
    3-4     X pos  (12 bits)
    5-6     Y pos  (12 bits)
    7-8     Z Pos  (8 bits)
    9       Packet checksum  
    
    ** X, Y pos has origin of TOP RIGHT corner.chr(mode1_byte)
    
    The status byte The Status byte has the following bit positions. 
    Touch packets will only be transmitted with the various bits set if 
    the corresponding mode is enabled with the Mode command.

    Bit     Status              Description
    0       Initial Touch       If 1, the Touch packet is for an Initial touch. 
                                Initial Touch Mode is enabled by bit 0 in the 
                                Mode1 byte of the Mode command.

    1       Stream Touch        If 1, the Touch packet is for a Stream touch, 
                                a coordinate transmitted continuously 
                                while the touchscreen is being touched. 
                                Stream Mode is enabled by bit 1 in the 
                                Mode1 byte of the Mode command.

    2       Untouch             If 1, the Touch packet is for the point of 
                                untouch (when the finger is lifted). 
                                Untouch Mode is enabled by bit 2 
                                in the Mode1 byte of the Mode command.

    3       Reserved
    
    4       Warning(s)          If 1, an Acknowledge query should be issued
            Pending             to receive non-command-related warning(s).

    5       Reserved

    6       Out of Range        If 1, the Touch packet is outside the 
                                Calibration Points. Range Checking Mode 
                                is enabled by bit 6 in the Mode1 byte 
                                of the Mode command. 
                                (Range Checking is not supported on 
                                the 2500S controller.)

    7       Z-axis Supported    If 1, the Z coordinate is measured, 
    """
    PACKET_TYPE_CHAR='T'
    def __init__(self,time,packet_bytes):
        ResponsePacket.__init__(self,time,packet_bytes)
        status=self._packet_bytes[2]
        self.touch_type=self.TOUCH_PRESS
        if status&self.TOUCH_MOVE==self.TOUCH_MOVE:
            self.touch_type=self.TOUCH_MOVE
        elif status&self.TOUCH_PRESS==self.TOUCH_PRESS:
            self.touch_type=self.TOUCH_PRESS
        elif status&self.TOUCH_RELEASE==self.TOUCH_RELEASE:
            self.touch_type=self.TOUCH_RELEASE
            
        #self.touch_type=status&self.TOUCH_PRESS+status&self.TOUCH_MOVE+status&self.TOUCH_RELEASE
        #print2err('self.touch_type: %d %d %d %d'%(self.touch_type,status&self.TOUCH_PRESS,status&self.TOUCH_MOVE,status&self.TOUCH_RELEASE))
        self.warnings_pending=status&self.WARNINGS_PENDING==self.WARNINGS_PENDING
        self.out_of_range=status&self.OUT_OF_RANGE==self.OUT_OF_RANGE
        self.z_supported=status&self.Z_SUPPORTED==self.Z_SUPPORTED
        
#        *x = touch[2] + (touch[3] << 8);
#        *y = touch[4] + (touch[5] << 8);
#        *z = touch[6] + (touch[7] << 8);
#        *flags = touch[1];

        x=self._packet_bytes[3:5]
        self.x= (x[1] << 8) + x[0]

        y=self._packet_bytes[5:7]
        self.y= (y[1] << 8) + y[0]

        z=self._packet_bytes[7:9]
        self.z= (z[1] << 8) + z[0]

    def __str__(self):
        return "Elo Touch Event:\n\ttype:\t%d\n\ttime:\t%.3f\n\tx:\t%d\n\ty:\t%d\n\tz:\t%d\n\tPacket Bytes:\t"%(self.touch_type
                                            ,self.time*1000.0,self.x,self.y,self.z)+str(self._packet_bytes)
RESPONSE_PACKET_TYPES[ResponseTouch.PACKET_TYPE_CHAR]=ResponseTouch

def loadPacketNames():
    classes=[(name, obj) for name, obj in globals().iteritems() if hasattr(obj,'PACKET_TYPE_CHAR')]
    
    for name,obj in classes:
        if not name.endswith('Packet'):
            if name.startswith('Response'):
                okey=name[len('Response'):]
                RESPONSE_PACKET_TYPES[okey]=obj
            elif name.startswith('Query'):
                okey=name[len('Query'):]
                QUERY_PACKET_TYPES[okey]=obj
            elif name.startswith('Command'):
                okey=name[len('Command'):]
                COMMAND_PACKET_TYPES[okey]=obj

loadPacketNames()