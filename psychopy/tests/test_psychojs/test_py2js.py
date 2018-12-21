
"""Test the output of py2js conversion
"""

import psychopy.experiment.py2js as py2js

class Test_PY2JS_Compile(object):
    """
    Test class for py2js code conversion
    """

    def test_Py2js_Expression2js(self):
        """Test that converts a short expression (e.g. a Component Parameter) Python to JS"""
        input = ['sin(t)',
                 'cos(t)',
                 'tan(t)',
                 'pi',
                 'rand',
                 'random',
                 't*5',
                 '(3, 4)',
                 '(5*-2)',
                 '(1,(2,3))',
                 '2*(2, 3)',
                 '[1, (2*2)]',
                 '(.7, .7)',
                 '(-.7, .7)',
                 '[-.7, -.7]',
                 '[-.7, (-.7 * 7)]']

        output = ['Math.sin(t)',
                  'Math.cos(t)',
                  'Math.tan(t)',
                  'Math.PI',
                  'Math.random',
                  'Math.random',
                  '(t * 5)',
                  '[3, 4]',
                  '(5 * (- 2))',
                  '[1, [2, 3]]',
                  '(2 * [2, 3])',
                  '[1, (2 * 2)]',
                  '[0.7, 0.7]',
                  '[(- 0.7), 0.7]',
                  '[(- 0.7), (- 0.7)]',
                  '[(- 0.7), ((- 0.7) * 7)]']

        for idx, expr in enumerate(input):
            # check whether direct match or at least a match when spaces removed
            assert (py2js.expression2js(expr) == output[idx] or
            py2js.expression2js(expr).replace(" ", "") == output[idx].replace(" ", ""))