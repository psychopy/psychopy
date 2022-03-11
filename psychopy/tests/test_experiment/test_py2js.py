from psychopy.experiment.py2js_transpiler import translatePythonToJavaScript
import psychopy.experiment.py2js as py2js


class TestTranspiler:

    def runTranspile(self, py, js):
        transpiledCode = translatePythonToJavaScript(py)
        assert (js == transpiledCode)

    def test_assignment(self):
        py = ("a = 1")
        js = ("a = 1;\n")
        self.runTranspile(py, js)

    def test_name(self):
        # Some typical cases
        exemplars = [
            {'py': "normalName",
             'js': "normalName;\n"}
        ]
        # Some problem cases
        tykes = [
            {'py': "variableName",
             'js': "variableName;\n"}  # Name containing "var" (should no longer return blank as of #4336)
        ]
        for case in exemplars + tykes:
            self.runTranspile(case['py'], case['js'])

    def test_if_statement(self):
        py = ("if True:\n    True")
        js = ("if (true) {\n    true;\n}\n")
        self.runTranspile(py, js)

    def test_print(self):
        py = ("print(True)")
        js = ("console.log(true);\n")
        self.runTranspile(py, js)

    def test_function(self):
        py = ("def fun(a):\n    print(a)")
        js = ("function fun(a) {\n    console.log(a);\n}\n")
        self.runTranspile(py, js)

    def test_status(self):
        py = "status = STOPPED"
        js = "status = PsychoJS.Status.STOPPED;\n"
        self.runTranspile(py, js)

    def test_substitutions(self):
        # Define some cases which should be handled
        cases = [
            {'py': "a.append(4)", 'js': "a.push(4);\n"},
            {'py': "a.index(2)", 'js': "util.index(a, 2);\n"},
            {'py': "a.count(2)", 'js': "util.count(a, 2);\n"},
            {'py': "a.lower()", 'js': "a.toLowerCase();\n"},
            {'py': "a.upper()", 'js': "a.toUpperCase();\n"},
            {'py': "a.extend([4, 5, 6])", 'js': "a.concat([4, 5, 6]);\n"},
        ]
        # Try each case
        for case in cases:
            self.runTranspile(case['py'], case['js'])


class Test_PY2JS_Compile:
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
