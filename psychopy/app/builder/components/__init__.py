"""Extensible set of components for the PsychoPy Builder view
"""
import os, imp, glob, wx
from os.path import *

def getIcons(filename=None):
        """Creates wxBitmaps ``self.icon`` and ``self.iconAdd`` based on the the image. 
        The latter has a plus sign added over the top.
        
        png files work best, but anything that wx.Image can import should be fine
        """
        if filename==None:
            filename=join(dirname(abspath(__file__)),'base.png')
        im = wx.Image(filename)
        icon = wx.BitmapFromImage(im)
        #add the plus sign
        add = wx.Image(join(dirname(abspath(__file__)),'edit_add.png'))
        im.Paste(add.Copy(),0,0)
        iconAdd = wx.BitmapFromImage(im)
        return icon, iconAdd
        
def getComponents(folder=None):
    """Get a dictionary of available component objects for the Builder experiments.
    
    If folder==None then the built-in components will be returned, otherwise
    the components found in the folder provided will be returned.
    """    
    if folder==None:
        folder = dirname(__file__)
    os.sys.path.append(folder)
    components={}  
    #setup a default icon
    if 'default' not in icons.keys():
        icons['default']=getIcons(filename=None) 
    #go through components in directory
    if os.path.isdir(folder):
        for file in glob.glob(os.path.join(folder, '[A-z]*.py')):#must start with a letter
            fullPath=os.path.join(folder, file)
            module = imp.load_source(file[:-3], fullPath)
            for attrib in dir(module):
                name=None
                #just fetch the attributes that end with 'Component', not other functions
                if attrib.endswith('omponent') and \
                    attrib not in ['VisualComponent', 'BaseComponent']:#must be a component
                    print file, attrib
                    name=attrib
                    components[attrib]=getattr(module, attrib)
                    #also try to get an iconfile
                    if hasattr(module,'iconFile'):
                        icons[name]=getIcons(module.iconFile)
                    else:icons[name]=icons['default']
    return components

def getAllComponents(folderList=[]):
    """Get a dictionary of all available components, from the builtins as well
    as all folders in the folderlist.
    
    User-defined components will override built-ins with the same name.
    """
    if type(folderList)!=list:
        raise TypeError, 'folderList should be a list, not a string'
    components=getComponents()#get the built-ins
    for folder in folderList:
        userComps=getComponents(folder)
        for thisKey in userComps.keys():
            components[thisKey]=userComps[thisKey]
    return components

icons={}