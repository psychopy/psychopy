from psychopy.tools.imagetools import *
import numpy
from psychopy.tests import utils
from pathlib import Path
from PIL import Image as image, ImageChops
import pytest


resources = Path(utils.TESTS_DATA_PATH)


imgL = image.open(str(resources / "testpixels.png")).convert("L")
imgF = image.open(str(resources / "testpixels.png")).convert("F")
arrL = numpy.array([
    [  0,  76, 226, 150, 179,  29, 105, 255],
    [136, 136, 136, 136,   1,   1,   1,   1],
    [136, 136, 136, 136,   1,   1,   1,   1],
    [136, 136, 136, 136,   1,   1,   1,   1],
    [254, 254, 254, 254, 137, 137, 137, 137],
    [254, 254, 254, 254, 137, 137, 137, 137],
    [254, 254, 254, 254, 137, 137, 137, 137],
    [103, 242, 132, 126, 165, 160, 196, 198]
], dtype=numpy.uint8)
arrF = numpy.array([
    [  0.   ,  76.245, 225.93 , 149.685, 178.755,  29.07 , 105.315, 255.   ],
    [136.   , 136.   , 136.   , 136.   ,   1.   ,   1.   ,   1.   , 1.     ],
    [136.   , 136.   , 136.   , 136.   ,   1.   ,   1.   ,   1.   , 1.     ],
    [136.   , 136.   , 136.   , 136.   ,   1.   ,   1.   ,   1.   , 1.     ],
    [254.   , 254.   , 254.   , 254.   , 137.   , 137.   , 137.   , 137.   ],
    [254.   , 254.   , 254.   , 254.   , 137.   , 137.   , 137.   , 137.   ],
    [254.   , 254.   , 254.   , 254.   , 137.   , 137.   , 137.   , 137.   ],
    [102.912, 242.   , 132.04 , 126.477, 165.264, 159.543, 196.144, 197.993]
], dtype=numpy.float32)


@pytest.mark.imagetools
def test_array2image():
    # Test when image type is F
    assert not ImageChops.difference(
        array2image(arrF).convert('RGB'), imgF.convert('RGB')
    ).getbbox()
    # Test when image type is L
    assert not ImageChops.difference(
        array2image(arrL).convert('RGB'), imgL.convert('RGB')
    ).getbbox()


@pytest.mark.imagetools
def test_image2array():
    # Test when image type is F
    assert numpy.array_equal(
        image2array(imgF), arrF
    )
    # Test when image type is L
    assert numpy.array_equal(
        image2array(imgL), arrL
    )
