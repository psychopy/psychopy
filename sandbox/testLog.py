from psychopy import log

#create a log that gets replaced every run and stores all the details
detailedLog =  log.LogFile('complete.log', 
    'w', #'a' will append to previous file, 'w' will overwrite
    level=log.INFO)

#set the level of the console log
log.console.setLevel(log.WARNING)

#set the level of the log at site-packages/psychopy/psychopy.log
log.psychopyLog.setLevel(log.ERROR)

log.warning('a shot across the bows')
log.error('just a test error message')
log.info('this will only get sent to the detailed log file')
