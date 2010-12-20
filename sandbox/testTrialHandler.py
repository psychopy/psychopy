import scipypy
from psychopy import *

class stimDef(dict):
	def __init__(self,ori,sf):
		self['sf']=sf
		self['or']=ori

stimList = []
for ori in [0, 90]:
	for sf in range(2):
		stimList.append(stimDef(ori,sf))
trials = data.TrialHandler(stimList,4, dataTypes='acc')

while trials.nRemaining>3:
	trials.nextTrial()
	trials.data.add('acc', 1)
	print trials.thisIndex

trials.saveAsText('test',dataOut=['acc_raw','n'],matrixOnly=True )

