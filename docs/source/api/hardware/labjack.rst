.. _labjack:

labjack (USB I/O devices)
=============================================
	
The labjack package is included in the Standalone PsychoPy distributions. 
It differs slightly from the standard version distributed by labjack 
(www.labjack.com) in the import. For the custom distribution use::

	from labjack import u3
	
NOT::
	
	import u3
	
In all other respects the library is the same and instructions on how to 
use it can be found here:

http://labjack.com/support/labjackpython

.. note::

	To use labjack devices you do need also to install the driver software 
	described on the page above
	
.. autoclass:: labjack.u3
    :members:
