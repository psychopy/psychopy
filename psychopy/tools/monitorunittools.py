#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Functions and classes related to unit conversion respective to a particular
monitor'''

from psychopy import monitors

def convertToPix(vertices, pos, units, win):
    """Takes vertices and position, combines and converts to pixels from any unit

    The reason that `pos` and `vertices` are provided separately is that it allows
    the conversion from deg to apply flat-screen correction to each separately.

    The reason that these use funtion args rather than relying on self.pos
    is that some stimuli (e.g. ElementArrayStim use other terms like fieldPos)
    """
    if units == 'pix':
        verts = pos+vertices
    elif units == 'cm':
        verts = cm2pix(pos+vertices, win.monitor)
    elif units =='deg':
        verts = deg2pix(pos+vertices, win.monitor)
    elif units == 'norm':
        verts = (pos+vertices) * win.size/2.0
    elif units == 'height':
        verts = (pos+vertices) * win.size[1]
    else:
        raise AttributeError, "Unknown unit '%s'"
    return verts

def cm2deg(cm, monitor):
    """Convert size in cm to size in degrees for a given Monitor object"""
    #check we have a monitor
    if not isinstance(monitor, monitors.Monitor):
        raise ValueError("cm2deg requires a monitors.Monitor object as the second argument but received %s" %str(type(monitor)))
    #get monitor dimensions
    dist = monitor.getDistance()
    #check they all exist
    if dist==None:
        raise ValueError("Monitor %s has no known distance (SEE MONITOR CENTER)" %monitor.name)
    return cm/(dist*0.017455)


def deg2cm(degrees, monitor):
    """Convert size in degrees to size in pixels for a given Monitor object"""
    #check we have a monitor
    if not isinstance(monitor, monitors.Monitor):
        raise ValueError("deg2cm requires a monitors.Monitor object as the second argument but received %s" %str(type(monitor)))
    #get monitor dimensions
    dist = monitor.getDistance()
    #check they all exist
    if dist==None:
        raise ValueError("Monitor %s has no known distance (SEE MONITOR CENTER)" %monitor.name)
    return degrees*dist*0.017455


def cm2pix(cm, monitor):
    """Convert size in degrees to size in pixels for a given Monitor object"""
    #check we have a monitor
    if not isinstance(monitor, monitors.Monitor):
        raise ValueError("cm2pix requires a monitors.Monitor object as the second argument but received %s" %str(type(monitor)))
    #get monitor params and raise error if necess
    scrWidthCm = monitor.getWidth()
    scrSizePix = monitor.getSizePix()
    if scrSizePix==None:
        raise ValueError("Monitor %s has no known size in pixels (SEE MONITOR CENTER)" %monitor.name)
    if scrWidthCm==None:
        raise ValueError("Monitor %s has no known width in cm (SEE MONITOR CENTER)" %monitor.name)

    return cm*scrSizePix[0]/float(scrWidthCm)


def pix2cm(pixels, monitor):
    """Convert size in pixels to size in cm for a given Monitor object"""
    #check we have a monitor
    if not isinstance(monitor, monitors.Monitor):
        raise ValueError("cm2pix requires a monitors.Monitor object as the second argument but received %s" %str(type(monitor)))
    #get monitor params and raise error if necess
    scrWidthCm = monitor.getWidth()
    scrSizePix = monitor.getSizePix()
    if scrSizePix==None:
        raise ValueError("Monitor %s has no known size in pixels (SEE MONITOR CENTER)" %monitor.name)
    if scrWidthCm==None:
        raise ValueError("Monitor %s has no known width in cm (SEE MONITOR CENTER)" %monitor.name)
    return pixels*float(scrWidthCm)/scrSizePix[0]


def deg2pix(degrees, monitor):
    """Convert size in degrees to size in pixels for a given Monitor object"""
    #get monitor params and raise error if necess
    scrWidthCm = monitor.getWidth()
    scrSizePix = monitor.getSizePix()
    if scrSizePix==None:
        raise ValueError("Monitor %s has no known size in pixels (SEE MONITOR CENTER)" %monitor.name)
    if scrWidthCm==None:
        raise ValueError("Monitor %s has no known width in cm (SEE MONITOR CENTER)" %monitor.name)

    cmSize = deg2cm(degrees, monitor)
    return cmSize*scrSizePix[0]/float(scrWidthCm)


def pix2deg(pixels, monitor):
    """Convert size in pixels to size in degrees for a given Monitor object"""
    #get monitor params and raise error if necess
    scrWidthCm = monitor.getWidth()
    scrSizePix = monitor.getSizePix()
    if scrSizePix==None:
        raise ValueError("Monitor %s has no known size in pixels (SEE MONITOR CENTER)" %monitor.name)
    if scrWidthCm==None:
        raise ValueError("Monitor %s has no known width in cm (SEE MONITOR CENTER)" %monitor.name)
    cmSize=pixels*float(scrWidthCm)/scrSizePix[0]
    return cm2deg(cmSize, monitor)
