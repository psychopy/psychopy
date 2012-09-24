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
    """
    Customized ListView showing contents of a resource pool. Used as a main component in
    ResourcePoolDialog.
    
    @see: ResourcePoolDialog
    """
    def __init__(self, parent, resource_entries):
        super(ResourceList, self).__init__(parent, style=wx.LC_ICON)
        self.InsertColumn(0, "name")
        self.fill_resources(resource_entries)
    
    def fill_resources(self, resource_entries):
        for entry in resource_entries:
            self.Append(entry)
    
    def update_resources(self, resource_entries):
        self.ClearAll()
        self.fill_resources(resource_entries)


class ResourcePoolDialog(wx.Frame):
    """
    A window which allows adding, editing and deleting resources.
    """
    def __init__(self, parent, pool):
        super(ResourcePoolDialog, self).__init__(parent, title="Resource Pool")
        self.app = parent.app
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
        remove_tool_id = wx.NewId()
        
        self.Bind(wx.EVT_TOOL, self.show_file_add, id=add_tool_id)
        self.Bind(wx.EVT_TOOL, self.remove_file, id=remove_tool_id)
        bitmap_add_path = os.path.join(self.app.prefs.paths['resources'], "fileopen32.png")
        bitmap_add = wx.Bitmap(bitmap_add_path)
        bitmap_remove_path = os.path.join(self.app.prefs.paths['resources'], "delete32.png")
        bitmap_remove = wx.Bitmap(bitmap_remove_path)
        toolbar.AddLabelTool(add_tool_id, "add file", bitmap_add)
        toolbar.AddLabelTool(remove_tool_id, "remove file", bitmap_remove)
        
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

    def show_file_add(self, event):
        file_name = wx.FileSelector("Add file", parent=self)
        if file_name:
            self.add_to_pool(file_name)
            self.list_added()

    def remove_file(self, event):
        #get selection
        index = self.resource_list.GetFirstSelected()
        name = self.resource_list.GetItem(index, 0).GetText()
        print name
        self.pool.remove_resource(name)
        self.resource_list.update_resources(self.make_resource_entries())

            
