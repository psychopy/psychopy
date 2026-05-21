from pathlib import Path
import ast
import json
import importlib


class TranslationExtractor(ast.NodeVisitor):
    """
    Visitor which cans an ast.Tree object for calls to `_translate`
    """
    def __init__(self):
        # initialise subclass
        ast.NodeVisitor.__init__(self)
        # create keys array
        self.keys = set()

    def visit_Call(self, node):
        # skip irrelevant calls
        if getattr(node.func, "id", None) != "_translate":
            return
        # skip calls with no args
        if len(node.args) == 0:
            return
        # skip calls where arg has no hardcoded value
        if not hasattr(node.args[0], "value"):
            return
        # store value in keys
        self.keys.add(node.args[0].value)


def extract(module="psychopy.experiment", save=True):
    keys = set()
    # get location of module
    folder = Path(importlib.import_module(module).__file__).parent
    # iterate through files in module
    for file in folder.glob("**/*.py"):
        # parse as ast
        tree = ast.parse(file.read_text(), filename=file.name)
        # look for _translate calls
        extractor = TranslationExtractor()
        extractor.visit(tree)
        # get keys
        keys.update(extractor.keys)
    
    # save new keys if requested
    if save:
        # get locales folder
        folder = Path(__file__).parent / "locales"
        # iterate through each JSON file
        for file in folder.glob("*.json"):
            # load existing
            with file.open() as f:
                translations = json.load(f)
            # add any untranslated keys
            translations = dict.fromkeys(keys, "") | translations
            # save
            with file.open("wt") as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)
    
    return keys


if __name__ == "__main__":
    extract()