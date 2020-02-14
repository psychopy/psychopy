from __future__ import absolute_import, print_function
from collections import deque, OrderedDict

import wx
import wx.stc
import wx.richtext

try:
    from wx import aui
except Exception:
    import wx.lib.agw.aui as aui  # some versions of phoenix

import os
import ast

_treeImgList = _treeGfx = None


def _initGraphics(rc):
    """Load graphics needed by the source browser."""
    global _treeImgList, _treeGfx

    _treeImgList = wx.ImageList(16, 16)
    _treeGfx = {
        'treeClass': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'coderclass16.png'), wx.BITMAP_TYPE_PNG)),
        'treeFunc': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'coderfunc16.png'), wx.BITMAP_TYPE_PNG)),
        'treeAttr': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'codervar16.png'), wx.BITMAP_TYPE_PNG)),
        'treePyModule': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'coderpython16.png'), wx.BITMAP_TYPE_PNG)),
        'treeImport': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'coderimport16.png'), wx.BITMAP_TYPE_PNG)),
        'treeFolderClosed': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'folder16.png'), wx.BITMAP_TYPE_PNG)),
        'treeWindowClass': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'monitor16.png'), wx.BITMAP_TYPE_PNG)),
        'treeFolderOpened': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'folder-open16.png'), wx.BITMAP_TYPE_PNG)),
        'treeImageStimClass': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'fileimage16.png'), wx.BITMAP_TYPE_PNG))}


