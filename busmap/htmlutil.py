# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from selenium import webdriver

from selenium.webdriver.chrome.options import Options
import time
from . import tablereader
from .datastruct import *

class HTMLReader:

    def __init__(self, url=None):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1024,768')
        self.driver = webdriver.Chrome(chrome_options=options)
        if url is not None:
            self.driver.get(url)
            time.sleep(3)

    def make_table_reader(self, xpath):
        readers = self.make_table_readers(xpath)
        if len(readers) != 1:
            raise Exception("Not single table")
        return readers[0]

    def make_table_readers(self, xpath):
        return [WebBrowserTableReader.from_table_elem(elem) for elem in self.driver.find_elements_by_xpath(xpath)]


class WebBrowserTableReader(tablereader.Table):

    def __init__(self, table_data=None, html=None):
        self.table_data = table_data
        self.html = html

    @classmethod
    def table_elem_to_list(cls, telem):
        table_data = []
        tbody = telem.find_element_by_tag_name('tbody')
        for line in tbody.find_elements_by_tag_name('tr'):
            line_data = []
            for cell in line.find_elements_by_css_selector('th,td'):
                line_data.append(normalize_text(cell.get_attribute('innerHTML')))
            table_data.append(line_data)
        return table_data

    @classmethod
    def from_table_elem(cls, table_elem):
        return WebBrowserTableReader(cls.table_elem_to_list(table_elem), table_elem.get_attribute('outerHTML'))

    @classmethod
    def concat_vert(cls, table1, table2):
        return WebBrowserTableReader(table_data=table1.table_data+table2.table_data)

    def concat_vert_with(self, table2):
        return self.concat_vert(self, table2)

    def num_rows(self):
        return len(self.table_data)

    def num_columns(self):
        return len(self.table_data[0])

    def get_value_from_index(self, colidx, rowidx):
        try:
            print("Get:{0},{1} -> {2}".format(colidx, rowidx, self.table_data[rowidx][colidx]))
            return self.table_data[rowidx][colidx]
        except IndexError:
            return None

    def col_index(self, colname):
        try:
            return self.table_data[0].index(normalize_text(colname))
        except ValueError:
            return None

    def row_index(self, rowname):
        rowname = normalize_text(rowname)
        for i, row in enumerate(self.table_data):
            if len(row) > 0 and row[0] == rowname:
                return i
        return None

    def to_csv(self):
        return '\n'.join(','.join(line) for line in self.table_data)

