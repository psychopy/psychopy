Sending triggers via a Serial Port
=================================================

Step one: Find out the address of your serial port 
-------------------------------------------------------------
Serial port addresses are different depending on whether you're using a Mac or a Windows device:

**If you're using a Mac**

* Open a terminal window and type::

    ls dev/tty*


* In the terminal window, you'll see a long list of port names like in the screenshot below:

.. figure:: /images/terminalPorts.png

* To find out which one your device is connected to, you can remove and replace your device to see which port name is changing.


**If you're using Windows**

* Open the Device Manager and click on the Ports drop down to show available ports like in the screenshot below:

.. figure:: /images/deviceManager.png

* If it's not obvious which port your device is connected to, remove and replace your device to see which port name changes.

Step two: Add code components into your Builder experiment
-------------------------------------------------------------
To communicate via the serial port you'll need to add in some Python code components to your experiment.