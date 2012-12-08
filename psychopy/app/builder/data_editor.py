'''
Module contains editor for conditions data.
'''

from psychopy import data_import
import json
import wx.grid
import collections
import cPickle as pickle
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
    
    def __init__(self, parent, message_sink):
        super(ConditionsGrid, self).__init__(parent)
        self.message_sink = message_sink
        self.data = None
        self.CreateGrid(0, 0)
        self.file_new()
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.cell_change)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.select_cell)
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.label_options)

    def get_all_selected_cells(self):
        """
        Get cells from all possibilities of selection.
        """
        #all rows
        for row_pos in self.GetSelectedRows():
            for col_pos in range(self.GetNumberCols()):
                yield (row_pos, col_pos)
        #all columns
        for col_pos in self.GetSelectedCols():
            for row_pos in range(self.GetNumberRows()):
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

    def get_selected_rectangle(self):
        """
        Get selected cells in a rectangular shape.
        """
        cells = set(self.get_all_selected_cells())
        if len(cells):
            r1 = self.GetNumberRows()
            c1 = self.GetNumberCols()
            r2 = 0
            c2 = 0
            for row_pos, col_pos in cells:
                r1 = min(r1, row_pos)
                r2 = max(r2, row_pos)
                c1 = min(c1, col_pos)
                c2 = max(c2, col_pos)
            if len(cells) == (c2 - c1 + 1) * (r2 - r1 + 1):
                return ((r1, c1), (r2, c2))
            else:
                return None
        else:
            selected = (self.GetGridCursorRow(), self.GetGridCursorCol())
            return (selected, selected)
    
    def command_copy(self):
        copy_range = self.get_selected_rectangle()
        if copy_range:
            (r1, c1), (r2, c2) = copy_range
            selection_rows = [[self.GetCellValue(row_pos, col_pos) for col_pos in range(c1, c2 + 1)] for row_pos in range(r1, r2 + 1)]
            selection_data = wx.CustomDataObject(wx.CustomDataFormat("grid"))
            selection_data.SetData(pickle.dumps(selection_rows))
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(selection_data)
                wx.TheClipboard.Close()
        return copy_range
    
    def command_cut(self):
        clear_range = self.command_copy()
        if clear_range:
            (r1, c1), (r2, c2) = clear_range
            for row_pos in range(r1, r2 + 1):
                for col_pos in range(c1, c2 + 1):
                    self.SetCellValue(row_pos, col_pos, "")
    
    def command_paste(self):
        if wx.TheClipboard.Open():
            if wx.TheClipboard.IsSupported(wx.CustomDataFormat("grid")):
                data_object = wx.CustomDataObject(wx.CustomDataFormat("grid"))
                wx.TheClipboard.GetData(data_object)
                pasted_rows = pickle.loads(data_object.GetData())
                base_row, base_col = self.GetGridCursorRow(), self.GetGridCursorCol()
                for row_pos, row in enumerate(pasted_rows):
                    for col_pos, cell in enumerate(row):
                        self.SetCellValue(base_row + row_pos, base_col + col_pos, cell)
            wx.TheClipboard.Close()
    
    def set_column_type(self, col_pos, column_type):
        self.column_types[col_pos] = column_type
        self.update_column_label(col_pos)
    
    def set_column_name(self, col_pos, column_name):
        self.column_names[col_pos] = column_name
        self.update_column_label(col_pos)

    def update_column_label(self, col_pos):
        column_type = self.column_types[col_pos]
        column_name = self.column_names[col_pos]
        self.SetColLabelValue(col_pos, column_name + ": " + column_type)

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
        for col_pos, header in enumerate(self.column_names):
            if not header:
                self.add_data_error((0, col_pos), "Empty header")
            elif not data_import.isValidVariableName(header)[0]:
                self.add_data_error((0, col_pos), "Invalid header")
            elif headers.has_key(header):
                self.add_data_error((0, col_pos), "Duplicate header")
            else:
                headers[header] = col_pos
        return self.column_names

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
        for row_pos in range(self.GetNumberRows()):
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
        
    def add_column(self, col_pos):
        self.InsertCols(col_pos)
        self.column_types.insert(col_pos, "text")
        self.column_names.insert(col_pos, "col_" + str(col_pos))
        for dirty_col_pos in range(col_pos, self.GetNumberCols()):
            self.update_column_label(dirty_col_pos)
    
    def remove_column(self, col_pos):
        self.DeleteCols(col_pos)
        del self.column_types[col_pos]
        del self.column_names[col_pos]
        for dirty_col_pos in range(col_pos, self.GetNumberCols()):
            self.update_column_label(dirty_col_pos)
    
    def add_column_handler(self, col_pos):
        def handler(event):
            self.add_column(col_pos + 1)
        return handler
    
    def remove_column_handler(self, col_pos):
        def handler(event):
            self.remove_column(col_pos)
        return handler
    
    def rename_column_handler(self, col_pos):
        def handler(hevent):
            dialog = wx.TextEntryDialog(self, "New column name:", "Rename column", self.column_names[col_pos])
            if dialog.ShowModal() == wx.ID_OK:
                self.set_column_name(col_pos, dialog.GetValue())
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
            ("remove column", self.remove_column_handler(col_pos)),
            ("rename", self.rename_column_handler(col_pos))
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
        """
        Fill grid cells with data.
        """
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
        self.InsertRows(numRows=len(rows))
        for col_pos in range(row_len):
            column_type = detect_column_type(rows, col_pos)
            self.set_column_type(col_pos, column_type)
            self.set_column_name(col_pos, headers[col_pos])

        loader_dict = TypeLoaderDict()
        for row_pos in range(len(rows)):
            for col_pos in range(row_len):
                cell_value = loader_dict[self.column_types[col_pos]](rows[row_pos][col_pos])
                self.SetCellValue(row_pos, col_pos, cell_value)

    def file_new(self):
        self.DeleteCols(numCols=self.GetNumberCols())
        self.DeleteRows(numRows=self.GetNumberRows())
        self.InsertRows(numRows=5)
        self.data_errors = {}
        self.column_names = []
        self.column_types = []
        for col_pos in range(4):
            self.add_column(col_pos)


