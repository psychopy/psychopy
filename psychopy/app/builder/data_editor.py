'''
Module contains editor for conditions data.
'''

import os.path
from psychopy import data
import json
import wx.grid
import collections
import pickle
import itertools

class ConditionsValueError(Exception):
    pass

class TypeParserDict(collections.OrderedDict):
    @staticmethod
    def parse_cell_text(value):
        return value

    @staticmethod
    def parse_cell_number(value):
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                raise ConditionsValueError()

    @staticmethod
    def parse_cell_boolean(value):
        return bool(value)

    @staticmethod
    def parse_cell_json(value):
        try:
            return json.loads(value)
        except ValueError:
            raise ConditionsValueError()

    def __init__(self):
        super(TypeParserDict, self).__init__()
        self["text"] = self.parse_cell_text
        self["number"] = self.parse_cell_number
        self["boolean"] = self.parse_cell_boolean
        self["json"] = self.parse_cell_json

class TypeLoaderDict(dict):
    @staticmethod
    def load_text_number(value):
        return unicode(value)
    
    @staticmethod
    def load_boolean(value):
        return "1" if value else "0"
    
    @staticmethod
    def load_json(value):
        try:
            return json.dumps(value)
        except ValueError:
            return "null"
    
    def __init__(self):
        super(TypeLoaderDict, self).__init__()
        self["text"] = self.load_text_number
        self["number"] = self.load_text_number
        self["boolean"] = self.load_boolean
        self["json"] = self.load_json

