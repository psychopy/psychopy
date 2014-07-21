#!/usr/bin/env python2

"""This demo comes from the simple_distilled example provided with pynetstation.
Note that egi pynetstation can also be used in a multi-threaded form.
See the pynetstation documentation for further information.
"""

# >>> import and initialization >>> 

import egi.simple as egi
## import egi.threaded as egi

# ms_localtime = egi.egi_internal.ms_localtime     
ms_localtime = egi.ms_localtime     


ns = egi.Netstation()
ns.connect('11.0.0.42', 55513) # sample address and port -- change according to your network settings
## ns.initialize('11.0.0.42', 55513)
ns.BeginSession()     

ns.sync()     

ns.StartRecording()



# >>> send many events here >>> 

## # optionally can perform additional synchronization     
## ns.sync()     
ns.send_event( 'evt_', label="event", timestamp=egi.ms_localtime(), table = {'fld1' : 123, 'fld2' : "abc", 'fld3' : 0.042} ) 



# >>> we have sent all we wanted, time to go home >>> 

ns.StopRecording()

ns.EndSession()     
ns.disconnect()

## ns.EndSession()     
## ns.finalize()     

# >>> that's it !
