# -*- coding: utf-8 -*-


class Database:

    def __init__(self):
        self.stations = {}
        self.lines = {}

    def add(self, obj):
        if isinstance(obj, Line):
            self.lines[obj.name] = obj
        elif isinstance(obj, Station):
            self.stations[obj.name] = obj
        obj.db = self

    def get_line(self, name):
        return self.lines.get(name)

    def get_station(self, name):
        if name not in self.stations:
            raise Exception("Error: no such station:" + name)

        return self.stations.get(name)


class Station:

    def __init__(self, name=None, alternative_names=None):
        self.name = name
        self.alternative_names = alternative_names or []
        self.db = None


class Line:

    def __init__(self, name, stations=None):
        self.name = name
        self.station_names = stations or []
        self.db = None

    def get_stations(self):
        return map(self.db.get_station, self.station_names)