class SourceTreePanel(wx.Panel):
    """Panel for the source tree browser."""
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.coder = frame

        # get graphics for toolbars and tree items
        rc = self.coder.paths['resources']
        _initGraphics(rc)

        self.SetDoubleBuffered(True)
        # create the source tree control
        self.treeId = wx.NewIdRef()
        self.srcTree = wx.TreeCtrl(
            self,
            self.treeId,
            pos=(0, 0),
            size=wx.Size(300, 300),
            style=wx.TR_HAS_BUTTONS)
        self.srcTree.SetImageList(_treeImgList)

        # do layout
        szr = wx.BoxSizer(wx.VERTICAL)
        szr.Add(self.srcTree, flag=wx.EXPAND, proportion=1)
        self.SetSizer(szr)

        # bind events
        self.Bind(
            wx.EVT_TREE_ITEM_ACTIVATED, self.OnTreeItemActivate, self.srcTree)

    def OnTreeItemActivate(self, evt=None):
        """When a tree item is clicked on."""
        if evt is None:
            evt.Skip()

        item = evt.GetItem()
        lineno = self.srcTree.GetItemData(item)
        if lineno is not None:
            self.coder.currentDoc.GotoLine(lineno - 1)
        else:
            self.srcTree.Expand(item)

    def GetScrollVert(self):
        """Keep track of where we scrolled for the current document. This keeps
        the tree viewer from moving back to the top when returning to a
        document, which may be jarring for users."""
        return self.srcTree.GetScrollPos(wx.VERTICAL)

    def createItems(self):
        """Walk through all the nodes in the AST and create tree items.
        """
        if self.coder.currentDoc.ast is None:
            return

        currentDoc = self.coder.currentDoc

        allNodes = []
        self.srcTree.Freeze()
        self.srcTree.DeleteAllItems()
        self.coder.currentDoc.ast.realize(self.srcTree)
        for i in self.coder.currentDoc.ast.nodes:
            visited = list()
            to_crawl = deque([i.fqn])
            while to_crawl:
                current = to_crawl.popleft()
                if current in visited:
                    continue
                visited.append(current)
                currentDoc.ast._objects[current].realize(self.srcTree)
                node_children = [i.fqn for i in
                                 currentDoc.ast._objects[current].nodes]

                # BFS for classes
                if isinstance(currentDoc.ast._objects[current], ClassDef):
                    # needs reverse
                    to_crawl.extendleft(
                        reversed(
                            [i for i in node_children if i not in visited]))
                else:
                    to_crawl.extend(
                        [i for i in node_children if i not in visited])

        self.srcTree.ExpandAll()
        self.srcTree.Thaw()

    def updatePySourceTree(self):
        """Update the source tree using the parsed AST from the active document.

        This assumes that we're editing a Python file.

        """
        self.srcTree.Freeze()
        self.srcTree.DeleteAllItems()
        root = self.srcTree.AddRoot(self.coder.currentDoc.filename)
        self.srcTree.SetItemImage(
            root, self._treeGfx['treePyModule'], wx.TreeItemIcon_Normal)
        self.srcTree.SetItemData(root, None)

        # keep track of imports
        importIdx = self.srcTree.AppendItem(root, '<imports>')
        self.srcTree.SetItemImage(
            importIdx,
            self._treeGfx['treeFolderClosed'],
            wx.TreeItemIcon_Normal)
        self.srcTree.SetItemImage(
            importIdx,
            self._treeGfx['treeFolderOpened'],
            wx.TreeItemIcon_Expanded)
        self.srcTree.SetItemData(importIdx, None)

        for node in self.coder.currentDoc.ast:
            if isinstance(node, ast.ClassDef):
                itemIdx = self.srcTree.AppendItem(root, node.name)
                self.srcTree.SetItemImage(
                    itemIdx, self._treeGfx['treeClass'], wx.TreeItemIcon_Normal)
                self.srcTree.SetItemData(itemIdx, node.lineno)
                for j in [n for n in node.body if isinstance(n, ast.FunctionDef)]:
                    childIdx = self.srcTree.AppendItem(itemIdx, j.name)
                    self.srcTree.SetItemImage(
                        childIdx, self._treeGfx['treeFunc'], wx.TreeItemIcon_Normal)
                    self.srcTree.SetItemData(childIdx, j.lineno)

                self.srcTree.Expand(itemIdx)

            elif isinstance(node, ast.FunctionDef):
                itemIdx = self.srcTree.AppendItem(root, node.name)
                self.srcTree.SetItemImage(
                    itemIdx, self._treeGfx['treeFunc'], wx.TreeItemIcon_Normal)
                self.srcTree.SetItemData(itemIdx, node.lineno)

            elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                itemIdx = self.srcTree.AppendItem(root, node.targets[0].id)
                self.srcTree.SetItemImage(
                    itemIdx,
                    self._treeGfx['treeAttr'],
                    wx.TreeItemIcon_Normal)
                self.srcTree.SetItemData(itemIdx, node.lineno)

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    itemIdx = self.srcTree.AppendItem(importIdx, alias.name)
                    self.srcTree.SetItemImage(
                        itemIdx,
                        self._treeGfx['treeImport'],
                        wx.TreeItemIcon_Normal)
                    self.srcTree.SetItemData(itemIdx, node.lineno)

            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                # look for an existing tree node with the same module name
                child, cookie = self.srcTree.GetFirstChild(importIdx)
                while child.IsOk():
                    folderName = self.srcTree.GetItemText(child)
                    if folderName == node.module:
                        fromImportIdx = child
                        break
                    child = self.srcTree.GetNextSibling(child)
                else:
                    fromImportIdx = self.srcTree.AppendItem(
                        importIdx, node.module)

                self.srcTree.SetItemImage(
                    fromImportIdx,
                    self._treeGfx['treeFolderClosed'],
                    wx.TreeItemIcon_Normal)
                self.srcTree.SetItemImage(
                    fromImportIdx,
                    self._treeGfx['treeFolderOpened'],
                    wx.TreeItemIcon_Expanded)
                self.srcTree.SetItemData(fromImportIdx, None)
                for alias in node.names:
                    itemIdx = self.srcTree.AppendItem(fromImportIdx, alias.name)
                    self.srcTree.SetItemImage(
                        itemIdx,
                        self._treeGfx['treeImport'],
                        wx.TreeItemIcon_Normal)
                    self.srcTree.SetItemData(itemIdx, node.lineno)

        self.srcTree.Expand(root)
        self.srcTree.Thaw()

    def updateSourceTree(self):
        """Update the source tree using the parsed AST from the active document.
        """
        lexer = self.coder.currentDoc.GetLexer()
        if lexer == wx.stc.STC_LEX_PYTHON:
            self.createItems()


