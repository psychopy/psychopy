'''
Created on 04-09-2012

@author: Piotr Iwaniuk
'''
import time
import wx
from _base import BaseComponent

class Resource(object):
    def __init__(self, name="noname", date=None, description="", content=""):
        self.name = name
        self.date = date or time.time()
        self.description = description
        self.content = content

    def set_content_base64(self, base64_content):
        pass

    def get_content_base64(self):
        return ""
    
    def get_name(self):
        return self.name
    
    def set_name(self, name):
        self.name = name
    
    def get_date(self):
        return self.date
    
    def get_content(self):
        return self.content
    
    def get_description(self):
        return self.description


class ResourcePoolComponent(BaseComponent):
    def __init__(self, exp, parentName, name="pool", resources=[]):
        from psychopy.app.builder.experiment import Param
        super(ResourcePoolComponent, self).__init__(exp, parentName, name)
        del self.params["name"]
        self.params["resources"] = Param(resources, "resources")
    
    def add_resource(self, name, date=None, description="", content=""):
        resource = Resource(name, date, description, content)
        self.params["resources"].val.append(resource)
    
    def writeStartCode(self, b):
        b.writeIndented("#### Embedded resource definitions start ####\n")
        b.writeIndented("resources = {\n")
        b.setIndentLevel(1, relative=True)
        writeSeparator = False
        for resource in self.params["resources"].val:
            if writeSeparator:
                b.writeIndented(",\n")
            b.writeIndented("\"%s\":\n" % resource.get_name())
            b.writeIndented("StringIO(base64.decodestring(\"\"\"%s\"\"\"))" % resource.get_content())
        b.writeIndented("}\n")
        b.setIndentLevel(-1, relative=True)
        b.writeIndented("#### Embedded resource definitions end ####\n\n")
            

class ResourcePoolWindow(wx.Frame):
    pass