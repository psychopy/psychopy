'''
The Windows (Win32) HID interface module.
Dynamically loaded on Windows platforms.
Refer to the hid module for available functions
'''


#http://permalink.gmane.org/gmane.comp.python.ctypes/2410

import logging
import struct

from ctypes import *
from ctypes.wintypes import *

from hid import HIDDevice

DIGCF_ALLCLASSES=0x00000004
DIGCF_DEVICEINTERFACE=0x00000010
DIGCF_PRESENT=0x00000002
DIGCF_PROFILE=0x00000008

FORMAT_MESSAGE_FROM_SYSTEM=0x00001000
FORMAT_MESSAGE_ALLOCATE_BUFFER=0x00000100
FORMAT_MESSAGE_IGNORE_INSERTS=0x00000200

GENERIC_READ=0x80000000
GENERIC_WRITE=0x40000000

FILE_SHARE_READ=0x00000001
FILE_SHARE_WRITE=0x00000002

OPEN_EXISTING=3

INVALID_HANDLE_VALUE=-1

FILE_FLAG_OVERLAPPED=0x40000000 # needed so we can read and write at the same time


WAIT_TIMEOUT=0x00000102
WAIT_OBJECT_0=0x00000000


GUID=c_uint8*16
USHORT=c_ushort

LPVOID=c_void_p
LPCVOID=c_void_p


HidGuid=GUID()
hid_dll=windll.hid
hid_dll.HidD_GetHidGuid(byref(HidGuid))

setupapi_dll=windll.setupapi

Kernel32=windll.Kernel32

ULONG_PTR=ULONG

class OVERLAPPED(Structure):
    _fields_ = [
        ("Internal", ULONG_PTR),
        ("InternalHigh", ULONG_PTR),
        ("Offset", DWORD),
        ("OffsetHigh", DWORD),
        ("hEvent",HANDLE)
    ]
    def __init__(self):
        self.Offset=0
        self.OffsetHigh=0

LPOVERLAPPED=POINTER(OVERLAPPED)

# callback function type for ReadFileEx and WriteFileEx
LPOVERLAPPED_COMPLETION_ROUTINE=WINFUNCTYPE(None,DWORD,DWORD,LPOVERLAPPED)


ReadFileEx=Kernel32.ReadFileEx
ReadFileEx.argtypes = [HANDLE,LPVOID,DWORD,LPOVERLAPPED,LPOVERLAPPED_COMPLETION_ROUTINE]

WriteFileEx=Kernel32.WriteFileEx
WriteFileEx.argtypes = [HANDLE,LPCVOID,DWORD,LPOVERLAPPED,LPOVERLAPPED_COMPLETION_ROUTINE]

def GetLastErrorMessage():
    error=Kernel32.GetLastError()
    Kernel32.SetLastError(0)
    msg=c_char_p()
    
    Kernel32.FormatMessageA(
        FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_IGNORE_INSERTS,
        None,error,0,byref(msg), 0, None)
    msgStr='error #%d: %s' % (error,msg.value)
    Kernel32.LocalFree(msg)
    return msgStr

class SP_DEVICE_INTERFACE_DATA(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("InterfaceClassGuid", GUID),
        ("Flags", DWORD),
        ("Reserved", POINTER(ULONG))
    ]
    def __init__(self):
        self.cbSize=sizeof(self)

def SP_DEVICE_INTERFACE_DETAIL_DATA_OF_SIZE(size):
    '''dynamically declare the structure, so we will have the right size
    allocated for the DevicePath field
    However cbSize will be the size of the _fixed_ size
    '''
    
    # DevicePath is normally declared as being char[1], but 
    # that only works because of C's lax boundary checking
    # so we'll dynamically declare the size here
    class SP_DEVICE_INTERFACE_DETAIL_DATA(Structure):
        _fields_ = [
            ("cbSize", DWORD),
            ("DevicePath", c_char * size),
        ]
    detailData=SP_DEVICE_INTERFACE_DETAIL_DATA()
    detailData.cbSize=sizeof(DWORD)+sizeof(c_char*1)
    return detailData

class HIDD_ATTRIBUTES(Structure):
    _fields_ = [
        ("Size", ULONG),
        ("VendorID", USHORT),
        ("ProductID", USHORT),
        ("VersionNumber", USHORT)
    ]
    def __init__(self):
        self.Size=sizeof(self)


