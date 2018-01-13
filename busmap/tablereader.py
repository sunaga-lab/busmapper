# -*- coding: utf-8 -*-
import re
from busmap.datastruct import *
import json

tablereader_debug_enabled = False

class TableGenerator:

    def generate_table(self):
        raise NotImplementedError()


class TableList:

    def __init__(self, tables):
        self.tables = tables

    def __getitem__(self, item):
        return self.tables[item]

    def save(self, fn):
        saving_data = {
            'format': 'table_list',
            'body': [t.to_dict() for t in self.tables]
        }
        with open(fn, 'w') as fp:
            json.dump(saving_data, fp)

    @classmethod
    def load(cls, fn):
        with open(fn, 'r') as fp:
            loading_data = json.load(fp)
            if loading_data['format'] == 'table_list':
                return TableList([Table.from_dict(t_dict) for t_dict in loading_data['body']])
            elif loading_data['format'] == 'table':
                return TableList([Table.from_dict(loading_data['body'])])
            else:
                raise Exception()

class Table:

    AXIS_ROW  = 'row'
    AXIS_COLUMN = 'column'

    def __init__(self):
        self.table_data = None
        self.columns = None
        self.rows = None
        self.table_attrs = {}

    def save(self, fn):
        saving_data = {
            'format': 'table',
            'body': self.to_dict()
        }
        with open(fn, 'w') as fp:
            json.dump(saving_data, fp)

    @classmethod
    def load(cls, fn):
        with open(fn, 'r') as fp:
            loading_data = json.load(fp)
            assert loading_data['format'] == 'table'
            return Table.from_dict(loading_data['body'])

    def to_dict(self):
        return {
            'table_data': self.table_data,
            'columns': self.columns,
            'rows': self.rows,
            'table_attrs': self.table_attrs
        }

    @classmethod
    def from_dict(cls, d):
        return cls.from_data(**d)

    @staticmethod
    def from_data(*idx, **kw):
        t = Table()
        t.set_data(*idx, **kw)
        return t

    def set_data(self, table_data, columns=None, rows=None, head_column_index=0, head_row_index=0, table_attrs=None):
        self.table_data = table_data
        if columns is None:
            self.columns = self.table_data[head_row_index]
        else:
            self.columns = columns
        if rows is None:
            self.rows = [(row[head_column_index] if len(row) > 0 else None) for row in self.table_data]
        else:
            self.rows = rows
        self.table_attrs = table_attrs or {}

    @classmethod
    def concat_vert(cls, table1, table2):
        result = Table()
        result.set_data(
            table1.table_data + table2.table_data,
            columns=table1.columns,
            rows=table1.rows + table2.rows
        )
        return result

    def concat_vert_with(self, table2):
        return self.concat_vert(self, table2)

    def num_cells(self, axis):
        return getattr(self, 'num_{0}s'.format(axis))()

    def num_rows(self):
        return len(self.rows)

    def num_columns(self):
        return len(self.columns)

    def get_value_from_index(self, column, row):
        try:
            return self.table_data[row][column]
        except IndexError:
            return None

    def get_value(self, column, row):
        colidx = column if isinstance(column, int) else self.col_index(column)
        rowidx = row if isinstance(row, int) else self.row_index(row)
        return self.get_value_from_index(colidx, rowidx)

    def col_index(self, colname):
        try:
            return self.columns.index(normalize_text(colname))
        except ValueError:
            return None

    def row_index(self, rowname):
        try:
            return self.rows.index(normalize_text(rowname))
        except ValueError:
            return None

    def index_from_head(self, axis, name):
        return self.col_index(name) if axis == self.AXIS_COLUMN else self.row_index(name)

    def to_csv(self):
        result = []
        result.append('# Columns:' + ','.join(str(col) for col in self.columns))
        result.append('# Rows:' + ','.join(str(row) for row in self.rows))
        result.extend(','.join(line) for line in self.table_data)
        return '\n'.join(result)

    def set_table_attr(self, name, value):
        self.table_attrs[name] = value

    def get_table_attr(self, name, default_value=None):
        return self.table_attrs.get(name, default_value)

    def with_table_atts(self, **attrs):
        self.table_attrs.update(**attrs)
        return self

def table_to_text(table, divider=','):
    result = []
    for row in range(0, table.num_rows()):
        cells = []
        for col in range(0, table.num_columns()):
            val = str(table.get_value(col=col, row=row))
            cells.append(val)

        result.append(divider.join(cells))

    return '\n'.join(result)

reTime = re.compile('[0-9]{1,2}:[0-9]{1,2}')
def is_time_str(text):
    if reTime.match(text):
        return True
    return False


def table_to_fact(db, table, line, tablename="", day_options=None, invert_axis=False):
    if not day_options:
        day_options = []

    if isinstance(table, TableGenerator):
        table = table.generate_table()

    if tablereader_debug_enabled:
        print("[Table CSV of {0}:{1}]".format(line.name, tablename))
        print(table.to_csv())

    (sta_axis, car_axis) = (Table.AXIS_ROW, Table.AXIS_COLUMN) if invert_axis else (Table.AXIS_COLUMN, Table.AXIS_ROW)

    station_idx = []
    for sta in line.get_stations():
        for label in [sta.name] + sta.altnames:
            station_idx.append((sta.name, 'stop', table.index_from_head(sta_axis, label)))
            station_idx.append((sta.name, 'leave', table.index_from_head(sta_axis, label+'発')))
            station_idx.append((sta.name, 'arrive', table.index_from_head(sta_axis, label+'着')))

    for car_num in range(table.num_cells(axis=car_axis)):
        car_name_arr = filter(lambda item: (item not in ['', None]), [line.name, tablename, car_num] + sorted(day_options))
        car_name = '-'.join(str(v) for v in car_name_arr)

        car = Car(name=car_name, linename=line.name)
        db.add(car)
        for sta, dtype, sta_index in station_idx:
            if sta_index is None:
                continue
            val = table.get_value(**{
                sta_axis: sta_index,
                car_axis: car_num
            })
            if val is None:
                continue
            if is_time_str(val):
                car.add_event(CarEvent(time=val, event=dtype, station=sta))


