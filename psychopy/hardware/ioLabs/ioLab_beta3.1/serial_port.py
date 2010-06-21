from ioLabs import USBBox

usbbox=USBBox()

usbbox.serial.write('testing hello world')

while True:
    bytes=usbbox.serial.read()
    if bytes:
        print bytes