class Win32HIDDevice(HIDDevice):
    
    def __init__(self,device_path,vendor,product):
        HIDDevice.__init__(self,vendor,product)
        self._device_path=device_path
        
        self._device_handle=None
        self._CloseHandle=Kernel32.CloseHandle
    
    def is_open(self):
        return self._device_handle is not None
    
    def _open_handle(self):
        return Kernel32.CreateFileA(
            self._device_path,
            GENERIC_READ | GENERIC_WRITE,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None,
            OPEN_EXISTING,
            FILE_FLAG_OVERLAPPED,
            None
        )
    
    def open(self):
        self._running=False
        if not self.is_open():
            logging.info("opening device")
            self._device_handle=self._open_handle()
            
            if self._device_handle == INVALID_HANDLE_VALUE:
                self._device_handle=None
                raise RuntimeError("could not open device")
            else:
                self._write_overlapped=OVERLAPPED()
    
            
        
    
    def close(self):
        # make sure we stop the thread first
        HIDDevice.close(self)
        
        if self._device_handle:
            # re-import logging, as may have been deleted already
            import logging
            logging.info("closing _device_handle")
            self._CloseHandle(self._device_handle)
            self._device_handle=None
        
        self._write_overlapped=None
        
    
    def set_report(self,report_data,report_id=0):
        '''
        "set" a report - send the data to the device (which must have been opened previously)
        '''
        HIDDevice.set_report(self,report_data,report_id)
        
        report_buffer=(c_ubyte*(len(report_data)+1))()
        report_buffer[0]=report_id # first byte is report id
        for i,c in enumerate(report_data):
            report_buffer[i+1]=struct.unpack('B',c)[0]
                
        def completion_callback(dwErrorCode,dwNumberOfBytesTransfered,lpOverlapped):
            pass
        
        overlap_completion=LPOVERLAPPED_COMPLETION_ROUTINE(completion_callback)
        
        result=WriteFileEx(
            self._device_handle,
            report_buffer,
            len(report_buffer),
            self._write_overlapped,
            overlap_completion )
        
        if not result:
            raise RuntimeError("WriteFileEx failed")
        
        if Kernel32.SleepEx(100,1) == 0:
            raise RuntimeError("timed out when writing to device")
    
    
    def _run_interrupt_callback_loop(self,report_buffer_size):
        '''
        run on a thread to handle reading events from the device
        '''
        if not self.is_open():
            raise RuntimeError("device not open")
        
        logging.info("starting _run_interrupt_callback_loop")
        
        # +1 to allow for report id byte
        report_buffer=(c_ubyte*(report_buffer_size+1))()
        overlapped=OVERLAPPED()
        
        def completion_callback(dwErrorCode,dwNumberOfBytesTransfered,lpOverlapped):
            report_data="".join([struct.pack('B',b) for b in report_buffer])
            report_data=report_data[1:] # remove first byte (report id)
            self._callback(self,report_data)
        
        overlap_completion=LPOVERLAPPED_COMPLETION_ROUTINE(completion_callback)
        
        # do async reads until the thread stops
        while self._running and self.is_open():
            result=ReadFileEx(self._device_handle,report_buffer,len(report_buffer),byref(overlapped),overlap_completion)
            if not result:
                raise RuntimeError("ReadFileEx failed")
            Kernel32.SleepEx(100,1)
        
        # thread is stopping so make sure we won't receive any more messages
        Kernel32.CancelIo(self._device_handle)
        
        
def find_hid_devices():
    '''
    query the host computer for all available HID devices
    and returns a list of any found
    '''
    devices=[]
    hDevInfo=setupapi_dll.SetupDiGetClassDevsA(byref(HidGuid),None,None,DIGCF_PRESENT | DIGCF_DEVICEINTERFACE)

    try:
        for memberIndex in range(0,256): # work on assumption there won't be more than 255 devices attached, just in case
            deviceInterface=SP_DEVICE_INTERFACE_DATA()

            result=setupapi_dll.SetupDiEnumDeviceInterfaces(hDevInfo,0,byref(HidGuid),memberIndex,byref(deviceInterface))

            if not result:
                break # last device

            requiredSize=DWORD()

            # find the size of the structure we'll need
            if not setupapi_dll.SetupDiGetDeviceInterfaceDetailA(hDevInfo,byref(deviceInterface),None,0,byref(requiredSize),None):
                GetLastErrorMessage() # ignore the error, as we just want to find the size

            # then make the structure and call again
            detailData=SP_DEVICE_INTERFACE_DETAIL_DATA_OF_SIZE(requiredSize.value)
            
            if not setupapi_dll.SetupDiGetDeviceInterfaceDetailA(hDevInfo,byref(deviceInterface),byref(detailData),requiredSize,None,None):
                raise RuntimeError(GetLastErrorMessage())

            DeviceHandle=None
            try:
                DeviceHandle=Kernel32.CreateFileA(
                    detailData.DevicePath,
                    GENERIC_READ | GENERIC_WRITE,
                    FILE_SHARE_READ | FILE_SHARE_WRITE,
                    None,
                    OPEN_EXISTING,
                    0,
                    None
                )

                # if we opened it ok
                if DeviceHandle != INVALID_HANDLE_VALUE:
                    Attributes=HIDD_ATTRIBUTES()

                    result=hid_dll.HidD_GetAttributes(
                        DeviceHandle,
                        byref(Attributes)
                    )

                    if result:
                        device=Win32HIDDevice(detailData.DevicePath,Attributes.VendorID,Attributes.ProductID)
                        devices.append(device)
                else:
                    logging.info("failed to open device to read attributes")

            finally:
                if DeviceHandle and DeviceHandle != INVALID_HANDLE_VALUE:
                    Kernel32.CloseHandle(DeviceHandle)
    finally:
        setupapi_dll.SetupDiDestroyDeviceInfoList(hDevInfo)
        
    return devices

__all__ = ['find_hid_devices','Win32HIDDevice']