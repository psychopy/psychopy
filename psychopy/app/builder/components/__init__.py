"""Extensible set of components for the PsychoPy Builder view
"""
# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import os, glob, wx, Image
from os.path import *
import psychopy
def pilToBitmap(pil):
    image = wx.EmptyImage(pil.size[0], pil.size[1] )
    image.SetData( pil.convert( "RGB").tostring() )
    image.SetAlphaData(pil.convert("RGBA").tostring()[3::4])
    return image.ConvertToBitmap()#wx.Image and wx.Bitmap are different

def getIcons(filename=None):
        """Creates wxBitmaps ``self.icon`` and ``self.iconAdd`` based on the the image. 
        The latter has a plus sign added over the top.
        
        png files work best, but anything that wx.Image can import should be fine
        """
        if filename==None:
            filename=join(dirname(abspath(__file__)),'base.png')
        im = Image.open(filename)
        icon = pilToBitmap(im)
        #add the plus sign
        add = Image.open(join(dirname(abspath(__file__)),'add.png'))
        im.paste(add, [0,0,add.size[0], add.size[1]], mask=add)
        #im.paste(add, [im.size[0]-add.size[0], im.size[1]-add.size[1],im.size[0], im.size[1]], mask=add)
        iconAdd = pilToBitmap(im)

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
        for file in glob.glob(os.path.join(folder, '*.py')):#must start with a letter
            file=os.path.split(file)[1]
#            module = imp.load_source(file[:-3], fullPath)#can't use imp - breaks py2app
            exec('import %s as module' %(file[:-3]))
            for attrib in dir(module):
                name=None
                #just fetch the attributes that end with 'Component', not other functions
                if attrib.endswith('omponent') and \
                    attrib not in ['VisualComponent', 'BaseComponent']:#must be a component
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