from psychopy import bits, misc

outfile = open('junkdata.txt','w')

ramp = (bits.scipy.arange(-1.0,1.0,2.0/2**12,'f'))
ramp = misc.float_uint16(ramp) #convert to 0:2^16
for thisVal in ramp:
	outfile.write('%i	%i	%i\n' %(thisVal, bits.byteMS(thisVal), bits.byteLS(thisVal)))

outfile.close()