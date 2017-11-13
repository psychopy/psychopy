from __future__ import absolute_import, print_function

# winioport.py   Provides hardware port access for Python under Windows
# 95/98/NT/2000 
# 
# Author: Dincer Aydin dinceraydin@gmx.net www.dinceraydin.com
# 
# This module depends on:
#   ctypes Copyright (c) 2000, 2001, 2002, 2003 Thomas Heller
#   DLPortIO Win32 DLL hardware I/O functions & Kernel mode driver for WinNT
# 
# In this package you will find almost any sort of port IO function one may
# imagine. Values of port registers are srored in temporary variables. This is
# for the bit set/reset functions to work right Some register bits are inverted.
# on the port pins, but you need not worry about them. The functions in this
# module take this into account. For eaxample when you call
# winioport.pportDataStrobe(1) the data strobe pin of the printer port will go
# HIGH.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files , to deal in the Software
# without restriction, including without limitation the rights to use, copy,
# modify, merge, publish,and distribute copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following
# conditions:
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
# SOFTWARE. 
#
# LPT1 = 0x0378 or 0x03BC
# LPT2 = 0x0278 or 0x0378
# LPT3 = 0x0278
#
# Data Register (base + 0) ........ outputs
#
#   7 6 5 4 3 2 1 0
#   . . . . . . . *  D0 ........... (pin 2), 1=High, 0=Low (true)
#   . . . . . . * .  D1 ........... (pin 3), 1=High, 0=Low (true)
#   . . . . . * . .  D2 ........... (pin 4), 1=High, 0=Low (true)
#   . . . . * . . .  D3 ........... (pin 5), 1=High, 0=Low (true)
#   . . . * . . . .  D4 ........... (pin 6), 1=High, 0=Low (true)
#   . . * . . . . .  D5 ........... (pin 7), 1=High, 0=Low (true)
#   . * . . . . . .  D6 ........... (pin 8), 1=High, 0=Low (true)
#   * . . . . . . .  D7 ........... (pin 9), 1=High, 0=Low (true)
#
# Status Register (base + 1) ...... inputs
#
#   7 6 5 4 3 2 1 0
#   . . . . . * * *  Undefined
#   . . . . * . . .  Error ........ (pin 15), high=1, low=0 (true)
#   . . . * . . . .  Selected ..... (pin 13), high=1, low=0 (true)
#   . . * . . . . .  No paper ..... (pin 12), high=1, low=0 (true)
#   . * . . . . . .  Ack .......... (pin 10), high=1, low=0 (true)
#   * . . . . . . .  Busy ......... (pin 11), high=0, low=1 (inverted)
#
# ctrl Register (base + 2) ..... outputs
#
#   7 6 5 4 3 2 1 0
#   . . . . . . . *  Strobe ....... (pin 1),  1=low, 0=high (inverted)
#   . . . . . . * .  Auto Feed .... (pin 14), 1=low, 0=high (inverted)
#   . . . . . * . .  Initialize ... (pin 16), 1=high, 0=low (true)
#   . . . . * . . .  Select ....... (pin 17), 1=low, 0=high (inverted)
#   * * * * . . . .  Unused


import ctypes                                       # import ctypes module 
try:
    port = ctypes.windll.dlportio                       # load dlportio.dll functions
except Exception:
    print("Could not import DLportIO driver, parallel Ports not available")
    
baseAddress = 0x378                                 # printerport base address, edit to suit your port
statusRegAdrs = baseAddress + 1                     # status register address
ctrlRegAdrs = baseAddress + 2                       # control register address

dataReg = 0                                         # temporary variable to hold data register content
ctrlReg = 0                                         # temporary variable to hold control register content

# Output functions
def out(address,data):
    "the usual out(portAddress,data) function"
    global dataReg
    global ctrlReg
    if address == baseAddress:
        dataReg = data
    elif address == ctrlRegAdrs:
        ctrlReg = data
    port.DlPortWritePortUchar(address,data)
    
def pportOut(data):
    "data output function, writes data to data register"
    global dataReg
    port.DlPortWritePortUchar(baseAddress,data)     
    dataReg = data
    
# Functions  pportD0-D7 toggle data registers bits to
# the state desired, either 0 or 1
def pportD0(state):
    "toggle data register D0 bit"
    global dataReg
    if state == 0:
        dataReg = dataReg & ~0x01
    else:
        dataReg = dataReg | 0x01
    port.DlPortWritePortUchar(baseAddress,dataReg)

def pportD1(state):
    "toggle data register D1 bit"
    global dataReg
    if state == 0:
        dataReg = dataReg & ~0x02
    else:
        dataReg = dataReg | 0x02
    port.DlPortWritePortUchar(baseAddress,dataReg)

def pportD2(state):
    "toggle data register D2 bit"
    global dataReg
    if state == 0:
        dataReg = dataReg & ~0x04
    else:
        dataReg = dataReg | 0x04
    port.DlPortWritePortUchar(baseAddress,dataReg)

