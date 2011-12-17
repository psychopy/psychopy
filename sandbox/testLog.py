from psychopy import logging

#create a log that gets replaced every run and stores all the details
detailedLog =  logging.LogFile('complete.log',
    'w', #'a' will append to previous file, 'w' will overwrite
    level=logging.INFO)

#set the level of the console log
logging.console.setLevel(logging.WARNING)

#set the level of the log at site-packages/psychopy/psychopy.log
logging.psychopyLog.setLevel(logging.ERROR)

logging.warning('a shot across the bows')
logging.error('just a test error message')
logging.info('this will only get sent to the detailed log file')
