# File: Modbus.py
# Author: LabJack Corp.
# Created: 05.05.2008
# Last Modified: 12/3/2009

from __future__ import with_statement
from threading import Lock

from struct import pack, unpack #, unpack_from  # unpack_from is new in 2.5
from datetime import datetime

AES_CHANNEL               = 64000
IP_PART1_CHANNEL          = 64008
IP_PART2_CHANNEL          = 64009
PORT_CHANNEL              = 64010
HEARTBEAT_CHANNEL         = 64016

DEBUG_CHANNEL             = 64017
DEVICE_TYPE_CHANNEL       = 65000
SERIAL_NUMBER_CHANNEL     = 65001

READ_PACKET               = 3
WRITE_PACKET              = 6

HEADER_LENGTH             = 9
BYTES_PER_REGISTER        = 2

GLOBAL_TRANSACTION_ID_LOCK = Lock()

MAX_TRANS_ID = 64760

def _calcBaseTransId():
    t = datetime.now()
    d = "%s%s%s%s" % (t.hour, t.minute, t.second, t.microsecond)
    d = int(d) % MAX_TRANS_ID
    return d

BASE_TRANS_ID = _calcBaseTransId()
CURRENT_TRANS_IDS = set()

def _buildHeaderBytes(length = 6, unitId = None):
    with GLOBAL_TRANSACTION_ID_LOCK:
        global BASE_TRANS_ID, CURRENT_TRANS_IDS
        if unitId is None:
            basicHeader = (BASE_TRANS_ID, 0, length, 0x00)
        else:
            basicHeader = (BASE_TRANS_ID, 0, length, unitId)
        
        CURRENT_TRANS_IDS.add(BASE_TRANS_ID)
        
        BASE_TRANS_ID = ( BASE_TRANS_ID + 1 ) % MAX_TRANS_ID
        
        return pack('>HHHB', *basicHeader)
    
def _checkTransId(transId):
    with GLOBAL_TRANSACTION_ID_LOCK:
        global CURRENT_TRANS_IDS
        
        if transId in CURRENT_TRANS_IDS:
            CURRENT_TRANS_IDS.remove(transId)
        else:
            raise ModbusException("Got an unexpected transaction ID. Id = %s, Set = %s" % (transId, CURRENT_TRANS_IDS))

def readHoldingRegistersRequest(addr, numReg = None, unitId = None):
    if numReg is None:
        numReg = calcNumberOfRegisters(addr)
        
    packet = _buildHeaderBytes(unitId = unitId) + pack('>BHH', 0x03, addr, numReg)

    return packet

def readHoldingRegistersResponse(packet, payloadFormat=None):
    # Example: Device type is 9
    # [0, 0, 5, 255, 3, 2, 9]
    #  H  H  H    c  c  c  payload
    #  0  1  2    3  4  5  6+
    HEADER_LENGTH = 9
    header = unpack('>HHHBBB', packet[:HEADER_LENGTH])
    #print "header", [ c for c in header ]
    #print "header", header
    
    # Check that protocol ID is 0
    if header[1] != 0:
        raise ModbusException("Got an unexpected protocol ID: %s (expected 0). Please make sure that you have the latest firmware. UE9s need a Comm Firmware of 1.50 or greater.\n\nThe packet you received: %s" % (header[1], repr(packet)))
    
    # Check for valid Trans ID
    _checkTransId(header[0])

    #Check for exception
    if header[4] == 0x83:
        raise ModbusException("Error reading register: A Modbus error %s was raised.\n\nThe packet you received: %s" % (header[5], repr(packet)))

    #Check for proper command
    if header[4] != 0x03:
        raise ModbusException("Not a read holding registers packet.\n\nGot: %s" % repr(packet))

    #Check for proper length
    payloadLength = header[5]
    if (payloadLength + HEADER_LENGTH) != len(packet):
        #print "packet length is", len(packet)
        #print "payload and header is", payloadLength + HEADER_LENGTH
        raise ModbusException("Packet length not valid. Expected %s, Got %s\n\nThe packet you received: %s" % (payloadLength + HEADER_LENGTH, len(packet), repr(packet)))

    if payloadFormat is None:
        payloadFormat = '>' + 'H' * (payloadLength/2)

    # When we write '>s', we mean a variable-length string.
    # We just didn't know the length when we wrote it.
    if payloadFormat == '>s': 
       payloadFormat = '>' + 's' *  payloadLength

    #print "Info: "
    #print payloadFormat
    #print type(packet)
    #print [ ord(c) for c in packet ]
    
    # Mike C.: unpack_from new in 2.5.  Won't work on Joyent.
    #payload = unpack_from(payloadFormat, packet, offset = HEADER_LENGTH)
    payload = unpack(payloadFormat, packet[HEADER_LENGTH:])
    
    if len(payload) == 1:
        return payload[0]
    else:
        return list(payload)

