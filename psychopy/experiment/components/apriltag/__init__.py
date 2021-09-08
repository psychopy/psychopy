#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from contextlib import contextmanager
from os import path
from pathlib import Path
from psychopy.experiment.components import image
from psychopy.experiment.components.image import ImageComponent, Param, getInitVals
from psychopy.localization import _translate


class AprilTagComponent(ImageComponent):
    """An event class for presenting image-based AprilTag stimuli"""

    categories = ['Stimuli']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'apriltag.png'
    tooltip = _translate('AprilTag: present AprilTag image')

    _apriltag_images_dir = Path(__file__).parent / 'apriltag_images'

    def __init__(self, exp, parentName, name='apriltag',
                 apriltag_family='tag16h5', apriltag_id=0,
                 **kwargs):
        super(AprilTagComponent, self).__init__(
            exp, parentName, name=name,
            interpolate='nearest', **kwargs)

        self.params['apriltag_family'] = Param(
            apriltag_family, valType='str', inputType="choice", categ='Basic',
            allowedVals=list(_apriltag_family_name_to_image_prefix.keys()),
            hint=_translate("AprilTag Family"),
            label=_translate('AprilTag Family'))

        self.params['apriltag_id'] = Param(
            apriltag_id, valType='int', inputType="int", categ='Basic',
            hint=_translate("AprilTag ID"),
            label=_translate("AprilTag ID"))

        # Define the UI config params from image that are not used in apriltag
        hidden_param_keys = ['image', 'interpolate']
        self.__hidden_params = {k: self.params[k] for k in hidden_param_keys}

        # Hide the image UI config params
        for key in self.__hidden_params.keys():
            del self.params[key]

    def writeInitCode(self, buff):
        with self._recreated_image_param():
            super().writeInitCode(buff)

    def writeInitCodeJS(self, buff):
        with self._recreated_image_param():
            super().writeInitCodeJS(buff)

    @property
    def _image_path(self):
        """Returns the path to the apriltag image based on user selection"""
        images_dir = self._apriltag_images_dir
        tag_family = self.params["apriltag_family"].val
        file_prefix = _apriltag_family_name_to_image_prefix[tag_family]
        tag_id = self.params["apriltag_id"].val
        tag_id = str(tag_id).zfill(5)
        return path.join(images_dir, tag_family, f"{file_prefix}{tag_id}.png")

    @contextmanager
    def _recreated_image_param(self):
        """Context manager which restores image params on yield"""

        # Restore the image UI config params
        for key, param in self.__hidden_params.items():
            self.params[key] = param

        try:
            # Validate and update the image path param
            image_path = self._image_path
            assert path.isfile(image_path), image_path
            self.params['image'].val = image_path
            yield
        finally:
            # Hide the image UI config params
            for key in self.__hidden_params.keys():
                del self.params[key]


_apriltag_family_name_to_image_prefix = {
    "tag16h5": "tag16_05_",
    "tag25h9": "tag25_09_",
    "tag36h11": "tag36_11_",
    "tagCircle21h7": "tag21_07_",
    "tagCircle49h12": "tag49_12_",
    "tagCustom48h12": "tag48_12_",
    "tagStandard41h12": "tag41_12_",
    "tagStandard52h13": "tag52_13_",
}
