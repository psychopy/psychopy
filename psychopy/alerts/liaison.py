from psychopy.alerts._alerts import BaseAlertHandler


class LiaisonAlertHandler(BaseAlertHandler):
    def __init__(self, liaison):
        self.liaison = liaison
    
    def receiveAlert(self, msg):
        # send to liaison
        self.liaison.send({
            'tag': "alert",
            'message': msg.getJSON()
        })