class GenericAST(object):
    """Class representing the root of the AST."""
    def __init__(self, name, nodes=None):
        self.name = name
        self.nodes = [] if nodes is None else list(nodes)
        self._objects = None
        self.treeIdx = None

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
        cookie = '' if cookie is not None else cookie
        visited = OrderedDict()  # keep track of nodes we visit
        for node in self.nodes:
            if not node.isResolved():
                visited[node.fqn] = node
                result = node.resolve(cookie)  # recursive call
                visited.update(result)  # add nodes we visited

        self._objects = visited

    def realize(self, treeCtrl=None):
        """Realize a tree item from this node."""
        if treeCtrl is None:
            return

        self.treeIdx = treeCtrl.AddRoot(self.name)
        treeCtrl.SetItemImage(
            self.treeIdx, _treeGfx['treePyModule'], wx.TreeItemIcon_Normal)
        treeCtrl.SetItemData(self.treeIdx, None)

    @staticmethod
    def parsePyScript(src, rootName='<unknown>'):
        """Parse a Python script. Uses the `ast` module to tokenize the file.

        Parameters
        ----------
        scr : str
            Python source code to parse.
        rootName : str
            Root name to use for the source tree. Usually the file name or
            path.

        Returns
        -------
        GenericAbstractSyntaxTree or None
            Source code tree. If `None`, a syntax error was encountered that
            halted the `ast` parser.

        """
        try:
            fullast = ast.parse(src)
        except (SyntaxError, IndentationError):
            return None

        root = GenericAST(rootName)

        def getObjectDefs(astNode, snowball=None):
            """Function converts objects in the Python AST to generic ones. This
            is called recursively on nested objects.
            """
            foundNodes = []
            snowball = [] if snowball is None else snowball

            for node in astNode.body:
                objDef = None

                if isinstance(node, ast.ClassDef):
                    objDef = ClassDef(snowball, node.name, node.lineno)
                elif isinstance(node, ast.FunctionDef):
                    if isinstance(snowball, ClassDef):
                        objDef = MethodDef(snowball, node.name, node.lineno)
                    else:
                        objDef = FunctionDef(snowball, node.name, node.lineno)
                elif isinstance(node, ast.Assign) and \
                        isinstance(node.targets[0], ast.Name):
                    objDef = AttributeDef(
                        snowball,
                        node.targets[0].id,
                        node.lineno)
                    # psychopy related object, give custom icon
                    if hasattr(node.value, 'func'):
                        if isinstance(node.value.func, ast.Attribute):
                            if node.value.func.attr == 'Window':
                                objDef.style = 'treeWindowClass'
                            elif node.value.func.attr == 'ImageStim':
                                objDef.style = 'treeImageStimClass'

                if objDef is not None:
                    if not isinstance(objDef, AttributeDef):
                        getObjectDefs(node, objDef)

                    foundNodes.append(objDef)

            snowball.nodes.extend(foundNodes)

            return snowball

        to_return = getObjectDefs(fullast, root)
        to_return.resolve()

        return to_return



class BaseObjectDef(object):
    """Base class for object definitions."""
    def __init__(self, parent, name, lineno, nodes=None):
        self.parent = parent
        self.name = name
        self.lineno = lineno
        self.nodes = [] if nodes is None else list(nodes)
        self.fqn = self.name  # fully-qualified name of object within file
        self._resolved = False
        self.treeIdx = None

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
        visited = OrderedDict()  # keep track of nodes we visit
        for node in self.nodes:
            if not node.isResolved():
                node.fqn = cookie + '.' + node.fqn
                visited[node.fqn] = node
                result = node.resolve(cookie)  # recursive call
                visited.update(result)  # add nodes we visited

        # finally, return the root object
        to_return = OrderedDict([(self.fqn, self)])
        to_return.update(visited)

        # mark this node as resolved
        self._resolved = True

        return to_return

    def realize(self, treeCtrl):
        """Realize a tree item from this node."""
        self.treeIdx = treeCtrl.AppendItem(self.parent.treeIdx, self.name)
        treeCtrl.SetItemImage(
            self.treeIdx, _treeGfx['treePyModule'], wx.TreeItemIcon_Normal)
        treeCtrl.SetItemData(self.treeIdx, None)