class ConditionsEditor(wx.Dialog):
    def __init__(self, parent, file_name=None):
        self.TOOLBAR_BUTTONS = [
            ("New", wx.ART_NEW, self.file_new), ("Open", wx.ART_FILE_OPEN, self.file_open),
            ("Save as", wx.ART_FILE_SAVE_AS, self.file_save_as), (), ("Cut", wx.ART_CUT, self.command_cut),
            ("Copy", wx.ART_COPY, self.command_copy), ("Paste", wx.ART_PASTE, self.command_paste),
            (), ("Product", wx.ART_MISSING_IMAGE, self.product)
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
        self.toolbar = wx.ToolBar(self)
        self.tool_ids = []
        for button in self.TOOLBAR_BUTTONS:
            if button == ():
                self.toolbar.AddSeparator()
            else:
                bitmap = wx.ArtProvider.GetBitmap(button[1], wx.ART_TOOLBAR)
                tool_id = self.toolbar.AddLabelTool(-1, button[0], bitmap, wx.NullBitmap, wx.ITEM_NORMAL).GetId()
                self.tool_ids.append(tool_id)
                self.Bind(wx.EVT_TOOL, button[2], id=tool_id)

        self.toolbar.Realize()
        #self.paste_timer = wx.Timer(self)
        #self.Bind(wx.EVT_TIMER, self.poll_clipboard, self.paste_timer)
        #self.paste_timer.Start(1500, wx.TIMER_CONTINUOUS)
    
    def poll_clipboard(self, event):
        paste_tool = self.toolbar.FindById(self.tool_ids[5]) # paste tool
        wx.TheClipboard.Close()
        if wx.TheClipboard.Open():
            paste_tool.Enable(wx.TheClipboard.IsSupported(wx.CustomDataFormat("grid")))
            print paste_tool.IsEnabled()
            wx.TheClipboard.Close()

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
        self.file_name = self.file_name or wx.SaveFileSelector("Save PKL file", "pkl", parent=self)
        if self.file_name:
            self.save_data_to_file()
            return True
        else:
            return False

    def file_new(self, event):
        self.file_name = None
        self.data_grid.file_new()

    def file_open(self, event):
        file_name = wx.LoadFileSelector("conditions file", "pkl", parent=self)
        if file_name:
            self.file_name = file_name
            self.load_data_from_file()

    def file_save_as(self, event):
        self.data_grid.validate_data()
        if not self.data_grid.data_errors:
            self.save_data_as()

    def product(self, event):
        """
        Calculate column-wise product of selected cells.
        """
        selection = self.data_grid.get_all_selected_cells()
        column_selection = collections.OrderedDict()
        processed = set()
        for (row_pos, col_pos) in selection:
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

    def command_copy(self, event):
        self.data_grid.command_copy()
    
    def command_paste(self, event):
        self.data_grid.command_paste()

    def command_cut(self, event):
        self.data_grid.command_cut()

    def onOK(self, event):
        self.data_grid.validate_data()
        if self.data_grid.data_errors:
            # TODO: show errors
            return
        else:
            if self.save_data_as():
                self.EndModal(wx.OK)