class ConditionsGrid(wx.grid.Grid):
    ERROR_COLOR = wx.Color(0xFF, 0xCC, 0xCC)
    TYPE_PARSER_DICT = TypeParserDict()

    @staticmethod
    def column_name(col_pos):
        ret = chr(ord('A') + (col_pos % 26))
        col_pos = col_pos / 26
        while col_pos > 0:
            col_pos = col_pos - 1
            ret = chr(ord('A') + (col_pos % 26)) + ret
            col_pos = col_pos / 26
        return ret
    
    def __init__(self, parent, message_sink):
        super(ConditionsGrid, self).__init__(parent)
        self.message_sink = message_sink
        self.data = None
        self.data_errors = {}
        self.CreateGrid(5, 4)
        self.init_column_types()
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.cell_change)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.select_cell)
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.label_options)

    def get_all_selected_cells(self):
        """
        Get cell from all possibilities of selection.
        """
        #all rows
        for row_pos in self.GetSelectedRows():
            for col_pos in self.GetNumberCols():
                yield (row_pos, col_pos)
        #all columns
        for col_pos in self.GetSelectedCols():
            for row_pos in self.GetNumberRows():
                yield (row_pos, col_pos)
        #all blocks
        blocks = zip(self.GetSelectionBlockTopLeft(), self.GetSelectionBlockBottomRight())
        for ((row_top, col_left), (row_bottom, col_right)) in blocks:
            for row_pos in range(row_top, row_bottom + 1):
                for col_pos in range(col_left, col_right + 1):
                    yield (row_pos, col_pos)
        #all single cells
        for (row_pos, col_pos) in self.GetSelectedCells():
            yield (row_pos, col_pos)
        

    def init_column_types(self):
        self.column_types = {}
        for col_pos in range(4):
            self.set_column_type(col_pos, "text")
    
    def set_column_type(self, col_pos, column_type):
        self.column_types[col_pos] = column_type
        self.SetColLabelValue(col_pos, self.column_name(col_pos) + ": " + str(column_type))

    def grid_cell_to_data(self, row_pos, col_pos):
        cell_value = self.GetCellValue(row_pos, col_pos)
        col_type = self.column_types[col_pos]
        return self.TYPE_PARSER_DICT[col_type](cell_value)

    def is_column_nonempty(self, col_pos):
        """
        Check if there is a nonempty cell in the column.
        @pure
        """
        exists_nonempty = lambda a, x: a or self.GetCellValue(x, col_pos)
        return reduce(exists_nonempty, range(self.GetNumberRows()), False)

    def get_nonempty_columns(self):
        """
        Get numbers of nonempty columns in the grid.
        @pure
        """
        return filter(self.is_column_nonempty, range(self.GetNumberCols()))

    def validate_headers(self, columns):
        headers = {}
        header_list = []
        for col_pos in columns:
            header = self.GetCellValue(0, col_pos)
            if not header:
                self.add_data_error((0, col_pos), "Empty header")
            elif not data.isValidVariableName(header)[0]:
                self.add_data_error((0, col_pos), "Invalid header")
            elif headers.has_key(header):
                self.add_data_error((0, col_pos), "Duplicate header")
            else:
                headers[header] = col_pos
                header_list.append(header)
        return header_list

    def validate_row(self, columns, row_pos):
        row = []
        for col_pos in columns:
            try:
                row.append(self.grid_cell_to_data(row_pos, col_pos))
            except ConditionsValueError:
                self.add_data_error((row_pos, col_pos), "Cell value is not a valid " + self.column_types[col_pos])
        return row

    def is_row_empty(self, columns, row_pos):
        all_empty = lambda a, x: a and x == ""
        return reduce(all_empty, [self.GetCellValue(row_pos, col_pos) for col_pos in columns], True)

    def validate_rows(self, columns):
        rows = []
        for row_pos in range(1, self.GetNumberRows()):
            if self.is_row_empty(columns, row_pos):
                continue
            else:
                rows.append(self.validate_row(columns, row_pos))
        return rows

    def add_data_error(self, pos, message):
        self.data_errors[pos] = message
        self.SetCellBackgroundColour(pos[0], pos[1], self.ERROR_COLOR)
        self.Refresh()
    
    def remove_data_error(self, pos):
        if self.data_errors.has_key(pos):
            del self.data_errors[pos]
            self.SetCellBackgroundColour(pos[0], pos[1], "white")
            self.Refresh()
    
    def get_data_error(self, pos):
        return self.data_errors.get(pos)

    def validate_data(self):
        self.data_errors = {}
        columns = self.get_nonempty_columns()
        headers = self.validate_headers(columns)
        rows = self.validate_rows(columns)
        if self.data_errors:
            self.data = None
        else:
            self.data = [headers]
            self.data.extend(rows)

    def cell_change(self, event):
        self.remove_data_error((event.GetRow(), event.GetCol()))
        self.message_sink.SetLabel("")
    
    def select_cell(self, event):
        message = self.get_data_error((event.GetRow(), event.GetCol()))
        if message:
            self.message_sink.SetLabel(message)
        else:
            self.message_sink.SetLabel("")
        event.Skip()
        
    def add_column_handler(self, col_pos):
        def handler(event):
            self.InsertCols(col_pos + 1)
            for dirty_col_pos in range(self.GetNumberCols() - 1, col_pos + 1, -1):
                self.set_column_type(dirty_col_pos, self.column_types[dirty_col_pos - 1])
            self.set_column_type(col_pos + 1, "text")
        return handler
    
    def remove_column_handler(self, col_pos):
        def handler(event):
            self.DeleteCols(col_pos)
            del self.column_types[col_pos]
            # shift column types by 1
            for dirty_col_pos in range(col_pos, self.GetNumberCols()):
                self.set_column_type(dirty_col_pos, self.column_types[dirty_col_pos + 1])
        return handler

    def column_options(self, event):
        def type_name_handler(type_name):
            return lambda event: self.set_column_type(col_pos, type_name)
        col_pos = event.GetCol()
        menu = wx.Menu()
        items1 = [(type_name, type_name_handler(type_name))
            for type_name in self.TYPE_PARSER_DICT.keys()]
        items2 = [
            ("add column", self.add_column_handler(col_pos)),
            ("remove column", self.remove_column_handler(col_pos))
        ]
        for item in items1:
            item_id = menu.Append(-1, item[0]).GetId()
            menu.Bind(wx.EVT_MENU, item[1], id=item_id)
        menu.AppendSeparator()
        for item in items2:
            item_id = menu.Append(-1, item[0]).GetId()
            menu.Bind(wx.EVT_MENU, item[1], id=item_id)
        self.PopupMenu(menu)
        
    def row_options(self, event):
        row_pos = event.GetRow()
        items = [
            ("add row", lambda event: self.InsertRows(row_pos + 1)),
            ("remove row", lambda event: self.DeleteRows(row_pos))
        ]
        menu = wx.Menu()
        for item in items:
            item_id = menu.Append(-1, item[0]).GetId()
            menu.Bind(wx.EVT_MENU, item[1], id=item_id)
        self.PopupMenu(menu)

    def grid_options(self, event):
        items = [
            ("add row", lambda event: self.InsertRows(0)),
            ("add column", self.add_column_handler(-1))
        ]
        menu = wx.Menu()
        for item in items:
            item_id = menu.Append(-1, item[0]).GetId()
            menu.Bind(wx.EVT_MENU, item[1], id=item_id)
        self.PopupMenu(menu)

    def label_options(self, event):
        if (event.GetCol() > -1):
            self.column_options(event)
        elif (event.GetRow() > -1):
            self.row_options(event)
        else:
            self.grid_options(event)

    def get_data(self):
        return self.data
    
    def extract_headers(self, data):
        try:
            return [unicode(header) for header in list(data[0])]            
        except TypeError:
            self.message_sink.SetLabel("Invalid headers list")
            return []

    def extract_rows(self, data):
        rows = []
        for row in data[1:]:
            try:
                rows.append(list(row))
            except:
                self.message_sink.SetLabel("Invalid row")
                rows.append([])
        return rows

    def set_data(self, data):
        def pad_data(headers, rows, width):
            new_headers = [headers[i] if i < len(headers) else u"" for i in range(width)]
            new_rows = [[row[i] if i < len(row) else None for i in range(width)] for row in rows]
            return (new_headers, new_rows)
        
        def detect_text_column(rows, col_pos):
            for row in rows:
                if not (isinstance(row[col_pos], str) or isinstance(row[col_pos], unicode)):
                    return False
            return True
        
        def detect_number_column(rows, col_pos):
            for row in rows:
                if not (isinstance(row[col_pos], int) or isinstance(row[col_pos], float)):
                    return False
            return True
        
        def detect_boolean_column(rows, col_pos):
            for row in rows:
                if not isinstance(row[col_pos], bool):
                    return False
            return True
        
        def detect_column_type(rows, col_pos):
            if detect_text_column(rows, col_pos):
                return "text"
            elif detect_number_column(rows, col_pos):
                return "number"
            elif detect_boolean_column(rows, col_pos):
                return "boolean"
            else:
                return "json"
        
        # clear grid
        self.DeleteCols(numCols=self.GetNumberCols())
        self.DeleteRows(numRows=self.GetNumberRows())
        # extract data
        headers = self.extract_headers(data)
        rows = self.extract_rows(data)
        # pad rows & headers to max width
        row_len = reduce(lambda a, x: max(len(x), a), rows, len(headers))
        (headers, rows) = pad_data(headers, rows, row_len)
        # insert columns
        self.InsertCols(numCols=row_len)
        self.InsertRows(numRows=len(rows) + 1)
        for col_pos in range(row_len):
            column_type = detect_column_type(rows, col_pos)
            self.set_column_type(col_pos, column_type)
            self.SetCellValue(0, col_pos, headers[col_pos])

        loader_dict = TypeLoaderDict()
        for row_pos in range(len(rows)):
            for col_pos in range(row_len):
                cell_value = loader_dict[self.column_types[col_pos]](rows[row_pos][col_pos])
                self.SetCellValue(row_pos + 1, col_pos, cell_value)


