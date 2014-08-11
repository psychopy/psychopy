Tutorial 3: Analysing data in Python
=========================================

You could simply output your data as tab- or comma-separated text files and analyse the data in some spreadsheet package. But the `matplotlib`_ library in Python also allows for very neat and simple creation of publication-quality plots. 

This script shows you how to use a couple of functions from PsychoPy to open some data files (:func:`psychopy.gui.fileOpenDlg`) and create a psychometric function out of some staircase data (:func:`psychopy.data.functionFromStaircase`). 

`Matplotlib`_ is then used to plot the data.

.. note:: `Matplotlib`_ and :mod:`pylab`. Matplotlib is a python library that has similar command syntax to most of the plotting functions in Matlab(tm). In can be imported in different ways; the ``import pylab`` line at the beginning of the script is the way to import matploblib as well as a variety of other scientific tools (that aren't strictly to do with plotting *per se*).

.. _matplotlib: http://matplotlib.sourceforge.net/

.. literalinclude:: tutorial3.py
   :linenos:
