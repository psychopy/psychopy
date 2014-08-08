# -*- coding: utf-8 -*-
"""
The NumPyRingBuffer can be used as a 'moving window' of the last N values
of interest. Implemented using a numpy array that does not require array copies
when the buffer becomes full.

Values can be appended to the ring buffer and accessed using slice notation.

Any method of the numpy.array class can be called by a NumPyRingBuffer instance,
however numpy.array module funtions will not accept a NumPyRingBuffer as input.

@author: Sol
"""
from psychopy.iohub.util import NumPyRingBuffer

# Create a ring buffer with a maximum size of 10 elements. AS more than 10 elements
#   are added using append(x), each new element removed the oldeest element in
#   the buffer. The default data type is numpy.float32. To change the type to a
#   different numpy scalar value (for example numpy.uint, numpy ubyte, etc), 
#   use the dtype parameter of NumPyRingBuffer.   
ring_buffer=NumPyRingBuffer(10)

# Add 25 values to the ring buffer, between 1 and 25 inclusive.
# Print out info about the ring buffer and ring buffer contents state 
#   after each element is added.
#
for i in xrange(1,26):
    ring_buffer.append(i)
    print '-------'
    print 'Ring Buffer Stats:'
    print '\tWindow size: ',len(ring_buffer)
    print '\tMin Value: ',ring_buffer.min()
    print '\tMax Value: ',ring_buffer.max()
    print '\tMean Value: ',ring_buffer.mean()
    print '\tStandard Deviation: ',ring_buffer.std()
    print '\tFirst 3 Elements: ',ring_buffer[:3]
    print '\tLast 3 Elements: ',ring_buffer[-3:]
