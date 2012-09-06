'''
Created on 04-09-2012

@author: piwaniuk
'''
import wx
from StringIO import StringIO
import base64
import os.path
from psychopy.app.builder.components.resource_pool import Resource

class ResourceList(wx.ListView):
    def __init__(self, parent, resource_entries):
        super(ResourceList, self).__init__(parent, style=wx.LC_ICON)
        self.InsertColumn(0, "name")
        self.fill_resources(resource_entries)
    
    def fill_resources(self, resource_entries):
        for entry in resource_entries:
            self.Append(entry)


class ResourcePoolDialog(wx.Frame):
    def __init__(self, parent, pool):
        super(ResourcePoolDialog, self).__init__(parent, title="Resource Pool")
        self.pool = pool
        self.resource_list = ResourceList(self, self.make_resource_entries())
        self.init_toolbar()
        self.SetSizer(wx.BoxSizer())
        self.GetSizer().Add(self.resource_list, 1, wx.EXPAND)

    def make_resource_entries(self):
        return [[resource.get_name()] for resource in self.pool.params["resources"].val]
            
    def init_toolbar(self):
        toolbar = self.CreateToolBar()
        add_tool_id = wx.NewId()
        self.Bind(wx.EVT_TOOL, self.show_file_add, id=add_tool_id)
        toolbar.AddLabelTool(add_tool_id, "foo", wx.Bitmap("Resources/fileopen32.png"))
        toolbar.Realize()

    def add_to_pool(self, file_name):
        added_file = open(file_name)
        encoded_data = StringIO()
        base64.encode(added_file, encoded_data)
        short_name = os.path.split(file_name)[1]
        self.pool.add_resource(short_name, content=encoded_data.getvalue())

    def list_added(self):
        entry = [self.pool.params["resources"].val[-1].get_name()]
        self.resource_list.Append(entry)

    def show_file_add(self, event=None):
        file_name = wx.FileSelector("Add file", parent=self)
        if file_name:
            self.add_to_pool(file_name)
            self.list_added()
            
