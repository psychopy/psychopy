# -*- coding: utf-8 -*-
from __future__ import division
from builtins import object
"""
Pixel to Visual Angle Calculation.

Uses "symmetric angles" formula provided by Dr. Josh Borah
(jborah AT asleyetracking.com), via email correspondence in 2012.

Assumptions:
   1) unit origin == position 0.0, 0.0 == screen center
   2) Eye is orthogonal to origin of 2D plane

"""

import numpy as np
arctan = np.arctan2
rad2deg = np.rad2deg
hypot = np.hypot


class VisualAngleCalc(object):

    def __init__(self, display_size_mm, display_res_pix, eye_distance_mm=None):
        """Used to store calibrated surface information and eye to screen
        distance so that pixel positions can be converted to visual degree
        positions.

        Note: The information for display_size_mm,display_res_pix, and default
        eye_distance_mm could all be read automatically when opening a ioDataStore
        file. This automation should be implemented in a future release.

        """
        self._display_width = display_size_mm[0]
        self._display_height = display_size_mm[1]
        self._display_x_resolution = display_res_pix[0]
        self._display_y_resolution = display_res_pix[1]
        self._eye_distance_mm = eye_distance_mm
        self.mmpp_x = self._display_width / self._display_x_resolution
        self.mmpp_y = self._display_height / self._display_y_resolution

    def pix2deg(self, pixel_x, pixel_y=None, eye_distance_mm=None):
        """
        Stimulus positions (pixel_x,pixel_y) are defined in x and y pixel units,
        with the origin (0,0) being at the **center** of the display, as to match
        the PsychoPy pix unit coord type.

        The pix2deg method is vectorized, meaning that is will perform the
        pixel to angle calculations on all elements of the provided pixel
        position numpy arrays in one numpy call.

        The conversion process can use either a fixed eye to calibration
        plane distance, or a numpy array of eye distances passed as
        eye_distance_mm. In this case the eye distance array must be the same
        length as pixel_x, pixel_y arrays.
        """
        eye_dist_mm = self._eye_distance_mm
        if eye_distance_mm is not None:
            eye_dist_mm = eye_distance_mm

        x_mm = self.mmpp_x * pixel_x
        y_mm = self.mmpp_y * pixel_y

        Ah = arctan(x_mm, hypot(eye_dist_mm, y_mm))
        Av = arctan(y_mm, hypot(eye_dist_mm, x_mm))

        return rad2deg(Ah), rad2deg(Av)

###############################################################################


def generatedPointGrid(pixel_width, pixel_height, width_scalar=1.0,
                       height_scalar=1.0, horiz_points=5, vert_points=5):
    """Generate a set of points in a NxM grid.

    Useful for creating calibration target positions, etc.

    """
    swidth = pixel_width * width_scalar
    sheight = pixel_height * height_scalar
    # center 0 on screen center
    x, y = np.meshgrid(np.linspace(-swidth / 2.0, swidth / 2.0, horiz_points),
                       np.linspace(-sheight / 2.0, sheight / 2.0, vert_points))
    points = np.column_stack((x.flatten(), y.flatten()))
    return points

# Test it

if __name__ == '__main__':

    # physical size (w,h) of monitor in mm
    dsize = (600.0, 330.0)
    # pixel resolution of monitor
    dres = (1920.0, 1080.0)
    # eye distance to monitor in mm:
    edist = 550.0

    # create converter class. Can be reused event if eye distance changes
    # from call to call. Also should support calc with vectorized inputs.
    vacalc = VisualAngleCalc(dsize, dres, edist)

    pix_20x20 = generatedPointGrid(pixel_width=1900, pixel_height=1060,
                                   horiz_points=15, vert_points=15)

    x_pos = pix_20x20[:, 0]
    y_pos = pix_20x20[:, 1]
    deg_20x20 = vacalc.pix2deg(x_pos, y_pos)

    # Plot the 2D target array in pixel and in deg corord units.
    from matplotlib import pyplot

    fig = pyplot.figure()
    fig.suptitle(
        'Pixel to Visual Angle (Eye Dist: %.1f cm, %0.3fx%0.3f cm/pixel' %
        (edist / 10, vacalc.mmpp_x, vacalc.mmpp_y))
    ax1 = fig.add_subplot(211)
    ax1.plot(x_pos, y_pos, '+g')
    ax1.grid(True)
    ax1.set_xlabel('Horizontal Pixel Pos')
    ax1.set_ylabel('Vertical Pixel Pos')

    ax2 = fig.add_subplot(212)
    ax2.plot(deg_20x20[0], deg_20x20[1], '+b')
    ax2.grid(True)
    ax2.set_xlabel('Horizontal Visual Angle')
    ax2.set_ylabel('Vertical Visual Angle')

    pyplot.show()
