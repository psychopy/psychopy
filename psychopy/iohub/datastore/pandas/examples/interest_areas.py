# -*- coding: utf-8 -*-
"""Demonstrates using Interest Areas to filter events by spatial locations.

NOTE: The use of Interest Areas within the datastore.panda module requires
that the python module called 'shapely' is installed on your python env.
s
@author: Sol

"""
from __future__ import print_function
from psychopy.iohub.datastore.pandas import ioHubPandasDataView
from psychopy.iohub.datastore.pandas.interestarea import Circle, Ellipse, Rectangle


exp_data = ioHubPandasDataView('io_stroop.hdf5')

print('Available Event Tables:')
print()
print(exp_data.event_table_info)
print()

print('MOUSE_MOVE events:', exp_data.MOUSE_MOVE.shape)
print(exp_data.MOUSE_MOVE)
print()

print('Creating Interest Areas....')
print()

# create some InterestAreas. Positions are in pixels in the data file,
# so represent interest areas in the pixel coord space as well.
#
circle = Circle('Circle IA', [0, 0], 400)
rect = Rectangle('Rect IA', -200, 200, 200, -200)
ellipse = Ellipse('Ellipse IA', [300, 300], 100, 200, 45)
spot = Circle('Spot IA', [300, 300], 10)

print('Filtering MOUSE MOVE events by each IP created.')
print()
print('* MOUSE_MOVE events within Circle IA:')
print(circle.filter(exp_data.MOUSE_BUTTON_RELEASE).head(25))
print()
print('* MOUSE_MOVE events within Ellipse IAs:')
print(ellipse.filter(exp_data.MOUSE_BUTTON_PRESS).head(25))
print()

exp_data.close()