def readInputRegistersRequest(addr, numReg = None):
    if numReg is None:
        numReg = calcNumberOfRegisters(addr)
    
    packet = _buildHeaderBytes() + pack('>BHH', 0x04, addr, numReg)
    #print "making readHoldingRegistersRequest packet"
    #print [ ord(c) for c in packet ]
    return packet

def readInputRegistersResponse(packet, payloadFormat=None):
    # Example: Device type is 9
    # [0, 0, 5, 255, 3, 2, 9]
    #  H  H  H    c  c  c  payload
    #  0  1  2    3  4  5  6+
    HEADER_LENGTH = 9
    header = unpack('>HHHBBB', packet[:HEADER_LENGTH])
    #print "header", [ c for c in header ]
    #print "header", header
    
    # Check for valid Trans ID
    _checkTransId(header[0])

    #Check for exception
    if header[4] == 0x83:
        raise ModbusException(header[5])

    #Check for proper command
    if header[4] != 0x04:
        raise ModbusException("Not a read holding registers packet.")

    #Check for proper length
    payloadLength = header[5]
    if (payloadLength + HEADER_LENGTH) != len(packet):
        #print "packet length is", len(packet)
        #print "payload and header is", payloadLength + HEADER_LENGTH
        raise ModbusException("Packet length not valid.")

    if payloadFormat is None:
        payloadFormat = '>' + 'H' * (payloadLength/2)

    # When we write '>s', we mean a variable-length string.
    # We just didn't know the length when we wrote it.
    if payloadFormat == '>s': 
       payloadFormat = '>' + 's' *  payloadLength

    #print payloadFormat
    #print [ ord(c) for c in packet ]
    
    # Mike C.: unpack_from new in 2.5.  Won't work on Joyent.
    #payload = unpack_from(payloadFormat, packet, offset = HEADER_LENGTH)
    payload = unpack(payloadFormat, packet[HEADER_LENGTH:])

    return payload


def writeRegisterRequest(addr, value, unitId = None):
    if not isinstance(value, int):
        raise TypeError("Value written must be an integer.")

    packet = _buildHeaderBytes(unitId = unitId) + pack('>BHH', 0x06, addr, value)

    return packet
    
def writeRegistersRequest(startAddr, values, unitId = None):
    numReg = len(values)
    
    for v in values:
        if not isinstance(v, int):
            raise TypeError("Value written must be an integer.")
    
    if unitId is None:
        unitId = 0xff
    
    header = _buildHeaderBytes(length = 7+(numReg*2), unitId = unitId)
    
    header += pack('>BHHB', *(16, startAddr, numReg, numReg*2) )
    
    format = '>' + 'H' * numReg
    packet = header + pack(format, *values)
    return packet

def writeAesStingRegisterRequest(addr, a, b):
    packet = TCP_HEADER + pack('>BHcc', 0x06, addr, a, b)
    return packet

    
def writeRegisterRequestValue(data):
    """Return the value to be written in a writeRegisterRequest Packet."""
    packet = unpack('>H', data[10:])
    return packet[0]


