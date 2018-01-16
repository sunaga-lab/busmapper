# -*- coding: utf-8 -*-

from . import preset_data_reader
from busmap.datastruct import *
import os
import os.path
from . import tablereader
from . import pdfutil

import urllib.request

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
    if isinstance(text, str):
        with open(filename, 'w') as f:
            f.write(text)
    else:
        with open(filename, 'wb') as f:
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

def pdf_to_pdfxml_if_necessary(source_name, target_name):
    source_filename = local_target_name_to_filename(source_name)
    target_filename = local_target_name_to_filename(target_name)
    if not os.path.exists(target_filename):
        print("Converting pdf...")
        pdfxml = pdfutil.pdf_to_pdfxml(source_filename)
        save_text(target_filename, pdfxml)


def download_file_if_necessary(url, target_name):
    target_filename = local_target_name_to_filename(target_name)
    if not os.path.exists(target_filename):
        print("Downloading file {0} ...".format(url))
        urllib.request.urlretrieve(url, target_filename)

def load_pdfxml_pages(pdfxml_name, original_pdf):
    pages = pdfutil.pdfxmlfile_to_pages(
        local_target_name_to_filename(pdfxml_name),
        original_pdf=local_target_name_to_filename(original_pdf)
    )
    return pages

def load_pdfpages_from_url(url, pdf_id=''):
    if pdf_id:
        pdf_id = '_' + pdf_id
    src_pdf = 'source{0}.pdf'.format(pdf_id)
    pdfxml = 'pdfxml{0}.xml'.format(pdf_id)
    download_file_if_necessary(url, src_pdf)
    pdf_to_pdfxml_if_necessary(src_pdf, pdfxml)
    return load_pdfxml_pages(pdfxml, original_pdf=src_pdf)


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

    if not os.path.exists('build'):
        os.mkdir('build')

    preset_data_reader.read_preset_files(db, PRESET_DATA_DIR)
    for func in g_build_funcs:
        g_build_scope = func.get('name')
        print("Building", g_build_scope, "...")
        func.get('callable')()
