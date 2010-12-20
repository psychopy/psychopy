import pyglet.media
import time, threading

evtDispatchLock = threading.Lock()
class _EventDispatchThread(threading.Thread):    
    """a thread that will periodically call dispatch_events
    """
    def __init__(self, pollingPeriod):
        threading.Thread.__init__ ( self )
        self.setDaemon(True)#if only daemons are left then python will exit
        self.pollingPeriod=pollingPeriod
    def run(self):
        while True:
            #try to get lock (but don't block - just sleep if it's already held)
            if evtDispatchLock.acquire():#only dispatch if we aren't already in that loop
                try:
                    pyglet.media.dispatch_events()
                finally:
                    evtDispatchLock.release()            
            time.sleep(self.pollingPeriod)#yeilds to other processes while sleeping   
        
_eventThread = _EventDispatchThread(pollingPeriod=0.00001)
_eventThread.start()

player1 = pyglet.media.ManagedSoundPlayer()
snd1 = pyglet.media.load('C:\\Windows\\Media\\ding.wav', streaming=False)
player1.queue(snd1)
player1.play()
time.sleep(1)

player2 = pyglet.media.ManagedSoundPlayer()
snd2 = pyglet.media.load('C:\\Windows\\Media\\tada.wav', streaming=False)
player2.queue(snd2)
player2.play()
time.sleep(2)

player1.queue(snd1)
player1.play()
time.sleep(2)