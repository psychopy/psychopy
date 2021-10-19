from psychopy.experiment.py2js_transpiler import translatePythonToJavaScript


class TestTranspiler:

    def runTranspile(self, py, js):
        transpiledCode = translatePythonToJavaScript(py)
        assert (js == transpiledCode)

    def test_assignment(self):
        py = ("a = 1")
        js = ("a = 1;\n")
        self.runTranspile(py, js)

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
