from psychopy.colors import Color, colorSpaces
import numpy

# Define expected values for different spaces
expectedHSV = [
    (  0, 1.0, 1.0),
    (  0, 1.0, 0.5),
    (  0, 0.5, 0.5),
    ( 30, 1.0, 1.0),
    ( 60, 1.0, 1.0),
    ( 90, 1.0, 1.0),
    (120, 1.0, 1.0),
    (150, 1.0, 1.0),
    (180, 1.0, 1.0),
    (210, 1.0, 1.0),
    (240, 1.0, 1.0),
    (270, 1.0, 1.0),
    (300, 1.0, 1.0),
    (330, 1.0, 1.0),
    (360, 1.0, 1.0)]
expectedRGB = [( 1.0, -1.0, -1.0),
               ( 1.0, -1.0, -1.0),
               ( 0.5, -0.5, -0.5),
               ( 1.0,  0.0, -1.0),
               ( 1.0,  1.0, -1.0),
               ( 0.0,  1.0, -1.0),
               (-1.0,  1.0, -1.0),
               (-1.0,  1.0,  0.0),
               (-1.0,  1.0,  1.0),
               (-1.0,  0.0,  1.0),
               (-1.0, -1.0,  1.0),
               ( 0.0, -1.0,  1.0),
               ( 1.0, -1.0,  1.0),
               ( 1.0, -1.0,  0.0),
               ( 1.0, -1.0, -1.0)]
expectedRGB1 = [(1.0,  0.0,  0.0),
                (1.0,  0.0,  0.0),
                (0.75, 0.25, 0.25),
                (1.0,  0.5,  0.0),
                (1.0,  1.0,  0.0),
                (0.5,  1.0,  0.0),
                (0.0,  1.0,  0.0),
                (0.0,  1.0,  0.5),
                (0.0,  1.0,  1.0),
                (0.0,  0.5,  1.0),
                (0.0,  0.0,  1.0),
                (0.5,  0.0,  1.0),
                (1.0,  0.0,  1.0),
                (1.0,  0.0,  0.5),
                (1.0,  0.0,  0.0)]
expectedRGB255 = [(255,   0,   0),
                  (255,   0,   0),
                  (191,  63,  63),
                  (255, 127,   0),
                  (255, 255,   0),
                  (127, 255,   0),
                  (  0, 255,   0),
                  (  0, 255, 127),
                  (  0, 255, 255),
                  (  0, 127, 255),
                  (  0,   0, 255),
                  (127,   0, 255),
                  (255,   0, 255),
                  (255,   0, 127),
                  (255,   0,   0)]
expectedHex = ['#ff0000',
               '#ff0000',
               '#bf3f3f',
               '#ff7f00',
               '#ffff00',
               '#7fff00',
               '#00ff00',
               '#00ff7f',
               '#00ffff',
               '#007fff',
               '#0000ff',
               '#7f00ff',
               '#ff00ff',
               '#ff007f',
               '#ff0000']
expectedNamed = ['red',
                 'red',
                 None,
                 None,
                 'yellow',
                 'chartreuse',
                 'lime',
                 'springgreen',
                 'aqua',
                 None,
                 'blue',
                 None,
                 'fuchsia',
                 None,
                 'red']
# Combine expected values into one dict
expected = {'named': expectedNamed,
            'hex': expectedHex,
            'rgb': expectedRGB,
            'rgb1': expectedRGB1,
            'rgb255': expectedRGB255,
            'hsv': expectedHSV
            }
# Construct matrix of space pairs
spaceMatrix = []
for space1 in expected:
    spaceMatrix.extend([[space1, space2] for space2 in expected if space2 != space1])

# Begin test
if __name__=='__main__':
    for space1, space2 in spaceMatrix:
        calc = []
        for i in range(len(expected[space1])):
            # For each color in each pair of spaces...
            col1 = expected[space1][i]
            col2 = expected[space2][i]
            if col1 == None or col2 ==None:
                # Skip unnamed colors
                continue
            # ...compare the same color in both spaces
            assert Color(col1, space1) == Color(col2, space2)