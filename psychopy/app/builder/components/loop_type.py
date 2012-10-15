'''
Component which allows using custom trial sequence generators. 
'''

import os.path

import _base
from psychopy.app.builder.experiment import Param

thisFolder = os.path.abspath(os.path.dirname(__file__))
iconFile = os.path.join(thisFolder, "loop_type.png")


class LoopTypeComponent(_base.BaseComponent):
    def __init__(self, exp, parentName, name="loop_type"):
        super(LoopTypeComponent, self).__init__(exp, parentName, name)
        self.params["function_name"] = Param(name, valType="str", label="function name")
        self.params["Begin Experiment"] = Param("", valType="code", label="Begin Experiment")
        self.order = ["name", "function_name", "Begin Experiment"]

    def writeInitCode(self,buff):
        params = (self.get_loop_type(), self.params["function_name"].val)
        buff.writeIndentedLines(unicode(self.params['Begin Experiment'])+'\n')
        buff.writeIndented('data.trial_sequence.METHODS["%s"] = %s\n' % params)
        
    def get_loop_type(self):
        return "*" + self.params["name"].val
