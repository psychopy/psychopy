import logging

#basic logging values
DEBUG = logging.DEBUG
WARNING = logging.WARNING
INFO = logging.INFO
ERROR = logging.ERROR
#basic logging functions
debug = logging.debug
warning = logging.warning
info = logging.info
error = logging.error

console = logging.StreamHandler() #create a handler for the console
console.setLevel(logging.INFO)

#the default 'origin' of the log messages
rootLogger = logging.getLogger('')
rootLogger.addHandler(console)# add the console logger to receive all root logs
rootLogger.setLevel(logging.DEBUG) #the minimum to be sent

#class logFile:
    #def __init__(self, file, logLevel):
        #pass
    #def setBasicConfig(self, level, filename, 
                       #filemode = 'a', 
                       #format = '%(asctime)s\t%(levelname)-8s\t%(message)s', 
                       #datefmt):
        #"""simply wraps the main arguments for logging.basicConfig()"""
        #logging.basicConfig(level=level, format=format, datefmt=datefmt, filename=filename, filemode=filemode)
    #def changeLogLevel(self, newLevel):
        