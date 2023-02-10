from psychopy.experiment.py2js_transpiler import translatePythonToJavaScript
import psychopy.experiment.py2js as py2js
from psychopy.experiment import Experiment
from psychopy.experiment.components.code import CodeComponent
from psychopy.experiment.routines import Routine


class TestTranspiler:

    def runTranspile(self, py, js):
        transpiledCode = translatePythonToJavaScript(py)
        assert (js == transpiledCode)

    def test_assignment(self):
        py = ("a = 1")
        js = ("var a;\na = 1;\n")
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
        js = "var status;\nstatus = PsychoJS.Status.STOPPED;\n"
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

    def test_var_defs(self):
        cases = [
            # Docstring at line 1
            {'py': (
"""'''
Docstring at line 1
'''
continueRoutine = False"""
            ),
                'var': False},
            # Comment at line 1
            {'py': (
"""# Comment at line 1
continueRoutine = False"""
            ),
             'var': False},
            # PsychoPy keyword (just one)
            {'py': (
"""continueRoutine = False"""
            ),
                'var': False},
            # PsychoPy keywords
            {'py': (
"""continueRoutine = False
expInfo = {}"""
            ),
                'var': False},
            # Numpy keywords
            {'py': (
"""sin = None
pi = 3.14"""
            ),
                'var': False},
            # Package names
            {'py': (
"""visual = psychopy.visual
np = numpy"""
            ),
                'var': False},
            # Component name
            {'py': (
"""testComponent = None"""
            ),
                'var': False},
            # Routine name
            {'py': (
"""testRoutine = None"""
            ),
                'var': False},
            # Valid var def
            {'py': (
"""newVariable = 0"""
            ),
                'var': True},
            # One valid one invalid
            {'py': (
"""continueRoutine = False
newVariable = {}"""
            ),
                'var': True},
            # Valriable from Code component
            {'py': (
"""extantVariable = 0"""
            ),
                'var': True},
        ]

        # Setup experiment
        exp = Experiment()
        rt = Routine("testRoutine", exp)
        comp = CodeComponent(exp, parentName="testRoutine", name="testComponent", beforeExp="extantVariable = 1")
        rt.addComponent(comp)
        exp.addRoutine("testRoutine", rt)
        exp.flow.addRoutine(rt, 0)
        # Add comp and routine names to namespace (this is usually done from Builder
        exp.namespace.add("testRoutine")
        exp.namespace.add("testComponent")
        # Run cases
        for case in cases:
            # Translate with exp namespace
            jsCode = py2js.translatePythonToJavaScript(case['py'], namespace=exp.namespace.all)
            # Check whether var statements are present
            if case['var']:
                assert "var " in jsCode, (
                    f"Could not find desired var def in:\n"
                    f"{jsCode}"
                )
            else:
                assert "var " not in jsCode, (
                    f"Found undesired var def in:\n"
                    f"{jsCode}"
                )


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
