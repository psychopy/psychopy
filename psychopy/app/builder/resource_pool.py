'''
Created on 04-09-2012

@author: piwaniuk
'''
import wx
from StringIO import StringIO
import base64
import os.path

class ResourceList(wx.ListView):
    """
    Customized ListView showing contents of a resource pool. Used as a main component in
    ResourcePoolDialog.
    
    @see: ResourcePoolDialog
    """
    def __init__(self, parent, pool=None, name_filter=None):
        super(ResourceList, self).__init__(parent, style=wx.LC_ICON)
        icon_list = wx.ImageList(32, 32)
        icon_list.AddIcon(wx.ArtProvider.GetIcon(wx.ART_NORMAL_FILE, wx.ART_OTHER, (32, 32)))
        self.AssignImageList(icon_list, wx.IMAGE_LIST_NORMAL)
        #self.InsertColumn(0, "name")
        if pool:
            self.fill_resources(pool, name_filter)
    
    def fill_resources(self, pool, name_filter=None):
        name_filter = str(name_filter or "")
        resource_names = (pool.params["resources"].val.keys())
        resource_entries = [[name] for name in filter(lambda s: name_filter in s, resource_names)]
        for pos, entry in enumerate(resource_entries):
            self.InsertImageStringItem(pos, entry[0], 0)
    
    def update_resources(self, pool, name_filter=None):
        self.ClearAll()
        self.fill_resources(pool)


class ResourcePoolDialog(wx.Frame):
    """
    A window which allows adding, editing and deleting resources.
    """
    def __init__(self, parent, pool):
        super(ResourcePoolDialog, self).__init__(parent, title="Resource Pool")
        self.app = parent.app
        self.pool = pool
        self.resource_list = ResourceList(self, self.pool)
        self.init_toolbar()
        self.SetSizer(wx.BoxSizer())
        self.GetSizer().Add(self.resource_list, 1, wx.EXPAND)
            
    def init_toolbar(self):
        toolbar_template = [
            ("add", wx.ART_FILE_OPEN, "Add file", self.show_file_add),
            ("remove", wx.ART_CROSS_MARK, "Remove file", self.remove_file),
            ("export", wx.ART_FILE_SAVE_AS, "Export to file", self.show_file_export)
        ]
        toolbar = self.CreateToolBar()
        for label, bitmap_name, tip, handler in toolbar_template:
            bitmap = wx.ArtProvider.GetBitmap(bitmap_name, wx.ART_TOOLBAR)
            tool_id = toolbar.AddLabelTool(wx.ID_ANY, label, bitmap, shortHelp=tip).GetId()
            self.Bind(wx.EVT_TOOL, handler, id=tool_id)
        toolbar.Realize()

    def add_to_pool(self, file_name):
        added_file = open(file_name)
        encoded_data = StringIO()
        base64.encode(added_file, encoded_data)
        short_name = os.path.split(file_name)[1]
        self.pool.add_resource(short_name, content=encoded_data.getvalue())

    def list_added(self):
        self.resource_list.update_resources(self.pool)

    def show_file_add(self, event):
        file_name = wx.FileSelector("Add file", parent=self)
        if file_name:
            self.add_to_pool(file_name)
            self.list_added()

    def get_selected_resource(self):
        index = self.resource_list.GetFirstSelected()
        name = self.resource_list.GetItem(index, 0).GetText()
        return name

    def remove_file(self, event):
        #get selection
        name = self.get_selected_resource()
        if name:
            self.pool.remove_resource(name)
            self.resource_list.update_resources(self.pool)
    
    def show_file_export(self, event):
        name = self.get_selected_resource()
        if name:
            file_name = wx.FileSelector("Export file", flags=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT, parent=self)
            exported_file = open(file_name, "wb")
            content = base64.decodestring(self.pool.get_resource(name).get_content())
            exported_file.write(content)
            exported_file.close()


class ResourceChooserPanel(wx.Panel):
    def __init__(self, parent, pool):
        super(ResourceChooserPanel, self).__init__(parent)
        self.pool = pool
        self.init_controls(self.pool)
        self.init_sizer()
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.item_selected)

    def init_controls(self, pool):
        self.resource_name_box = wx.TextCtrl(self)
        self.resource_list = ResourceList(self, pool)
        self.preview_panel = wx.Panel(self)

    def init_sizer(self):
        sizer = wx.GridBagSizer()
        sizer.AddGrowableCol(0, proportion=21)
        sizer.AddGrowableCol(1, proportion=13)
        sizer.AddGrowableRow(1)
        sizer.Add(self.resource_name_box, (0, 0), (1, 1), flag=wx.EXPAND)
        sizer.Add(self.resource_list, (1, 0), (1, 1), flag=wx.EXPAND)
        sizer.Add(self.preview_panel, (0, 1), (2, 1), flag=wx.EXPAND)
        self.SetSizer(sizer)
    
    def item_selected(self, event):
        resource_name = event.GetItem().GetText()
        self.resource_name_box.SetValue(resource_name)


class ResourceChooserDialog(wx.Dialog):
    def __init__(self, parent, pool):
        super(ResourceChooserDialog, self).__init__(parent, title="Choose resource")
        self.pool = pool
        self.resource_name = None
        self.chooser = ResourceChooserPanel(self, pool)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.chooser, proportion=1, flag=wx.EXPAND)
        sizer.Add(self.CreateButtonSizer(wx.CANCEL | wx.OK), flag=wx.EXPAND)
        self.SetSizer(sizer)
        self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)

    def Validate(self):
        resource_name = self.chooser.resource_name_box.GetValue()
        if self.pool.get_resource(resource_name):
            self.resource_name = resource_name
            return True
        else:
            return False
    
    def on_ok(self, event):
        if self.Validate():
            event.Skip()
        else:
            wx.MessageBox("Specified resource file does not exist.", "Choose resource", wx.OK | wx.ICON_EXCLAMATION)


if __name__ == "__main__":
    app = wx.App()
    dialog = ResourceChooserDialog(None, None)
    dialog.Show()
    app.SetTopWindow(dialog)
    app.MainLoop()
