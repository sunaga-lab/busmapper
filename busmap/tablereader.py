# -*- coding: utf-8 -*-
import re

class Table:

    def __init__(self):
        pass

    def num_rows(self):
        raise NotImplementedError()

    def num_columns(self):
        raise NotImplementedError()

    def get_value(self, col, row):
        raise NotImplementedError()

    def col_index(self, colname):
        raise NotImplementedError()

    def row_index(self, rowname):
        raise NotImplementedError()


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


def table_to_fact(table, line_data):
    station_def = []
    car_def = []
    car_stops = []

    station_colidx_map = {}
    for sta in line_data.get_stations():
        station_def.append("data_station('{0}').".format(sta.name))
        for label in [sta.name] + sta.alternative_names:
            station_colidx_map[(sta.name, 'stop')] = table.col_index(label)
            station_colidx_map[(sta.name, 'leave')] = table.col_index(label+'発')
            station_colidx_map[(sta.name, 'arrive')] = table.col_index(label+'着')

    for rowid in range(table.num_rows()):
        car_id = "{0}-{1}".format(line_data.name, rowid)
        car_def.append("data_car('{0}').".format(car_id))
        for (sta, dtype), colid in station_colidx_map.items():
            if colid is None:
                continue
            val = table.get_value(row=rowid, col=colid)
            if val is None:
                continue
            if is_time_str(val):
                car_stops.append("data_car_stop('{0}', '{1}', '{2}', {3}).".format(car_id, sta, val, dtype))

    return '\n'.join(station_def + car_def + car_stops)
