# -*- coding: utf-8 -*-

import json
import yaml
import re

class Database:

    def __init__(self):
        self.stations = {}
        self.lines = {}
        self.cars = {}

    def add(self, obj):
        if isinstance(obj, Line):
            self.lines[obj.name] = obj
        elif isinstance(obj, Station):
            self.stations[obj.name] = obj
        elif isinstance(obj, Car):
            self.cars[obj.name] = obj
        elif isinstance(obj, CarEvent):
            self.carevents.append(obj)
        obj.db = self

    def get_line(self, name):
        return self.lines.get(name)

    def get_station(self, name):
        if name not in self.stations:
            raise Exception("Error: no such station:" + name)

        return self.stations.get(name)


    def dump(self, fn):
        data = {
            'stations': [sta.ddump() for sta in self.stations.values()],
            'lines': [line.ddump() for line in self.lines.values()],
            'cars': [car.ddump() for car in self.cars.values()]
        }
        with open(fn, 'w') as f:
            yaml.dump(data, f, indent=2, allow_unicode=True)


class Station:

    def __init__(self, name=None, altnames=None, **kw):
        self.name = name
        self.altnames = altnames or []
        self.db = None

    def ddump(self):
        return {
            'name': self.name,
            'altnames': self.altnames
        }

class Line:

    def __init__(self, name, stations=None, **kw):
        self.name = name
        self.station_names = stations or []
        self.db = None

    def get_stations(self):
        return map(self.db.get_station, self.station_names)

    def ddump(self):
        return {
            'name': self.name,
            'stations': self.station_names
        }

class Car:

    def __init__(self, name, linename):
        self.name = name
        self.linename = linename
        self.carevents = []

    def ddump(self):
        return {
            'name': self.name,
            'line': self.linename,
            'events': [e.ddump() for e in self.carevents]
        }

    def add_event(self, carevent):
        self.carevents.append(carevent)


reTimeStrHHcMM = re.compile("([0-9]{1,2}):([0-9]{1,2})")
reTimeStrHHMM = re.compile("([0-9]{2})([0-9]{2})")

def normalize_timestr(ts):

    m = reTimeStrHHcMM.match(ts)
    if m:
        return time_to_timestr(hours=m.group(1), minutes=m.group(2))
    m = reTimeStrHHMM.match(ts)
    if m:
        return time_to_timestr(hours=m.group(1), minutes=m.group(2))

    raise ValueError("Invalid timestr:" + ts)


def time_to_timestr(hours=0, minutes=0, seconds=0):

    all_seconds = int((int(hours)*60+int(minutes))*60 + int(seconds))

    secs = all_seconds % 60
    mins = (all_seconds // 60) % 60
    hours = all_seconds // 3600

    return "{0:02}{1:02}".format(hours, mins)



class CarEvent:

    def __init__(self, time, event, station=None, day_options=None):
        self.time = normalize_timestr(time)
        self.event = event
        self.station_name = station
        self.day_options = day_options or []

    def ddump(self):
        result = {
            'time': self.time,
            'event': self.event,
            'station': self.station_name
        }
        if self.day_options:
            result['day_options'] = self.day_options
        return result


def dict_to_dataobj(data):
    dtype = data.get('t').lower()

    if dtype == 'station':
        return Station(**data)
    if dtype == 'line':
        return Line(**data)

    raise Exception('Unknown data-type:' + str(dtype))
