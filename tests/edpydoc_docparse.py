from epydoc import docparser, apidoc


def parse(filename=None, name=None):
    d = docparser.parse_docs(filename, name)
    
    isinstance(d, apidoc.APIDoc)
    tokens = {}
    
    print 'Imports:'
    for imp in d.imports:
        modName = str(imp)
        outerContainer = modName.split('.')[-1]
        tokens[modName] = docparser.parse_docs(name = modName)
        tokens[outerContainer] = tokens[modName]
    print tokens
    
    print '\nVariables:'
    vars=d.variables
    for varName in vars:
        print varName, vars[varName].docstring
        if hasattr(vars[varName].value, 'parse_repr'):        
            print '\t', vars[varName].value.parse_repr
            print '\t', vars[varName].value.docstring

parse('/Users/jwp/Code/PsychoPy/svn/trunk/psychopy/demos/face_jpg.py')