# -*- coding: utf-8 -*-

import json
import yaml
import re
from math import pow, sqrt, floor
import random
import zenhan
import sys


STATION_WP_WAIT_TIME = 30
DAY_SPLIT = 3 * 60 * 60 # 3:00区切り

def random_tmp_fn(suffix = ""):
    ri = random.randint(10000000,99999999)
    return "tmp/" + str(ri) + suffix


LATITUDE_TO_KM_AROUND_TOKYO = 111.263
LONGITUDE_TO_KM_AROUND_TOKYO = 91.159
DEFAULT_SPEED_VALUE = 60


normalize_replace_map = [
    [' ', ''],
    ['　', ''],
    ['ヶ', 'ｹ']
]

def normalize_text(text):
    text = text.strip()
    text = zenhan.z2h(text, mode=7)
    for a, b in normalize_replace_map:
        text = text.replace(a,b)
    return text

def normalized_eq(a, b):
    return normalize_text(a) == normalize_text(b)

class Database:

    def __init__(self):
        self.stations = {}
        self.lines = {}
        self.cars = {}
        self.paths = []

        self.dumped_data = None
        self.shown_errors = set()

    def add(self, obj):
        self.dumped_data = None
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
        見つからなかった場合はリバースルートを作成。
        """
        path = None
        rev_path = None
        for p in self.paths:
            if normalized_eq(p.from_sta, from_sta) and normalized_eq(p.to_sta, to_sta):
                return p
            if normalized_eq(p.from_sta, to_sta) and normalized_eq(p.to_sta, from_sta):
                rev_path = p

        if rev_path is not None:
            return rev_path.reversed_path()

        return None

    def get_line(self, name):
        if name not in self.lines:
            raise Exception('No station: ' + str(name))
        return self.lines.get(name)

    def get_station(self, name):
        if name not in self.stations:
            print(self.stations)
            raise Exception("Error: no such station: '" + name + "'")

        return self.stations.get(name)

    def dump(self, fn, format='yaml', field_name=None, for_debug=False):
        if not self.dumped_data:
            self.dumped_data = {
                'stations': [sta.ddump(self) for sta in self.stations.values()],
                'lines': [line.ddump(self) for line in self.lines.values()],
                'cars': [car.ddump(self) for car in self.cars.values()],
                'paths': [path.ddump(self) for path in self.paths]
            }
        with open(fn, 'w') as f:
            if format == 'debug_text':
                f.write(self.debug_text())
            elif format == 'yaml':
                yaml.dump(self.dumped_data, f, indent=2, allow_unicode=True)
            elif format == 'json':
                json.dump(self.dumped_data, f, indent=2, ensure_ascii=not for_debug)
            elif format == 'jsonp':
                datajson = json.dumps(self.dumped_data, indent=2)
                f.write("{0} = {1};".format(field_name, datajson))

    def debug_text(self):
        result = []
        result.extend([path.debug_text(self) for path in self.paths])
        return '\n'.join(result)


    def error(self, msg, submsg=""):
        if msg in self.shown_errors:
            return
        print(msg, submsg, file=sys.stderr)
        self.shown_errors.add(msg)

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
                db.error(
                    "ERROR: path '{0}', '{1}' not found".format(evt_from.station_name, evt_to.station_name),
                    "Referenced by: {0} event {1}".format(self.name, i)
                )
                result.append(evt_to)
                continue
            path_point_time = path.get_point_time(db)
            path_points = path.get_points_included(db)
            all_dur = evt_to.time - evt_from.time - STATION_WP_WAIT_TIME * 2
            for i in range(0, len(path_points)):
                result.append(CarEvent(
                    time=int(evt_from.time + all_dur*path_point_time[i] + STATION_WP_WAIT_TIME),
                    event='v',
                    day_options=evt_from.day_options,
                    pos=path_points[i]
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
    result = int((int(hours)*60+int(minutes))*60 + int(seconds))
    # 日付区切りより前だったら24時以降とみなす
    if result < DAY_SPLIT:
        result += 24*60*60
    return result


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


class ReversedPath:

    def __init__(self, orig_path):
        self.orig_path = orig_path

    def reversed_path(self):
        return self.orig_path

    def get_points_included(self, db, reverse=False):
        return self.orig_path.get_points_included(db, not reverse)


    def get_point_time(self, db, reverse=False):
        return self.orig_path.get_point_time(db, not reverse)

    def debug_text(self, db):
        return self.orig_path.debug_text(db)


class Path:

    def __init__(self, points=None, from_sta=None, to_sta=None, name=None, via=None, **kw):
        self.from_sta = from_sta or kw.get('from')
        self.to_sta = to_sta or kw.get('to')

        if 'fromto' in kw:
            if len(kw['fromto']) < 2:
                print("Error: less than 1 point ({0}) at fromto".format(kw['fromto']))
            self.from_sta, self.to_sta = kw['fromto']

        self.name = name

        self.points = points or []
        if via:
            if isinstance(via, str):
                via = [via]
            via_points = [self.from_sta] + via + [self.to_sta]
            self.points = [
                ['include', via_points[i-1], via_points[i]]
                for i in range(1, len(via_points))
            ]

        self.points_with_speeds = None
        self.points_included = {}
        self.point_time = {}


    def reversed_path(self):
        return ReversedPath(self)


    def get_points_with_speeds(self, reverse=False):
        if not self.points_with_speeds:
            curspeed = None
            self.points_with_speeds = []
            for p in self.points:
                if not p:
                    continue
                if p[0] == 'include':
                    self.points_with_speeds.append(p)
                elif len(p) == 2:
                    self.points_with_speeds.append(p + [curspeed, curspeed])
                elif len(p) == 3:
                    self.points_with_speeds.append([p[0], p[1], curspeed, p[2]])
                    curspeed = p[2]

        if reverse:
            return [(p if len(p) < 4 else ([p[0], p[1], p[3], p[2]] + p[4:])) for p in reversed(self.points_with_speeds)]
        else:
            return self.points_with_speeds


    def get_points_included(self, db, reverse=False):
        if self.points_included.get(reverse):
            return self.points_included[reverse]

        result_path = []
        for p in self.get_points_with_speeds(reverse):
            if p[0] == 'include' and len(p) >= 3:
                from_p = p[1]
                to_p = p[2]
                if reverse:
                    to_p, from_p = from_p, to_p
                including_path = db.get_path(from_p, to_p)
                if not including_path:
                    db.error(
                        "ERROR: Route ['{0}', '{1}'] does not exists.".format(from_p, to_p),
                        "Referenced by ['{0}', '{1}'] (include)".format(self.from_sta, self.to_sta)
                    )
                else:
                    result_path.extend(including_path.get_points_included(db))
            else:
                result_path.append(p)
        self.points_included[reverse] = result_path
        return result_path


    def get_point_time(self, db, reverse=False):
        if self.point_time.get(reverse):
            return self.point_time[reverse]

        points = self.get_points_included(db, reverse=reverse)

        point_time = [0]
        point_dur = [0]
        for i in range(1, len(points)):
            p0 = points[i-1]
            p = points[i]
            speed = p0[3] or DEFAULT_SPEED_VALUE
            # 東京付近での大体のkm
            edge_len = sqrt(sq((p[0] - p0[0]) * LATITUDE_TO_KM_AROUND_TOKYO) + sq((p[1] - p0[1]) * LONGITUDE_TO_KM_AROUND_TOKYO))
            point_dur.append(edge_len / speed)

        all_dur = sum(point_dur)
        assumed_dur_min = floor(all_dur * 60)
        print("Notice: Assumed duration for ['{0}', '{1}']{3} = {2}min".format(self.from_sta, self.to_sta, assumed_dur_min, '(rev)' if reverse else ''))

        for i in range(1, len(points)):
            point_time.append(
                point_time[i - 1] + (point_dur[i])/all_dur
            )
            if point_time[-1] >= 1.0:
                point_time[-1] = 1.0
        self.point_time[reverse] = point_time
        return point_time

    def debug_text(self, db):
        result = ["[ROUTE from:{0} to:{1}".format(self.from_sta, self.to_sta)]
        for p, pt in zip(self.get_points_included(db), self.get_point_time(db)):
            result.append("- [{0}, {1}] spd={2}->{3} : w:{4}".format(p[0], p[1], p[2], p[3], pt))

        result.append("(reverse)")
        for p, pt in zip(self.get_points_included(db, reverse=True), self.get_point_time(db, reverse=True)):
            result.append("- [{0}, {1}] spd={2}->{3} : w:{4}".format(p[0], p[1], p[2], p[3], pt))
        return '\n'.join(result)

    def ddump(self, db):
        return {
            'from': self.from_sta,
            'to': self.to_sta,
            'points': self.points,
            'points_included': self.points_included,
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


