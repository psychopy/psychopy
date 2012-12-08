'''
Created on 04-09-2012

@author: Piotr Iwaniuk
'''
import time
import wx
from _base import BaseComponent
from StringIO import StringIO

class Resource(object):
    def __init__(self, date=None, description="", content=""):
        self.date = date or time.time()
        self.description = description
        self.content = content

    def get_date(self):
        return self.date
    
    def get_content(self):
        return self.content
    
    def get_content_file(self):
        return StringIO(self.content)
    
    def get_description(self):
        return self.description


class ResourcePoolComponent(BaseComponent):
    def __init__(self, exp, parentName, name="pool", resources={}):
        from psychopy.app.builder.experiment import Param
        super(ResourcePoolComponent, self).__init__(exp, parentName, name)
        del self.params["name"]
        self.params["resources"] = Param(resources, "resources")

    def add_resource(self, name, date=None, description="", content=""):
        resource = Resource(date, description, content)
        self.params["resources"].val[name] = resource

    def remove_resource(self, name):
        del self.params["resources"].val[name]

    def get_resource(self, name):
        return self.params["resources"].val.get(name)

    def rename_resource(self, old_name, new_name):
        resource = self.get_resource(old_name)
        self.remove_resource(old_name)
        self.params["resources"].val[new_name] = resource

    def writeStartCode(self, b):
        b.writeIndented("#### Embedded resource definitions start ####\n")
        b.writeIndented("resources = {\n")
        b.setIndentLevel(1, relative=True)
        writeSeparator = False
        for resourceName, resource in self.params["resources"].val.items():
            if writeSeparator:
                b.writeIndented(",\n")
            b.writeIndented("\"%s\":\n" % resourceName)
            b.writeIndented("StringIO(base64.decodestring(\"\"\"%s\"\"\"))" % resource.get_content())
            writeSeparator = True
        b.writeIndented("}\n")
        b.setIndentLevel(-1, relative=True)
        b.writeIndented("#### Embedded resource definitions end ####\n\n")
            

class ResourcePoolWindow(wx.Frame):
    pass
