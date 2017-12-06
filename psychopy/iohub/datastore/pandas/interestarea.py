# -*- coding: utf-8 -*-
# ioHub DataStore to Pandas DataFrames - Event Filtering Support
# Part of the psychopy.iohub library.
# .. moduleauthor:: Sol Simpson <sol@isolver-software.com> and
#                   Pierce Edmiston <pierce.edmiston@gmail.com>
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division, absolute_import, print_function

try:
    import shapely
    import shapely.geometry
    import shapely.affinity
    import shapely as spy
except ImportError:
    from ...errors import print2err
    print2err("iohub.datastore.pandas.interestarea requires 'shapely' package.")

from weakref import proxy


class Polygon(shapely.geometry.Polygon):
    _next_id = 1

    def __init__(self, name, points):
        self._ia_id = self.__class__._next_id
        self.__class__._next_id += 1
        self._name = name
        if name is None:
            self.name = self.__class__.__name__ + '_' + str(self._ia_id)
        self._last_target_df = None
        shapely.geometry.Polygon.__init__(self, points)

    @property
    def name(self):
        return self._name

    @property
    def ia_id(self):
        return self._ia_id

    def contains(self, v):
        return shapely.geometry.Polygon.contains(
            self, spy.geometry.Point(v[0], v[1]))

    def filter(self, target_df, x_col='x_position', y_col='y_position'):
        if self._last_target_df is not target_df:
            self._last_target_df = proxy(target_df)
            self._ia_df = None
            self._ia_df = target_df[
                target_df[[x_col, y_col]].apply(self.contains, axis=1)]
            self._ia_df['ia_name'] = self.name
            self._ia_df['ia_id'] = self.ia_id
            self._ia_df['ia_name'] = self.name
            self._ia_df['ia_id_num'] = range(1, len(self._ia_df) + 1)
        return self._ia_df


class Circle(Polygon):

    def __init__(self, name, center_point, radius):
        point = shapely.geometry.Point(
            *
            center_point).buffer(
            radius,
            resolution=16)
        Polygon.__init__(self, name, point.exterior.coords)


class Ellipse(Polygon):

    def __init__(
            self,
            name,
            center_point,
            min_axis,
            max_axis,
            angle,
            use_radians=False):
        point = spy.geometry.Point(
            *
            center_point).buffer(
            min_axis,
            resolution=16)
        point = spy.affinity.scale(
            point,
            xfact=1.0,
            yfact=max_axis /
            min_axis,
            origin='center')
        point = spy.affinity.rotate(
            point, angle, origin='center', use_radians=use_radians)
        Polygon.__init__(self, name, point.exterior.coords)


class Rectangle(Polygon):

    def __init__(self, name, minx, miny, maxx, maxy, ccw=True):
        coords = [(maxx, miny), (maxx, maxy), (minx, maxy), (minx, miny)]
        if not ccw:
            coords = coords[::-1]
        Polygon.__init__(self, name, coords)
