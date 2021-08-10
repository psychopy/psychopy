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
