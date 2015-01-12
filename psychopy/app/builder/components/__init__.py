"""Extensible set of components for the PsychoPy Builder view
"""
# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import os, glob, copy
import wx
try:
    from PIL import Image
except ImportError:
    import Image
from os.path import join, dirname, abspath

excludeComponents = ['VisualComponent', 'BaseComponent', #these are templates, not for use
                     'EyetrackerComponent', #this one isn't ready yet
                     ]

def pilToBitmap(pil,scaleFactor=1.0):
    image = wx.EmptyImage(pil.size[0], pil.size[1] )
    image.SetData( pil.convert( "RGB").tostring() )
    image.SetAlphaData(pil.convert("RGBA").tostring()[3::4])
    image.Rescale(image.Width*scaleFactor, image.Height*scaleFactor)
    return image.ConvertToBitmap()#wx.Image and wx.Bitmap are different

def getIcons(filename=None):
    """Creates wxBitmaps ``self.icon`` and ``self.iconAdd`` based on the the image.
    The latter has a plus sign added over the top.

    png files work best, but anything that wx.Image can import should be fine
    """
    icons={}
    if filename is None:
        filename=join(dirname(abspath(__file__)),'base.png')
    im = Image.open(filename)
    icons['48'] = pilToBitmap(im)
    icons['24'] = pilToBitmap(im, scaleFactor=0.5)
    #add the plus sign
    add = Image.open(join(dirname(abspath(__file__)),'add.png'))
    im.paste(add, [0,0,add.size[0], add.size[1]], mask=add)
    #im.paste(add, [im.size[0]-add.size[0], im.size[1]-add.size[1],im.size[0], im.size[1]], mask=add)
    icons['48add'] = pilToBitmap(im)
    icons['24add'] = pilToBitmap(im, scaleFactor=0.5)

    return icons

def getComponents(folder=None, fetchIcons=True):
    """Get a dictionary of available component objects for the Builder experiments.

    If folder is None then the built-in components will be returned, otherwise
    the components found in the folder provided will be returned.
    """
    if folder is None:
        folder = dirname(__file__)
    os.sys.path.append(folder)
    components={}
    #setup a default icon
    if fetchIcons and 'default' not in icons.keys():
        icons['default']=getIcons(filename=None)
    #go through components in directory
    if os.path.isdir(folder):
        for file in glob.glob(os.path.join(folder, '*.py')):#must start with a letter
            file=os.path.split(file)[1]
#            module = imp.load_source(file[:-3], fullPath)#can't use imp - breaks py2app
            exec('import %s as module' %(file[:-3]))
            if not hasattr(module,'categories'):
                module.categories=['Custom']
            for attrib in dir(module):
                name=None
                #just fetch the attributes that end with 'Component', not other functions
                if attrib.endswith('omponent') and \
                    attrib not in excludeComponents:#must be a component
                    name=attrib
                    components[attrib]=getattr(module, attrib)
                    #also try to get an iconfile
                    if fetchIcons:
                        if hasattr(module,'iconFile'):
                            icons[name]=getIcons(module.iconFile)
                        else:
                            icons[name]=icons['default']
                    if hasattr(module, 'tooltip'):
                        tooltips[name] = module.tooltip
                    #assign the module categories to the Component
                    if not hasattr(components[attrib], 'categories'):
                        components[attrib].categories=['Custom']
    return components

def getAllComponents(folderList=[], fetchIcons=True):
    """Get a dictionary of all available components, from the builtins as well
    as all folders in the folderlist.

    User-defined components will override built-ins with the same name.
    """
    if type(folderList)!=list:
        raise TypeError, 'folderList should be a list, not a string'
    components=getComponents(fetchIcons=fetchIcons)#get the built-ins
    for folder in folderList:
        userComps=getComponents(folder)
        for thisKey in userComps.keys():
            components[thisKey]=userComps[thisKey]
    return components


def getAllCategories(folderList=[]):
    allComps = getAllComponents(folderList)
    allCats = ['Stimuli','Responses','Custom']
    for name, thisComp in allComps.items():
        for thisCat in thisComp.categories:
            if thisCat not in allCats:
                allCats.append(thisCat)
    return allCats

def getInitVals(params):
    """Works out a suitable initial value for a parameter (e.g. to go into the
    __init__ of a stimulus object, avoiding using a variable name if possible
    """
    inits = copy.deepcopy(params)
    for name in params.keys():

        if not hasattr(inits[name], 'updates'):#might be settings parameter instead
            continue

        #value should be None (as code)
        elif inits[name].val in [None,'None','none','']:
            inits[name].val='None'
            inits[name].valType='code'

        #is constant so don't touch the parameter value
        elif inits[name].updates in ['constant',None,'None']:
            continue #things that are constant don't need handling

        #is changing so work out a reasonable default
        elif name in ['pos', 'fieldPos']:
            inits[name].val='[0,0]'
            inits[name].valType='code'
        elif name in ['ori','sf','size','height','letterHeight',
                    'color','lineColor','fillColor',
                    'phase','opacity',
                    'volume', #sounds
                    'coherence','nDots', 'fieldSize','dotSize', 'dotLife', 'dir', 'speed',#dots
                    ]:
            inits[name].val="1.0"
            inits[name].valType='code'
        elif name in ['image','mask']:
            inits[name].val="sin"
            inits[name].valType='str'
        elif name=='texture resolution':
            inits[name].val="128"
            inits[name].valType='code'
        elif name == 'colorSpace':
            inits[name].val="rgb"
            inits[name].valType='str'
        elif name == 'font':
            inits[name].val="Arial"
            inits[name].valType='str'
        elif name == 'units':
            inits[name].val="norm"
            inits[name].valType='str'
        elif name == 'text':
            inits[name].val="default text"
            inits[name].valType='str'
        elif name == 'flip':
            inits[name].val=""
            inits[name].valType='str'
        elif name == 'sound':
            inits[name].val="A"
            inits[name].valType='str'
        else:
            print "I don't know the appropriate default value for a '%s' parameter. Please email the mailing list about this error" %name
    return inits

tooltips = {}
icons = {}