class ConditionsEditor(wx.Dialog):
    def file_new(self, event):
        self.file_name = None
        self.data_grid.DeleteCols(numCols=self.data_grid.GetNumberCols())
        self.data_grid.DeleteRows(numRows=self.data_grid.GetNumberRows())
        self.data_grid.InsertCols(numCols=4)
        self.data_grid.InsertRows(numRows=5)
        self.data_grid.data_errors = {}
        for col_pos in range(4):
            self.data_grid.set_column_type(col_pos, "json")

    def file_open(self, event):
        file_name = wx.LoadFileSelector("conditions file", "pkl", parent=self)
        if file_name:
            self.file_name = file_name
            self.load_data_from_file()

    def file_save_as(self, event):
        self.save_data_as()

    def product(self, event):
        """
        Calculate column-wise product of selected cells.
        """
        selection = self.data_grid.get_all_selected_cells()
        column_selection = collections.OrderedDict()
        processed = set()
        for (row_pos, col_pos) in selection:
            if row_pos == 0:
                continue
            if (row_pos, col_pos) in processed:
                continue
            if not column_selection.has_key(col_pos):
                column_selection[col_pos] = [(row_pos, col_pos)]
            else:
                column_selection[col_pos].append((row_pos, col_pos))
            processed.add((row_pos, col_pos))
        product_size = reduce(lambda a, x: a * x, [len(column) for column in column_selection.values()], 1)
        tuples = itertools.product(*column_selection.values())
        row_pos = self.data_grid.GetNumberRows()
        self.data_grid.InsertRows(self.data_grid.GetNumberRows(), product_size)
        for pos_tuple in tuples:
            for (src_row_pos, col_pos) in pos_tuple:
                value = self.data_grid.GetCellValue(src_row_pos, col_pos)
                self.data_grid.SetCellValue(row_pos, col_pos, value)
            row_pos = row_pos + 1

    def __init__(self, parent, file_name=None):
        self.TOOLBAR_BUTTONS = [
            ("New", "filenew", self.file_new), ("Open", "fileopen", self.file_open),
            ("Save as", "filesave", self.file_save_as), (), ("Product", "product", self.product)
        ]
        super(ConditionsEditor, self).__init__(parent, title="Conditions editor", size=(600, 375))
        self.app = parent.app
        self.file_name = file_name
        self.create_toolbar()
        self.message_sink = wx.StaticText(self)
        self.data_grid = ConditionsGrid(self, self.message_sink)
        self.init_sizer()
        if self.file_name:
            self.load_data_from_file()

    def create_toolbar(self):
        resource_path = self.app.prefs.paths['resources']
        self.toolbar = wx.ToolBar(self)

        for button in self.TOOLBAR_BUTTONS:
            if button == ():
                self.toolbar.AddSeparator()
            else:
                bitmap_path = os.path.join(resource_path, button[1] + "32.png")
                bitmap = wx.Bitmap(bitmap_path)
                tool_id = self.toolbar.AddSimpleTool(-1, bitmap, button[0]).GetId()
                self.Bind(wx.EVT_TOOL, button[2], id=tool_id)

        self.toolbar.Realize()

    def init_sizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.toolbar, flag=wx.EXPAND)
        sizer.Add(self.data_grid, proportion=1, flag=wx.EXPAND)
        sizer.Add(self.message_sink, flag=wx.EXPAND | wx.ALL, border=8)
        sizer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), flag=wx.EXPAND | wx.ALL, border=8)
        self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
        self.SetSizer(sizer)

    def load_data_from_file(self):
        pickle_file = open(self.file_name, "r")
        self.data_grid.set_data(pickle.load(pickle_file))

    def save_data_to_file(self):
        pickle_file = open(self.file_name, "w")
        pickle.dump(self.data_grid.get_data(), pickle_file)
        pickle_file.close()

    def save_data_as(self):
        self.file_name = self.file_name or wx.SaveFileSelector("wat?", "pkl", parent=self)
        if self.file_name:
            self.save_data_to_file()
            return True
        else:
            return False

    def onOK(self, event):
        self.data_grid.validate_data()
        if self.data_grid.data_errors:
            self.data_grid
        else:
            if self.save_data_as():
                self.EndModal(wx.OK)
