# -*- coding: utf-8 -*-

import json
import yaml
import re
from math import pow, sqrt

STATION_WP_WAIT_TIME = 30

class Database:

    def __init__(self):
        self.stations = {}
        self.lines = {}
        self.cars = {}
        self.paths = []

    def add(self, obj):
        if isinstance(obj, Line):
            self.lines[obj.name] = obj
        elif isinstance(obj, Station):
            self.stations[obj.name] = obj
        elif isinstance(obj, Car):
            self.cars[obj.name] = obj
        elif isinstance(obj, CarEvent):
            self.carevents.append(obj)
        elif isinstance(obj, Path):
            self.paths.append(obj)
        obj.db = self

    def get_path(self, from_sta, to_sta):
        """
        正方向のパスを探す。
        見つからなかった場合はリバースルートを作成　
        """
        path = None
        rev_path = None
        for p in self.paths:
            if p.from_sta == from_sta and p.to_sta == to_sta:
                return p
            if p.from_sta == to_sta and p.to_sta == from_sta:
                rev_path = p

        if rev_path is not None:
            return rev_path.reversed_path()

        return None

    def get_line(self, name):
        return self.lines.get(name)

    def get_station(self, name):
        if name not in self.stations:
            raise Exception("Error: no such station:" + name)

        return self.stations.get(name)


    def dump(self, fn, format='yaml', field_name=None):
        data = {
            'stations': [sta.ddump(self) for sta in self.stations.values()],
            'lines': [line.ddump(self) for line in self.lines.values()],
            'cars': [car.ddump(self) for car in self.cars.values()],
            'paths': [path.ddump(self) for path in self.paths]
        }
        with open(fn, 'w') as f:
            if format == 'yaml':
                yaml.dump(data, f, indent=2, allow_unicode=True)
            elif format == 'json':
                json.dump(data, f, indent=2)
            elif format == 'jsonp':
                datajson = json.dumps(data, indent=2)
                f.write("{0} = {1};".format(field_name, datajson))


class Station:

    def __init__(self, name=None, altnames=None, pos=None, **kw):
        self.name = name
        self.altnames = altnames or []
        self.db = None
        self.pos = pos

    def ddump(self, db):
        return {
            'name': self.name,
            'altnames': self.altnames,
            'pos': self.pos
        }

class Line:

    def __init__(self, name, stations=None, **kw):
        self.name = name
        self.station_names = stations or []
        self.db = None

    def get_stations(self):
        return map(self.db.get_station, self.station_names)

    def ddump(self, db):
        return {
            'name': self.name,
            'stations': self.station_names
        }

class Car:

    def __init__(self, name, linename):
        self.name = name
        self.linename = linename
        self.carevents = []

    def ddump(self, db, resolve_events=True):
        return {
            'name': self.name,
            'line': self.linename,
            'events': [e.ddump() for e in self.dump_events(db, resolve=resolve_events)]
        }

    def resolve_event_station(self, db, event):
        if not event.pos and event.station_name:
            event.pos = db.get_station(event.station_name).pos
        return event

    def dump_events(self, db, resolve=False):
        if not self.carevents:
            return []

        for e in self.carevents:
            self.resolve_event_station(db, e)

        events = sorted(self.carevents, key=lambda c: c.time)
        if not resolve:
            return events

        result = [events[0]]
        for i in range(1, len(events)):
            evt_from = events[i-1]
            evt_to = events[i]
            if evt_from.station_name == evt_to.station_name:
                result.append(evt_to)
                continue
            path = db.get_path(evt_from.station_name, evt_to.station_name)
            if not path:
                result.append(evt_to)
                continue

            all_dur = evt_to.time - evt_from.time - STATION_WP_WAIT_TIME * 2
            for i in range(0, len(path.points)):
                result.append(CarEvent(
                    time=int(evt_from.time + all_dur*path.point_time[i] + STATION_WP_WAIT_TIME),
                    event='v',
                    day_options=evt_from.day_options,
                    pos=path.points[i]
                ))
            result.append(evt_to)
        return result


    def add_event(self, carevent):
        self.carevents.append(carevent)


reTimeStrHHcMM = re.compile("([0-9]{1,2}):([0-9]{1,2})")
reTimeStrHHMM = re.compile("([0-9]{2})([0-9]{2})")

def normalize_time(ts):
    if isinstance(ts, int):
        return ts
    m = reTimeStrHHcMM.match(ts)
    if m:
        return time_to_seconds(hours=m.group(1), minutes=m.group(2))
    m = reTimeStrHHMM.match(ts)
    if m:
        return time_to_seconds(hours=m.group(1), minutes=m.group(2))

    raise ValueError("Invalid timestr:" + ts)


def time_to_seconds(hours=0, minutes=0, seconds=0):
    return int((int(hours)*60+int(minutes))*60 + int(seconds))

def time_to_timestr(*idx, **kw):
    all_seconds = time_to_seconds(*idx, **kw)

    secs = all_seconds % 60
    mins = (all_seconds // 60) % 60
    hours = all_seconds // 3600

    return "{0:02}{1:02}".format(hours, mins)



class CarEvent:

    def __init__(self, time, event, station=None, day_options=None, pos=None):
        self.time = normalize_time(time)
        self.event = event
        self.station_name = station
        self.day_options = day_options or []
        self.pos=pos

    def ddump(self):
        result = {
            'time': self.time,
            'event': self.event,
            'station': self.station_name
        }
        if self.day_options:
            result['day_options'] = self.day_options
        if self.pos:
            result['pos'] = self.pos
        return result



def sq(v):
    return v*v


class Path:

    def __init__(self, points, from_sta=None, to_sta=None, point_time=None, **kw):
        self.points = points
        self.from_sta = from_sta or kw.get('from')
        self.to_sta = to_sta or kw.get('to')
        self.point_time = point_time or []
        if not self.point_time:
            self.calc_point_time()

    def reversed_path(self):
        return Path(
                points=list(reversed(self.points)),
                from_sta=self.to_sta,
                to_sta=self.from_sta,
                point_time=[(1.0 - t) for t in reversed(self.point_time)]
            )

    def calc_point_time(self):
        self.point_time = [0]
        point_dur = [0]

        for i in range(1, len(self.points)):
            p0 = self.points[i-1]
            p = self.points[i]
            point_dur.append(sqrt(sq(p[0] - p0[0]) + sq(p[1] - p0[1])))

        all_dur = sum(point_dur)

        for i in range(1, len(self.points)):
            self.point_time.append(
                self.point_time[i - 1] + (point_dur[i])/all_dur
            )
            if self.point_time[-1] >= 1.0:
                self.point_time[-1] = 1.0

    def ddump(self, db):
        return {
            'from': self.from_sta,
            'to': self.to_sta,
            'points': self.points,
            'point_time': self.point_time,
        }


def dict_to_dataobj(data):
    dtype = data.get('t').lower()

    if dtype == 'station':
        return Station(**data)
    if dtype == 'line':
        return Line(**data)
    if dtype == 'path':
        return Path(**data)

    raise Exception('Unknown data-type:' + str(dtype))
