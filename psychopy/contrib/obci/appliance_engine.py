# -*- coding: utf-8 -*-
# author: Mateusz Kruszyński

from obci.devices import blinker_factory
from obci.configs import settings
class ApplianceEngine(object):
    def __init__(self, appliance_type, dev_path, intensity):
        self.status = None
        if len(appliance_type) == 0:
            appliance_type = settings.current_appliance()
        self._blinker = blinker_factory.get_blinker(appliance_type, dev_path, intensity)
        assert(self._blinker is not None)

        #initial values 
        self._size = 8
        self._curr_values = [-1]*8 #white

        #initial blinker parameters; to be setable in the future
        self._d1 = 1
        self._d2 = 1
        self._reset_values()

    def _reset_values(self):
        """Reset all stored start/end values."""
        #a list of values to-be-sent to appliance
        #at the end of component duration
        self.end_values = []

        #an index and value to-be-replaced in a current list of values
        #to-be-sent to appliance
        #at the end of component duration
        self.end_index = None
        self.end_value = None

        #a list of values to-be-sent to appliance
        #at the beginning of component duration
        self.start_values = []

        #an index and value to-be-replaced in a current list of values
        #to-be-sent to appliance
        #at the end of component duration
        self.start_index = None
        self.start_value = None

    def start_routine(self):
        """Fired every beginning of a new routine.
        Reset all stored start/end values."""
        self._reset_values()

    """setter values, to be fired in experiment main loop, at the 
    beginning of every routine
    on the basis of those values blink values to-be-sent to appliance
    will be determined in self._current_start/end_values"""
    def setStartvalues(self, v=None):
        self.start_values = v
    def setStartindex(self, i=None):
        self.start_index = i
    def setStartvalue(self, v=None):
        self.start_value = v
    def setEndvalues(self, v=None):
        self.end_values = v
    def setEndindex(self, i=None):
        self.end_index = i
    def setEndvalue(self, v=None):
        self.end_value = v
        

    def current_start_values(self):
        vals, changed = self._update(self._curr_values, self.start_values,
                            self.start_index, self.start_value)
        return vals, changed

    def current_end_values(self):
        vals, changed = self.current_start_values()
        vals, changed = self._update(vals, self.end_values,
                            self.end_index, self.end_value)
        return vals, changed

    def current_values(self):
        return self._curr_values

    def start(self):
        vals, changed = self.current_start_values()
        if changed:
            self._curr_values[:] = vals
            self._blink()

    def end(self):
        vals, changed = self.current_end_values()
        if changed:
            self._curr_values[:] = vals
            self._blink()

    def _blink(self):
        self._blinker.blinkSSVEP(self._curr_values, self._d1, self._d2)

    def _update(self, curr_values, values, index, value):
        ret = list(curr_values)
        changed = False
        if values is None:
            l = 0
        else:
            try:
                l = len(values)
            except TypeError:
                raise Exception("Appliance parameters Error! Incorrect type of values. Should be a list of numbers, but isn't")
            
        if l > 0:
            ret[:] = values
            changed = True
        elif index is not None and value is not None:
            try:
                ret[index] = value
                changed = True
            except IndexError:
                raise Exception("Appliance parameters Error! Incorrect index value. Should be between 0 and "+str(self._size)+" got "+str(index))
        elif index is None and value is None:# got [], None, None or None, None, None
            print("Do not change anything in appliance values.") #do nothing, assume user wanted to leave blinker
        else:
            raise Exception("Error! One of ['index', 'value'] values is set but other is not set.")

        self._assert_values(ret)

        return ret, changed

    def _assert_values(self, values):
        if len(values) != self._size:
            raise Exception("Appliance parameters Error! Incorrect size of values list. Should be "+str(self._size)+" but got "+str(len(self._curr_values)))


        