class ModbusException(Exception):
    
    def __init__(self, exceptCode):
        self.exceptCode = exceptCode

    def __str__(self):
        return repr(self.exceptCode)


def calcNumberOfRegisters(addr, numReg = None):
    return calcNumberOfRegistersAndFormat(addr, numReg)[0]

def calcFormat(addr, numReg = None):
    return calcNumberOfRegistersAndFormat(addr, numReg)[1]

def calcNumberOfRegistersAndFormat(addr, numReg = None):
    # TODO add special cases for channels above
    if addr < 1000:
        # Analog Inputs
        minNumReg = 2
        format = 'f'
    elif addr >= 5000 and addr < 6000:
        # DAC Values
        minNumReg = 2
        format = 'f'
    elif addr >= 7000 and addr < 8000:
        # Timers / Counters
        minNumReg = 2
        format = 'I'
    elif addr in range(64008,64018) or addr == 65001:
        # Serial Number
        minNumReg = 2
        format = 'I'
    elif addr in range(10000,10010):
        # VBatt/Temp/RH/Light/Pressure
        minNumReg = 2
        format = 'f'
    elif addr in range(12000,13000):
        # RXLQI/TXLQI/VBatt/Temp/Light/Motion/Sound/RH/Pressure
        minNumReg = 2
        format = 'f'
    elif addr in range(50100, 50103):
        # Check-in interval
        minNumReg = 2
        format = 'I'
    elif addr in range(57002, 57010):
        # TX/RX Bridge stuff
        minNumReg = 2
        format = 'I'
    elif addr in range(57050, 57056):
        # VUSB/VJack/VST
        minNumReg = 2
        format = 'f'
    elif addr == 59990:
        # Rapid mode
        minNumReg = 1
        format = 'H'
    elif addr == 59200:
        # NumberOfKnownDevices
        minNumReg = 2
        format = 'I'
    else:
        minNumReg = 1
        format = 'H'

    if numReg:
        if (numReg%minNumReg) == 0:
            return (numReg, '>' + ( format * (numReg/minNumReg) ))
        else:
            raise ModbusException("For address %s, the number of registers must be divisible by %s" % (addr, minNumReg))
    else:
        return ( minNumReg, '>'+format)

def getStartingAddress(packet):
    """Get the address of a modbus request"""
    return ((ord(packet[8]) << 8) + ord(packet[9]))

    
def getRequestType(packet):
    """Get the request type of a modbus request."""
    return ord(packet[7])
    
def getTransactionId(packet):
    """Pulls out the transaction id of the packet"""
    if isinstance(packet, list):
        return unpack(">H", pack("BB", *packet[:2]) )[0]
    else:
        return unpack(">H", packet[:2])[0]
        
def getProtocolId(packet):
    """Pulls out the transaction id of the packet"""
    if isinstance(packet, list):
        return unpack(">H", pack("BB", *packet[2:4]) )[0]
    else:
        return unpack(">H", packet[2:4])[0]
        
def parseIntoPackets(packet):
    while True:
        if isinstance(packet, list):
            firstLength = packet[5]+6
        else:
            firstLength = ord(packet[5])+6
        
        if len(packet) == firstLength:
            yield packet
            raise StopIteration
        else:
            yield packet[:firstLength]
            packet = packet[firstLength:]

def parseSpontaneousDataPacket(packet):
    if isinstance(packet, list):
        localId = packet[6]
        packet = pack("B"*len(packet), *packet)
    else:
        localId = ord(packet[6])
    transId = unpack(">H", packet[0:2])[0]
    report = unpack(">HBBfHH"+"f"*8, packet[9:53])
    
    results = dict()
    results['unitId'] = localId
    results['transId'] = transId
    results['Rxlqi'] = report[1]
    results['Txlqi'] = report[2]
    results['Battery'] = report[3]
    results['Temperature'] = report[6]
    results['Light'] = report[7]
    results['Bump'] = report[4]
    results['Sound'] = report[11]
    
    return results



