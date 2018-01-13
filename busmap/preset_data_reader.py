# -*- coding: utf-8 -*-

from busmap.datastruct import *
import yaml
import os


def read_preset_files(db, datadir):

    for file in os.listdir(datadir):
        with open(os.path.join(datadir, file), 'r') as f:
            data_dict = yaml.load(f)
            print("Reading preset", file, "...")
            read_preset(db, data_dict)

def read_preset(db, data):

    for entry in data:
        if entry.get('t') == 'options':
            if entry.get('disabled', False):
                print("Skip reading.")
                return
            continue
        dobj = dict_to_dataobj(entry)
        db.add(dobj)
