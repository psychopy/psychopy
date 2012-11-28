'''
Module handles images and other resources.
'''

import os.path
import wx
from psychopy.app.builder import components

class ArtProvider(wx.ArtProvider):
    
    IMAGE_FILES = {
        "sketchpad-ellipse": "ellipse.png",
        "sketchpad-rectangle": "rectangle.png",
        "sketchpad-arrow": "arrow.png" 
    }
    
    def __init__(self):
        super(ArtProvider, self).__init__()
        self.resource_path = wx.GetApp().prefs.paths["resources"]
    
    def CreateBitmap(self, art_id, client, size):
        image_path = self.IMAGE_FILES.get(art_id)
        if image_path:
            full_path = os.path.join(self.resource_path, image_path)
            bitmap = wx.Bitmap(full_path, wx.BITMAP_TYPE_PNG)
            if bitmap.IsOk():
                return bitmap
            else:
                return wx.NullBitmap
        else:
            return wx.NullBitmap


class ComponentArtProvider(wx.ArtProvider):
    def CreateBitmap(self, art_id, client, size):
        if str(art_id).startswith("components-"):
            component_name = art_id[len("components-"):]
            icon_set = components.icons[component_name]
            if icon_set:
                return icon_set["24"]
            else:
                return wx.NullBitmap
        else:
            return wx.NullBitmap
