from psychopy import visual, colors  # used to draw stimuli


class TestRect:
    """ A class to test the Rect class """
    @classmethod
    def setup_class(self):
        """ Initialise the rectangle and window objects """
        # Create window
        self.win = visual.Window()
        # Create rect
        self.rect = visual.Rect(self.win)

    def test_color(self):
        """ Test that the color or a rectangle sets correctly """
        # Set the rectangle's fill color
        self.rect.colorSpace = 'rgb'
        self.rect.fillColor = (1, -1, -1)
        # Check that the rgb value of its fill color is consistent with what we set
        assert self.rect._fillColor == colors.Color('red'), f"Was expecting rect._fillColor to have an rgb value of '(1, -1, -1)'," \
                                              f" but instead it was '{self.rect._fillColor.rgb}'"

    def test_rect(self):
        """ Test that a rect object has 4 vertices """
        assert len(self.rect.vertices) == 4, f"Was expecting 4 vertices in a Rect object, got {len(self.rect.vertices)}"

    def test_rect_colors(self):
        """Test a range of known exemplar colors as well as colors we know to be troublesome AKA tykes"""
        # Define exemplars
        exemplars = [
            { # Red with a blue outline
                'fill': 'red',
                'border': 'blue',
                'colorSpace': 'rgb',
                'targetFill': colors.Color((1, -1, -1), 'rgb'),
                'targetBorder': colors.Color((-1, -1, 1), 'rgb'),
            },
            { # Blue with a red outline
                'fill': 'blue',
                'border': 'red',
                'colorSpace': 'rgb',
                'targetFill': colors.Color((-1, -1, 1), 'rgb'),
                'targetBorder': colors.Color((1, -1, -1), 'rgb'),
            },
        ]
        # Define tykes
        tykes = [
            { # Transparent fill with a red border when color space is hsv
                'fill': None,
                'border': 'red',
                'colorSpace': 'rgb',
                'targetFill': colors.Color(None, 'rgb'),
                'targetBorder': colors.Color((0, 1, 1), 'hsv'),
            }
        ]
        # Iterate through all exemplars and tykes
        for case in exemplars + tykes:
            # Set colors
            self.rect.colorSpace = case['colorSpace']
            self.rect.fillColor = case['fill']
            self.rect.borderColor = case['border']
            # Check values are the same
            assert self.rect._fillColor == case['targetFill'], f"Was expecting rect._fillColor to be '{case['targetFill']}', but instead it was '{self.rect._fillColor}'"
            assert self.rect._borderColor == case['targetBorder'], f"Was expecting rect._borderColor to be '{case['targetBorder']}', but instead it was '{self.rect._borderColor}'"

    @classmethod
    def teardown_class(self):
        """clean-up any objects, wxframes or windows opened by the test"""
        # Close the window
        self.win.close()
        # Delete the object
        del self.rect