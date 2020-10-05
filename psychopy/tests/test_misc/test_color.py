import os
import shutil
from tempfile import mkdtemp
from psychopy.colors import Color, colorSpaces
from psychopy.tests.utils import TESTS_DATA_PATH
import importlib
from psychopy.scripts import psyexpCompile

# Define expected values for different spaces
sets = [
    {'rgb': ( 1.00,  1.00,  1.00), 'rgb255': (255, 255, 255), 'hsv': (  0, 0.00, 1.00), 'hex': '#ffffff', 'named': 'white'}, # Pure white
    {'rgb': ( 0.00,  0.00,  0.00), 'rgb255': (128, 128, 128), 'hsv': (  0, 0.00, 0.50), 'hex': '#808080', 'named': 'gray'}, # Mid grey
    {'rgb': (-1.00, -1.00, -1.00), 'rgb255': (  0,   0,   0), 'hsv': (  0, 0.00, 0.00), 'hex': '#000000', 'named': 'black'}, # Pure black
    {'rgb': ( 1.00, -1.00, -1.00), 'rgb255': (255,   0,   0), 'hsv': (  0, 1.00, 1.00), 'hex': '#ff0000', 'named': 'red'}, # Pure red
    {'rgb': (-1.00,  1.00, -1.00), 'rgb255': (  0, 255,   0), 'hsv': (120, 1.00, 1.00), 'hex': '#00ff00', 'named': 'lime'}, # Pure green
    {'rgb': (-1.00, -1.00,  1.00), 'rgb255': (  0,   0, 255), 'hsv': (240, 1.00, 1.00), 'hex': '#0000ff', 'named': 'blue'}, # Pure blue
    # Psychopy colours
    {'rgb': (-0.20, -0.20, -0.14), 'rgb255': (102, 102, 110), 'hsv': (240, 0.07, 0.43), 'hex': '#66666e'}, # grey
    {'rgb': ( 0.35,  0.35,  0.38), 'rgb255': (172, 172, 176), 'hsv': (240, 0.02, 0.69), 'hex': '#acacb0'}, # light grey
    {'rgb': ( 0.90,  0.90,  0.90), 'rgb255': (242, 242, 242), 'hsv': (  0, 0.00, 0.95), 'hex': '#f2f2f2'}, # offwhite
    {'rgb': ( 0.90, -0.34, -0.29), 'rgb255': (242,  84,  91), 'hsv': (357, 0.65, 0.95), 'hex': '#f2545b'}, # red
    {'rgb': (-0.98,  0.33,  0.84), 'rgb255': (  2, 169, 234), 'hsv': (197, 0.99, 0.92), 'hex': '#02a9ea'}, # blue
    {'rgb': (-0.15,  0.60, -0.09), 'rgb255': (108, 204, 116), 'hsv': (125, 0.47, 0.80), 'hex': '#6ccc74'}, # green
    {'rgb': ( 0.85,  0.18, -0.98), 'rgb255': (236, 151,   3), 'hsv': ( 38, 0.99, 0.93), 'hex': '#ec9703'}, # orange
    {'rgb': ( 0.89,  0.65, -0.98), 'rgb255': (241, 211,   2), 'hsv': ( 52, 0.99, 0.95), 'hex': '#f1d302'}, # yellow
    {'rgb': ( 0.53,  0.49,  0.94), 'rgb255': (195, 190, 247), 'hsv': (245, 0.23, 0.97), 'hex': '#c3bef7'}, # violet
]
# A few values which are likely to mess things up
tykes = [

]

# Begin test
def test_ColorSets():
    for colorSet in sets:
        # Construct matrix of space pairs
        spaceMatrix = []
        for space1 in colorSet:
            spaceMatrix.extend([[space1, space2] for space2 in colorSet if space2 != space1])
        # Compare each space pair for consistency
        for space1, space2 in spaceMatrix:
            col1 = Color(colorSet[space1], space1)
            col2 = Color(colorSet[space2], space2)
            closeEnough = all(abs(col1.rgba[i]-col2.rgba[i])<0.02 for i in range(4))
            # Check setters
            assert col1 == col2 or closeEnough
def test_ColorTykes():
    for colorSet in tykes:
        for space in colorSet:
            assert bool(Color(colorSet[space], space))

def test_ComponentColors():
    # Setup temp directory
    temp_root = mkdtemp()
    temp_dir = os.path.join(temp_root, 'colorTest')
    psyexpDir = os.path.join(TESTS_DATA_PATH, 'componentColorsExperiment')
    shutil.copytree(psyexpDir, temp_dir)
    # Compile experiment
    inFile = os.path.join(temp_dir, 'colour.psyexp')
    outFile = os.path.join(temp_dir, 'colour.py')
    psyexpCompile.compileScript(infile=inFile, outfile=outFile)
    spec = importlib.util.spec_from_file_location("colour.py", outFile)
    # Run experiment
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