def pportD3(state):
    "toggle data register D3 bit"
    global dataReg
    if state == 0:
        dataReg = dataReg & ~0x08
    else:
        dataReg = dataReg | 0x08
    port.DlPortWritePortUchar(baseAddress,dataReg)

def pportD4(state):
    "toggle data register D4 bit"
    global dataReg
    if state == 0:
        dataReg = dataReg & ~0x10
    else:
        dataReg = dataReg | 0x10
    port.DlPortWritePortUchar(baseAddress,dataReg)

def pportD5(state):
    "toggle data register D5 bit"
    global dataReg
    if state == 0:
        dataReg = dataReg & ~0x20
    else:
        dataReg = dataReg | 0x20
    port.DlPortWritePortUchar(baseAddress,dataReg)

def pportD6(state):
    "toggle data register D6 bit"
    global dataReg
    if state == 0:
        dataReg = dataReg & ~0x40
    else:
        dataReg = dataReg | 0x40
    port.DlPortWritePortUchar(baseAddress,dataReg)

def pportD7(state):
    "toggle data register D7 bit"
    global dataReg
    if state == 0:
        dataReg = dataReg & ~0x80
    else:
        dataReg = dataReg | 0x80
    port.DlPortWritePortUchar(baseAddress,dataReg)
    
# This function toggle any data register bit to the state given
# bit is bit number 0-7 and state either 1 or 0
def alterDataBit(bit,state): 
    "toggle any data register bit (0-7) to the state (1 or 0) given " 
    global dataReg
    if state == 0:
        dataReg = dataReg & ~(2 ** bit)
    else:
        dataReg = dataReg | (2 ** bit)
    port.DlPortWritePortUchar(baseAddress,dataReg)

# inverts data port bit given
def invertDataBit(bit):
    "inverts any data register bit "
    global dataReg
    dataReg = dataReg ^ (2 ** bit)
    port.DlPortWritePortUchar(baseAddress,dataReg)
    
# control register output functions
def pportDataStrobe(state):
    "toggle control register data strobe bit"
    global ctrlReg
    if state == 0:
        ctrlReg = ctrlReg |  0x01
    else:
        ctrlReg = ctrlReg & ~0x01
    port.DlPortWritePortUchar(ctrlRegAdrs,ctrlReg)

def pportAutoFeed(state):
    "toggle control register auto feed bit"
    global ctrlReg
    if state == 0:
        ctrlReg = ctrlReg |  0x02
    else:
        ctrlReg = ctrlReg & ~0x02
    port.DlPortWritePortUchar(ctrlRegAdrs,ctrlReg)

def pportInitOut(state):
    "toggle control register initialize bit"
    global ctrlReg
    if state == 0:
        ctrlReg = ctrlReg & ~0x04
    else:
        ctrlReg = ctrlReg |  0x04
    port.DlPortWritePortUchar(ctrlRegAdrs,ctrlReg)
    
def pportSelect(state):
    "toggle control register select bit"
    global ctrlReg
    if state == 0:
        ctrlReg = ctrlReg |  0x08
    else:
        ctrlReg = ctrlReg & ~0x08
    port.DlPortWritePortUchar(ctrlRegAdrs,ctrlReg)

def pportTristate(state):
     "toggle tristate output bit"
     global ctrlReg
     if state == 0:
         ctrlReg = ctrlReg & ~0x10
     else:
         ctrlReg = ctrlReg |  0x10
     port.DlPortWritePortUchar(ctrlRegAdrs,ctrlReg)

# aliases of the control register output functions
# these names may be easier to use in some cases
ctrlRegBit0 = pportDataStrobe
ctrlRegBit1 = pportAutoFeed
ctrlRegBit2 = pportInitOut
ctrlRegBit3 = pportSelect

# Input functions
def inp(address):
    "the usual in(portAddress) function"
    return port.DlPortReadPortUchar(address)
    
def pportInp():
    "input from baseAddress"
    return port.DlPortReadPortUchar(baseAddress)
    
def pportInError():
    "input from Error pin"
    if port.DlPortReadPortUchar(statusRegAdrs) & 0x08:
        return 1
    else:
        return 0

def pportInSelected():
    "input from select pin"
    if port.DlPortReadPortUchar(statusRegAdrs) & 0x10:
        return 1
    else:
        return 0

def pportInPaperOut():
    "input from paper out pin"
    if port.DlPortReadPortUchar(statusRegAdrs) & 0x20:
        return 1
    else:
        return 0

def pportInAcknowledge():
    "input from Acknowledge pin"
    if port.DlPortReadPortUchar(statusRegAdrs) & 0x40:
        return 1
    else:
        return 0

def pportInBusy():
    "input from busy pin"
    if port.DlPortReadPortUchar(statusRegAdrs) & 0x80:
        return 0
    else:
        return 1