class ClassDef(BaseObjectDef):
    """Class representing an ubound class definition in an AST."""
    def __init__(self, parent, name, lineno, nodes=None):
        super(ClassDef, self).__init__(parent, name, lineno, nodes=nodes)

    def realize(self, treeCtrl):
        """Realize a tree item from this node."""
        self.treeIdx = treeCtrl.AppendItem(self.parent.treeIdx, self.name)
        treeCtrl.SetItemImage(
            self.treeIdx, _treeGfx['treeClass'], wx.TreeItemIcon_Normal)
        treeCtrl.SetItemData(self.treeIdx, self.lineno)


class FunctionDef(BaseObjectDef):
    """Class representing a function definition in an AST."""
    def __init__(self, parent, name, lineno, nodes=None):
        super(FunctionDef, self).__init__(parent, name, lineno, nodes=nodes)

    def realize(self, treeCtrl):
        """Realize a tree item from this node."""
        self.treeIdx = treeCtrl.AppendItem(self.parent.treeIdx, self.name)
        treeCtrl.SetItemImage(
            self.treeIdx, _treeGfx['treeFunc'], wx.TreeItemIcon_Normal)
        treeCtrl.SetItemData(self.treeIdx, self.lineno)


class MethodDef(FunctionDef):
    """Class representing a class method definition in an AST."""
    def __init__(self, parent, name, lineno, nodes=None):
        super(MethodDef, self).__init__(parent, name, lineno, nodes=nodes)


class AttributeDef(BaseObjectDef):
    """Class representing a class/module attribute definition in an AST."""
    def __init__(self, parent, name, lineno, nodes=None, style=None):
        super(AttributeDef, self).__init__(parent, name, lineno, nodes=nodes)
        self.style = 'treeAttr' if style is None else style

    def realize(self, treeCtrl):
        """Realize a tree item from this node."""
        self.treeIdx = treeCtrl.AppendItem(self.parent.treeIdx, self.name)
        treeCtrl.SetItemImage(
            self.treeIdx, _treeGfx[self.style], wx.TreeItemIcon_Normal)
        treeCtrl.SetItemData(self.treeIdx, self.lineno)


#
# for node in self.coder.currentDoc.ast:
#     if isinstance(node, ast.ClassDef):
#         itemIdx = self.srcTree.AppendItem(root, node.name)
#         self.srcTree.SetItemImage(
#             itemIdx, self._treeGfx['treeClass'], wx.TreeItemIcon_Normal)
#         self.srcTree.SetItemData(itemIdx, node.lineno)
#         for j in [n for n in node.body if isinstance(n, ast.FunctionDef)]:
#             childIdx = self.srcTree.AppendItem(itemIdx, j.name)
#             self.srcTree.SetItemImage(
#                 childIdx, self._treeGfx['treeFunc'], wx.TreeItemIcon_Normal)
#             self.srcTree.SetItemData(childIdx, j.lineno)
#
#         self.srcTree.Expand(itemIdx)
#
#     elif isinstance(node, ast.FunctionDef):
#         itemIdx = self.srcTree.AppendItem(root, node.name)
#         self.srcTree.SetItemImage(
#             itemIdx, self._treeGfx['treeFunc'], wx.TreeItemIcon_Normal)
#         self.srcTree.SetItemData(itemIdx, node.lineno)
#
#     elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
#         itemIdx = self.srcTree.AppendItem(root, node.targets[0].id)
#         self.srcTree.SetItemImage(
#             itemIdx,
#             self._treeGfx['treeAttr'],
#             wx.TreeItemIcon_Normal)
#         self.srcTree.SetItemData(itemIdx, node.lineno)
#
#     elif isinstance(node, ast.Import):
#         for alias in node.names:
#             itemIdx = self.srcTree.AppendItem(importIdx, alias.name)
#             self.srcTree.SetItemImage(
#                 itemIdx,
#                 self._treeGfx['treeImport'],
#                 wx.TreeItemIcon_Normal)
#             self.srcTree.SetItemData(itemIdx, node.lineno)
#
#     elif isinstance(node, ast.ImportFrom):
#         if node.module is None:
#             continue
#         # look for an existing tree node with the same module name
#         child, cookie = self.srcTree.GetFirstChild(importIdx)
#         while child.IsOk():
#             folderName = self.srcTree.GetItemText(child)
#             if folderName == node.module:
#                 fromImportIdx = child
#                 break
#             child = self.srcTree.GetNextSibling(child)
#         else:
#             fromImportIdx = self.srcTree.AppendItem(
#                 importIdx, node.module)


