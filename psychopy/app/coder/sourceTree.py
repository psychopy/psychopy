import ast
from collections import deque


class GenericAbstractSyntaxTree(object):
    """Generic abstract syntax tree (AST) class.

    This is a base class for representing ASTs to be shown in the source tree
    sidebar in Coder view. The purpose of this class is to standardize the
    representation of ASTs of multiple languages. So they all appear the same
    to the interface which displays them, independent of the language.

    """
    def __init__(self, filePath, nodes=None):
        self.filePath = filePath
        self.nodes = {} if nodes is None else dict(nodes)
        self._ast = []

    # def walk(self):  # from http://kmkeen.com/python-trees/
    #     """Walk through all the nodes in the AST."""
    #     visited = set()
    #     to_crawl = deque([token])
    #     while to_crawl:
    #         current = to_crawl.popleft()
    #         if current in visited:
    #             continue
    #         visited.add(current)
    #         node_children = set(self.nodes[current])
    #         to_crawl.extend(node_children - visited)
    #     return list(visited)
    #
    # def addNode(self):
    #     """Add a node to the AST."""
    #     # walk through the object's nodes and add sub objects


class BaseObjectDef(object):
    """Base class for object definitions."""
    def __init__(self, parent, name, lineno, nodes=None):
        self.parent = parent
        self.name = name
        self.lineno = lineno
        self.nodes = [] if nodes is None else list(nodes)
        self.fqn = self.name  # fully-qualified name of object within file
        self._resolved = False

    def __hash__(self):
        return hash((self.name, self.lineno))

    def isResolved(self):
        """Check if this object's name has been resolved."""
        return self._resolved

    def resolve(self, cookie=None):
        """Walk through the node and resolve FQNs. This recursively sets the
        FQNs of all decedent nodes to be relative to this one.

        Parameters
        ----------
        cookie : str
            FQN of the calling object. This is used to keep track of where a
            node is relative to the root of the source tree.

        """
        # cookie leaves crumbs so we can keep track of where we've been
        cookie = cookie + '.' + self.name if cookie is not None else self.fqn
        visited = {}  # keep track of nodes we visit
        for node in self.nodes:
            if not node.isResolved():
                node.fqn = cookie + '.' + node.fqn
                visited[node.fqn] = node
                result = node.resolve(cookie)  # recursive call
                visited.update(result)  # add nodes we visited

        # finally, return the root object
        to_return = {self.fqn: self.getNodeNames()}
        to_return.update(visited)

        # mark this node as resolved
        self._resolved = True

        return to_return

    def getNodeNames(self):
        """Get the fully-qualified names of nodes in this object."""
        return [node.fqn for node in self.nodes]



class ClassDef(BaseObjectDef):
    """Class representing an ubound class definition in an AST."""
    def __init__(self, parent, name, lineno, nodes=None):
        super(ClassDef, self).__init__(parent, name, lineno, nodes=nodes)


class FunctionDef(BaseObjectDef):
    """Class representing a function definition in an AST."""
    def __init__(self, parent, name, lineno, nodes=None):
        super(FunctionDef, self).__init__(parent, name, lineno, nodes=nodes)


class MethodDef(FunctionDef):
    """Class representing a class method definition in an AST."""
    def __init__(self, parent, name, lineno, nodes=None):
        super(MethodDef, self).__init__(parent, name, lineno, nodes=nodes)


class AttributeDef(BaseObjectDef):
    """Class representing a class/module attribute definition in an AST."""
    def __init__(self, parent, name, lineno, nodes=None):
        super(AttributeDef, self).__init__(parent, name, lineno, nodes=nodes)


if __name__ == "__main__":
    pass