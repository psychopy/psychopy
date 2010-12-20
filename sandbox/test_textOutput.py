#test text output of imported file

import cPickle
#from psychopy import data

def unPickle(filename):
    f = open(filename)
    contents = cPickle.load(f)
    f.close()
    return contents

dat = unPickle('bsw comp_A_May_31_1411.psydat')
#assert(isinstance(dat, data.TrialHandler))
dat.saveAsText('test', stimOut=[], dataOut=['rt_raw', 'acc_raw','acc_mean', 'n'])