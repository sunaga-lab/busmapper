# -*- coding: utf-8 -*-
import re
from busmap.datastruct import *

class Table:

    def __init__(self):
        pass

    def num_rows(self):
        raise NotImplementedError()

    def num_columns(self):
        raise NotImplementedError()

    def col_index(self, colname):
        raise NotImplementedError()

    def row_index(self, rowname):
        raise NotImplementedError()

    def get_value_from_index(self, colidx, rowidx):
        raise NotImplementedError()

    def get_value(self, col, row):
        colidx = col if isinstance(col, int) else self.col_index(col)
        rowidx = row if isinstance(row, int) else self.row_index(row)
        return self.get_value_from_index(colidx, rowidx)


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


def table_to_fact(db, table, line, tablename="", day_options=None):
    if not day_options:
        day_options = []

    station_colidx = []
    for sta in line.get_stations():
        for label in [sta.name] + sta.altnames:
            station_colidx.append((sta.name, 'stop', table.col_index(label)))
            station_colidx.append((sta.name, 'leave', table.col_index(label+'発')))
            station_colidx.append((sta.name, 'arrive', table.col_index(label+'着')))

    for rowid in range(table.num_rows()):
        car_name_arr = filter(lambda item: item, [line.name, tablename, rowid] + sorted(day_options))
        car_name = '-'.join(str(v) for v in car_name_arr)

        car = Car(name=car_name, linename=line.name)
        db.add(car)
        for sta, dtype, colid in station_colidx:
            if colid is None:
                continue
            val = table.get_value(row=rowid, col=colid)
            if val is None:
                continue
            if is_time_str(val):
                car.add_event(CarEvent(time=val, event=dtype, station=sta))


