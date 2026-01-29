#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to image handling"""

__all__ = ['HaarCascadeObjectRecognizer', 'array2image', 'image2array', 'makeImageAuto']

try:
    from PIL import Image
except ImportError:
    import Image

import os
import numpy
from psychopy.experiment.components import image
from psychopy.tools.typetools import float_uint8


class BaseObjectRecognizer:
    """Base class for object recognizers used for object detection in images.
    This class should be subclassed to implement specific recognition algorithms.
    """

    def detectObjects(self, image, **kwargs):
        """Detect objects in the given image.

        Parameters
        ----------
        image : numpy.ndarray
            The image in which to detect objects.
        **kwargs : keyword arguments
            Additional keyword arguments for future expansion.

        Returns
        -------
        list 
            A list of detected objects with their details. Each object is
            represented as a dictionary with keys:
                - 'rect': (x, y, w, h) rectangle coordinates.
                - 'size': (w, h) size of the rectangle.
                - 'center': (x, y) center coordinates.
                - 'bbox': bounding box corner points.

        """
        raise NotImplementedError("Subclasses must implement this method.")


class HaarCascadeObjectRecognizer(BaseObjectRecognizer):
    """A class to hold information about an object classifier (e.g., Haar
    Cascade) used for object detection in images.

    Parameters
    ----------
    classifer : str
        The name or path of the classifier XML file.
    scaleFactor : float, optional
        Parameter specifying how much the image size is reduced at each image 
        scale. Default is 1.1.
    minNeighbors : int, optional
        Parameter specifying how many neighbors each candidate rectangle should 
        have to retain it. Default is 5.
    minSize : tuple, optional
        Minimum possible object size. Default is (30, 30).
    searchPaths : list or str, optional
        Additional paths to search for classifier XML files.
    name : str, optional
        A name for the classifier. If None, the filename will be used.
    **kwargs : keyword arguments
        Additional keyword arguments for future expansion.

    """
    _detectorType = 'haarCascade'
    _searchPaths = []  # additional search paths for classifier XML files

    def __init__(self, classifer, scaleFactor=1.1, minNeighbors=5, 
                 minSize=(30, 30), name=None, **kwargs):  # for later expansion
        classifierXMLPath = self._getClassifierPath(classifer)
        if classifierXMLPath is None:
            # check if the file exists as given
            if os.path.isfile(classifer):
                classifierXMLPath = classifer
            else:
                raise ValueError(f"Classifier XML file '{classifer}' not found.")
        
        import cv2
        self._classifier = cv2.CascadeClassifier(classifierXMLPath)
        self._scaleFactor = scaleFactor
        self._minNeighbors = minNeighbors
        self._minSize = minSize
        self._flags = cv2.CASCADE_SCALE_IMAGE

        # if not provided, use the filename as the name
        self.name = os.path.basename(
            classifierXMLPath) if name is None else name

    @staticmethod
    def addSearchPaths(*args):
        """Add additional search paths for classifier XML files.

        Parameters
        ----------
        *args : str
            One or more directory paths to add to the search paths.
            
        """
        if not args:
            return
        
        for path in args:
            if path not in HaarCascadeObjectRecognizer._searchPaths:
                HaarCascadeObjectRecognizer._searchPaths.append(path)

    def getAvailableClassifiers(self):
        """Return a list of available pre-trained classifiers.

        Returns
        -------
        list
            A list of strings representing the names of available classifiers.

        """
        # glob the haarcascade files from cv2 data
        import cv2

        defaultXMLDir = cv2.data.haarcascades
        cascadeDirs = [defaultXMLDir] + self._searchPaths

        xmlFiles = []
        for cascadeDir in cascadeDirs:
            if os.path.isdir(cascadeDir):
                for file in os.listdir(cascadeDir):
                    if file.endswith('.xml'):
                        xmlFiles.append(os.path.join(cascadeDir, file))

        return xmlFiles
    
    def _getClassifierPath(self, classifierName):
        """Get the full path to a classifier XML file by name.

        Parameters
        ----------
        classifierName : str
            The name of the classifier XML file.

        Returns
        -------
        str or None
            The full path to the classifier XML file if found, else None.

        """
        for path in self.getAvailableClassifiers():
            if os.path.basename(path) == classifierName:
                return path
            
        return None
    
    def _convertCoords(self, rect, imageShape):
        """Convert rectangle coordinates based on the specified coordinate space
        and origin.

        Parameters
        ----------
        rect : tuple
            A tuple (x, y, w, h) representing the rectangle.
        imageShape : tuple
            The shape of the image (height, width).

        Returns
        -------
        tuple
            Converted rectangle coordinates.

        """
        x, y, w, h = rect

        # make coordinate origin the center of the image
        imgWidth, imgHeight = imageShape[:2]  # height+width not depth

        x = x - imgWidth // 2
        y = (y - imgHeight // 2)

        return (x, y, w, h)
    
    def _getGetBoundingBox(self, rect):
        """Get coordinates of the corner points of the bounding box.
        
        Parameters
        ----------
        rect : tuple
            A tuple (x, y, w, h) representing the rectangle.

        """
        x, y, w, h = rect
        return ((x, y), (x + w, y), (x + w, y + h), (x, y + h))

    def detectObjects(self, image, **kwargs):
        """Detect objects in the given image using the classifier.

        Parameters
        ----------
        image : numpy.ndarray
            The image in which to detect objects. Image is expected to be in
            grayscale format.
        **kwargs : keyword arguments
            Additional keyword arguments for future expansion.

        Returns
        -------
        list 
            A list of detected objects with their details. Each object is
            represented as a dictionary with keys:
                - 'rect': (x, y, w, h) rectangle coordinates.
                - 'size': (w, h) size of the rectangle.
                - 'center': (x, y) center coordinates.
                - 'bbox': bounding box corner points.

            Returned coordinates are adjusted to have the origin at the center
            of the image with y-axis pointing upwards. Furthermore, 

        """
        toReturn = []
        
        if self._classifier is None:
            return toReturn

        foundObjects = self._classifier.detectMultiScale(
            image,
            scaleFactor=self._scaleFactor,
            minNeighbors=self._minNeighbors,
            minSize=self._minSize,
            flags=self._flags
        )

        for boundRect in foundObjects:
            x, y, w, h = self._convertCoords(boundRect, image.shape[:2])
            x = int(x)
            y = int(y)
            toReturn.append({
                'rect': (x, y, w, h),
                'size': (w, h),
                'center': (x, -int(y + h)),
                'bbox': self._getGetBoundingBox(boundRect)
            })

        return toReturn


def array2image(a):
    """Takes an array and returns an image object (PIL)."""
    # fredrik lundh, october 1998
    #
    # fredrik@pythonware.com
    # http://www.pythonware.com
    #
    if a.dtype.kind in ['u', 'I', 'B']:
        mode = "L"
    elif a.dtype.kind in [numpy.float32, 'f']:
        mode = "F"
    else:
        raise ValueError("unsupported image mode")

    im = Image.frombytes(mode, (a.shape[1], a.shape[0]), a.tobytes())

    return im


def image2array(im):
    """Takes an image object (PIL) and returns a numpy array.
    """
    #     fredrik lundh, october 1998
    #
    #     fredrik@pythonware.com
    #     http://www.pythonware.com
    #
    if im.mode not in ("L", "F"):
        raise ValueError("can only convert single-layer images")

    imdata = im.tobytes()

    if im.mode == "L":
        a = numpy.frombuffer(imdata, numpy.uint8)
    else:
        a = numpy.frombuffer(imdata, numpy.float32)

    a.shape = im.size[1], im.size[0]
    return a


def makeImageAuto(inarray):
    """Combines float_uint8 and image2array operations ie. scales a numeric
    array from -1:1 to 0:255 and converts to PIL image format.
    """
    return image2array(float_uint8(inarray))
