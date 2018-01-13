# -*- coding: utf-8 -*-

from . import preset_data_reader
from busmap.datastruct import *
import os
import os.path
from . import tablereader

db = Database()
PRESET_DATA_DIR = "./preset_data"


g_build_scope = None
g_build_funcs = []

def build_group(alter_name=None, enabled=True):
    def _dec(func):
        if not enabled:
            return
        g_build_funcs.append({
            'name': alter_name or func.__name__,
            'callable': func
        })
    return _dec


def local_target_name_to_filename(target_name):
    return "build/{0}_{1}".format(g_build_scope, target_name)

def save_text(filename, text):
    with open(filename, 'w') as f:
        f.write(text)

def build_for(target_name):
    def _dec(func):
        target_filename = local_target_name_to_filename(target_name)
        if os.path.exists(target_filename):
            print("Building {0}::{1} skip.".format(g_build_scope, target_filename))
        else:
            result = func()
            if result is None:
                save_text(target_filename, "__None__")
            else:
                result.save(target_filename)


    return _dec

def import_tables(*table_names):

    for table_name in table_names:
        table_filename = local_target_name_to_filename(table_name)
        tables = tablereader.TableList.load(table_filename)
        for table in tables:
            if table.get_table_attr('linename'):
                tablereader.table_to_fact(
                    db,
                    table,
                    tablename=table.get_table_attr('tablename'),
                    line=db.get_line(table.get_table_attr('linename')),
                    day_options=table.get_table_attr('day_options'),
                    invert_axis=table.get_table_attr('invert_axis', False)
                )


def build_all():
    global g_build_scope
    preset_data_reader.read_preset_files(db, PRESET_DATA_DIR)
    for func in g_build_funcs:
        g_build_scope = func.get('name')
        print("Building", g_build_scope, "...")
        func.get('callable')()
