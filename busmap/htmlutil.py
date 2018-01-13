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

    def make_table_reader(self, xpath, **kw):
        readers = self.make_table_readers(xpath, **kw)
        if len(readers) != 1:
            raise Exception("Not single table")
        return readers[0]

    def make_table_readers(self, xpath, **kw):
        return tablereader.TableList([WebBrowserTableReader.from_table_elem(elem, **kw) for elem in self.driver.find_elements_by_xpath(xpath)])


def striptags(text):
    return re.sub('<[^<]+?>', '', text)


class WebBrowserTableReader(tablereader.Table):

    def __init__(self, table_data=None, html=None, head_column_index=0, head_row_index=0):
        super().__init__()
        self.set_data(table_data, head_column_index=head_column_index, head_row_index=head_row_index)

    @classmethod
    def table_elem_to_list(cls, telem):
        table_data = []
        for line in telem.find_elements_by_xpath('.//tr'):
            line_data = []
            for cell in line.find_elements_by_css_selector('th,td'):
                line_data.append(normalize_text(striptags(cell.get_attribute('innerHTML'))))
            table_data.append(line_data)
        return table_data

    @classmethod
    def from_table_elem(cls, table_elem, **kw):
        return WebBrowserTableReader(
            cls.table_elem_to_list(table_elem),
            html=table_elem.get_attribute('outerHTML'),
            **kw
        )


