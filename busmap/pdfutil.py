# -*- coding: utf-8 -*-

import subprocess
import random
from PIL import Image, ImageDraw, ImageFont
import numbers
import xml.etree.ElementTree as ET
from .datastruct import *

import math
from . import tablereader


pdfutil_debug_enabled = False



def pdf_rasterized(pdffn, page):
    image_png = pdf_filename_to_rasterized_image_fn(pdffn, page)
    return Image.open(image_png, 'r').convert('RGBA')


def pdf_filename_to_rasterized_image_fn(pdffn, page):
    int_filename = random_tmp_fn("_inter.png")
    rasterized_image_filename = random_tmp_fn("_raster.png")
    cmd = ["convert",
           "-density", "600", "-geometry", "4000",
           # "-colorspace", "sRGB", "-type", "truecolor",
           "{0}[{1}]".format(pdffn,page), int_filename]
    subprocess.run(args=cmd)

    cmd = ["convert",
           "-colorspace", "rgb",
           "-type", "truecolormatte",
           "-background", "white", "-alpha", "remove",
           int_filename, rasterized_image_filename]
    subprocess.run(args=cmd)

    return rasterized_image_filename


def split_tables(pdfimg, vert=True):
    debug_img = Image.new('RGB', pdfimg.size)

    (w,h) = pdfimg.size
    nlines = h if vert else w
    npix = w if vert else h
    for l in range(nlines):
        lineval = 0
        for p in range(npix):
            pos = (p,l) if vert else (l,p)
            (r,g,b) = pdfimg.getpixel(pos)
            if g < 250:
                lineval += 1
            debug_img.putpixel(pos, (r,g,b))
    debug_img.save('tmp/_debug.png')


def is_color_same(a,b,error):
    return abs(a[0] - b[0]) <= error and abs(a[1] - b[1]) <= error and abs(a[2] - b[2]) <= error

def fill_same_color_area(img, from_pos, color, error=3):
    tc = img.getpixel(from_pos)
    posstack = [from_pos]
    while posstack:
        pos = posstack.pop()
        if pos[0] < 0 or pos[1] < 0 or pos[0] >= img.size[0] or pos[1] >= img.size[1]:
            continue
        pix = img.getpixel(pos)

        # 染色ずみ
        if is_color_same(pix, color, error):
            continue

        # 染色対象
        if is_color_same(pix, tc, error):
            img.putpixel(pos, color)
            posstack.append((pos[0]+1, pos[1]))
            posstack.append((pos[0]-1, pos[1]))
            posstack.append((pos[0], pos[1]+1))
            posstack.append((pos[0], pos[1]-1))
    return img

def pdf_to_fact(filename):
    print("Rasterizing image...")
    pdfimg_fn = pdf_filename_to_rasterized_image_fn(filename, page=1)
    pdfimg = Image.open(pdfimg_fn)
    pdfimg.show()
    pdfimg_rgb = pdfimg.convert('RGB')
    pdfimg_rgb.save('tmp/rgb.png')
    pdfimg_rgb.show()

    print("Filling")
    filled = fill_same_color_area(pdfimg_rgb.copy(), (1,1), (255,0,0))
    filled.save('tmp/filled.png')
    print("Table splitting...")


    split_tables(pdfimg_rgb, False)


# val is between a and b
def between(val, a, b):
    return a <= val <= b or b <= val <= a


def bboxstr_to_float(bboxstr):
    return [float(v) for v in bboxstr.split(',')]

class Rectangle:

    INDEX_LEFT = 0
    INDEX_BOTTOM = 1
    INDEX_RIGHT = 2
    INDEX_TOP = 3

    @staticmethod
    def from_bbox_str(bbox_str):
        if not bbox_str:
            return None
        return Rectangle(*bboxstr_to_float(bbox_str))


    @staticmethod
    def covered_rect(*rects):
        return Rectangle(
            left=min(r.left for r in rects),
            right=max(r.right for r in rects),
            top=max(r.top for r in rects),
            bottom=min(r.bottom for r in rects)
        )

    def __init__(self, left, bottom, right, top, coord_sys='pdf'):
        if coord_sys == 'pdf':
            assert left <= right
            assert bottom <= top
        self.coord_sys = coord_sys
        self.coords = [left, bottom, right, top]

    @property
    def left(self):
        return self.coords[self.INDEX_LEFT]

    @property
    def bottom(self):
        return self.coords[self.INDEX_BOTTOM]

    @property
    def right(self):
        return self.coords[self.INDEX_RIGHT]

    @property
    def top(self):
        return self.coords[self.INDEX_TOP]


    def __getitem__(self, key):
        return self.coords[key]

    def __setitem__(self, key, val):
        self.coords[key] = val

    def center(self):
        return Point((self.left + self.right)/2.0, (self.top + self.bottom)/2.0)

    def contains(self, rect, inclusive=False):
        if self.left <= rect.left and rect.right <= self.right and self.bottom <= rect.bottom and rect.top <= self.top:
            return True
        if inclusive and self.is_touching(rect):
            return True
        return False

    def is_touching(self, rect):
        return rect.left <= self.right and self.bottom <= rect.top \
               and self.left <= rect.right and rect.bottom <= self.top

    def __repr__(self):
        return "<Rect: {0}>".format(self.coords)


    def _inv_edge(self, e):
        return {
            'left': 'right',
            'right': 'left',
            'bottom': 'top',
            'top': 'bottom'
        }.get(e)

    def _edge_area_of(self, edge, val):
        if isinstance(val, AbstractTextLine):
            return self._edge_area_of(edge, getattr(val.rect, edge))
        if isinstance(val, Rectangle):
            return self._edge_area_of(edge, getattr(val, edge))
        elif isinstance(val, numbers.Real):
            p = dict(top=self.top, bottom=self.bottom, left=self.left, right=self.right)
            p[self._inv_edge(edge)] = val
            return Rectangle(**p)

        raise TypeError("{0} is invalid".format(val))

    def left_area_of(self, x):
        return self._edge_area_of('left', x)

    def right_area_of(self, x):
        return self._edge_area_of('right', x)

    def top_area_of(self, y):
        return self._edge_area_of('top', y)

    def bottom_area_of(self, y):
        return self._edge_area_of('bottom', y)


    def top_left(self):
        return Point(x=self.left, y=self.top, coord_sys=self.coord_sys)


def sq(v):
    return v*v

class Point:
    def __init__(self, x, y, coord_sys='pdf'):
        self.coords = [x,y]
        self.coord_sys = coord_sys

    @property
    def x(self):
        return self.coords[0]

    @property
    def y(self):
        return self.coords[1]

    def __getitem__(self, key):
        return self.coords[key]

    def __setitem__(self, key, val):
        self.coords[key] = val

    def __repr__(self):
        return "<Point: {0}>".format(self.coords)

    def distance_from(self, pos):
        return math.sqrt(sq(self.x - pos.x) + sq(self.y - pos.y))

    @property
    def as_array(self):
        return self.coords




class AbstractTextLine:

    def center_pos(self):
        raise NotImplementedError()


class CharBox:

    def __init__(self, char, rect, size):
        self.char = char
        self.rect = rect
        self.size = size

    @staticmethod
    def char_list_to_text(char_list):
        return ''.join(c.char for c in char_list)



class TextLine(AbstractTextLine):

    def __init__(self, page, char_list, rect):
        self.page = page
        self.char_list = char_list
        self.text = CharBox.char_list_to_text(char_list)
        self.normalized_text = normalize_text(self.text)
        self.rect = rect
        self.boxid = None
        self.char_size_max = None

    def contains(self, text):
        if text in self.normalized_text:
            return True
        return False

    def endswith(self, text):
        return self.normalized_text.endswith(text)

    def __repr__(self):
        return "<Line:{0} bbox:{1} bid:{2}>".format(self.normalized_text, self.rect, self.boxid)

    def getsize(self):
        return [abs(self.rect[0]-self.rect[2]), abs(self.rect[1]-self.rect[3])]

    def is_near_to(self, rhs, scale=3.0):
        xlim = (self.getsize()[0] + rhs.getsize()[0])*0.5*scale
        ylim = (self.getsize()[1] + rhs.getsize()[1])*0.5*scale
        if abs(self.center_pos[0]-rhs.center_pos[0]) < xlim and abs(self.center_pos[1] - rhs.center_pos[1]) < ylim:
            return True
        return False

    def is_in_line(self, val, vert=False):
        vindex = 0 if vert else 1
        return between(val, self.rect[0+vindex], self.rect[2+vindex])

    @property
    def center_pos(self):
        return self.rect.center()

    def dmark(self, text=None):
        if text is None:
            text = self.normalized_text
        self.page.dmark_rect('label', self.rect)
        self.page.dmark_text('label', Point(self.rect.left, self.rect.top), text)
        return self

    def clipped(self, bounds, inclusive=True):
        new_char_list = list(filter(lambda c: bounds.contains(c.rect, inclusive), self.char_list))
        if len(new_char_list) == len(self.char_list):
            return self
        tl = TextLine(self.page, new_char_list, self.rect)
        tl.boxid = self.boxid
        tl.char_size_max = self.char_size_max
        return tl

class TextLineGroup(AbstractTextLine):

    def __init__(self, *items):
        self.items = []
        for item in items:
            if isinstance(item, TextLineGroup):
                self.items += item.items
            elif isinstance(item, TextLine):
                self.items.append(item)
            else:
                raise Exception("Cannot merge")

    @property
    def normalized_text(self):
        return ''.join(item.normalized_text for item in self.items)

    @property
    def rect(self):
        return Rectangle.covered_rect(*(l.rect for l in self.items))

    @property
    def center_pos(self):
        return self.rect.center()

    def dmark(self, text=None):
        for tl in self.items:
            tl.dmark(text=text)
        return self

    def clipped(self, bounds, inclusive=True):
        new_items = map(lambda item: item.clipped(bounds, inclusive), self.items)
        return TextLineGroup(*new_items)

    def __repr__(self):
        return "<TLGrp:{0}>".format(self.items)



class TextLineSet:

    def __init__(self, items=None):
        self.items = items or []

    def first(self):
        if len(self.items) > 0:
            return self.items[0]
        return None

    def add(self, tl):
        self.items.append(tl)

    def nearest_from(self, pos_or_textline):
        if not self.items:
            return None
        pos = None
        if isinstance(pos_or_textline, Point):
            pos = pos_or_textline
        elif isinstance(pos_or_textline, AbstractTextLine):
            pos = pos_or_textline.center_pos
        else:
            raise Exception("Unknown type:", type(pos_or_textline))
        nearest = self.items[0]
        nearest_len = nearest.rect.center().distance_from(pos)
        for item in self.items[1:]:
            dist = item.rect.center().distance_from(pos)
            if dist < nearest_len:
                nearest_len = dist
                nearest = item
        return nearest

    def __len__(self):
        return len(self.items)

    def __repr__(self):
        return "<TLSet:{0}>".format(repr(self.items))

    def dmark(self, text=None):
        for tl in self.items:
            tl.dmark(text=text)
        return self

    def sort_by_distance_from(self, pos):
        self.items.sort(key=lambda tl: pos.distance_from(tl.center_pos))

    def clipped(self, bounds, inclusive=True):
        new_items = map(lambda item: item.clipped(bounds, inclusive), self.items)
        return TextLineSet(*new_items)

class Page:

    def __init__(self):
        self.lines = TextLineSet()
        self.bounds = None
        self.original_pdf = None
        self.page_index = None
        self._draw_target = None
        self._draw_target_image = None
        self.debug_enabled = pdfutil_debug_enabled

        self.dmark_default_draw_type = 'main'
        self.dmark_draw_types = {
            'sub': {
                'color': (255,0,0, 255),
                'width': 2
            },
            'main': {
                'color': (0, 255, 0, 255),
                'width': 2
            },
            'label': {
                'color': (0, 0, 255, 255),
                'width': 2
            },
            'clip': {
                'color': (255, 0, 255, 255),
                'width': 2
            }
        }

    def prepare_dmark_target(self):
        if self._draw_target is not None:
            return
        self._draw_target_image = pdf_rasterized(self.original_pdf, self.page_index)
        self._draw_font = ImageFont.truetype('ipaexg.ttf', 15)
        self._draw_target = ImageDraw.Draw(self._draw_target_image)

    @property
    def draw_target(self):
        if not self.debug_enabled:
            return None
        if self._draw_target:
            return self._draw_target
        self.prepare_dmark_target()
        return self._draw_target

    def set_bounds(self, bounds):
        self.bounds = bounds

    def full_page(self):
        return self

    def clipped(self, bounds, inclusive=True, clip_name=None):
        clipped_page = ClippedPage(self, bounds)

        for tl in self.lines.items:
            if bounds.contains(tl.rect):
                clipped_page.lines.add(tl.clipped(bounds, inclusive=inclusive))
                continue

            if inclusive and bounds.is_touching(tl.rect):
                clipped_page.lines.add(tl.clipped(bounds, inclusive=inclusive))
                continue

        if clip_name is not None:
            self.dmark_rect('clip', bounds)
            self.dmark_text('clip', bounds.top_left(), "CLIP:" + clip_name)
        return clipped_page

    def add_text_line(self, char_list, boxid):
        if not char_list:
            return None
        text_rect = Rectangle.covered_rect(*[c.rect for c in char_list])
        tl = TextLine(self, char_list, text_rect)
        tl.boxid = boxid
        tl.char_size_max = max(c.size for c in char_list)
        self.lines.add(tl)
        return tl

    def search_text_contains(self, text, near_to=None, excludes=[], exact_match=False, single_label_only=False):
        assert text
        text = normalize_text(text)
        result = TextLineSet()
        for line in self.lines.items:
            if line in excludes:
                continue
            if near_to and not line.is_near_to(near_to):
                continue
            if line.contains(text):
                result.add(line)
            elif not exact_match and not single_label_only:
                for l in range(1, len(text)):
                    if line.endswith(text[:l]):
                        continued_boxes = self.search_text_contains(text[l:], near_to=line, excludes=excludes+[line], exact_match=True)
                        for b in continued_boxes.items:
                            result.add(TextLineGroup(line, b))
        if near_to is not None:
            result.sort_by_distance_from(near_to.center_pos)
        return result

    def num_nodes_at_line(self, val, vert=False):
        return len(list(filter(lambda tl: tl.is_in_line(val, vert), self.lines)))

    def nearest_textline_from(self, x, y):
        return self.lines.nearest_from(Point(x,y))

    def to_dmark_x(self, x):
        return (x/self.bounds.right) * self._draw_target_image.size[0]

    def to_dmark_y(self, y):
        return (1.0 - y/self.bounds.top) * self._draw_target_image.size[1]

    def to_dmark_coord(self, p):
        self.prepare_dmark_target()
        if isinstance(p, Point):
            return Point(x=self.to_dmark_x(p.x), y=self.to_dmark_y(p.y), coord_sys='image')
        elif isinstance(p, Rectangle):
            return Rectangle(
                left=self.to_dmark_x(p.left),
                right=self.to_dmark_x(p.right),
                top=self.to_dmark_y(p.top),
                bottom=self.to_dmark_y(p.bottom),
                coord_sys='image')

    def get_dmark_type(self, typename):
        return self.dmark_draw_types.get(typename, self.dmark_draw_types[self.dmark_default_draw_type])

    def dmark_line(self, dmark_type, p_from, p_to):
        if not self.debug_enabled:
            return
        dmt = self.get_dmark_type(dmark_type)
        self.draw_target.line(self.to_dmark_coord(p_from).as_array + self.to_dmark_coord(p_to).as_array, fill=dmt['color'], width=dmt['width'])

    def dmark_rect(self, dmark_type, rect):
        if not self.debug_enabled:
            return
        dmt = self.get_dmark_type(dmark_type)
        rcv = self.to_dmark_coord(rect)
        self.draw_target.line(
            [(rcv.left, rcv.top), (rcv.right, rcv.top), (rcv.right, rcv.bottom), (rcv.left, rcv.bottom), (rcv.left, rcv.top)],
            fill=dmt['color'],
            width=dmt['width'])

    def dmark_text(self, dmark_type, pos, text):
        if not self.debug_enabled:
            return
        dmt = self.get_dmark_type(dmark_type)
        self.draw_target.text(self.to_dmark_coord(pos), text, font=self._draw_font, fill=dmt['color'])

    def flush_debug_marks(self):
        if not self.debug_enabled:
            return
        if self._draw_target_image:
            fn = random_tmp_fn("_dmarks.png")
            self._draw_target_image.save(fn)
            print("Debug image saved to:", fn)


class ClippedPage(Page):

    def __init__(self, original_page, bounds):
        super().__init__()
        self.original_page = original_page
        self.bounds = bounds
        self.original_pdf = original_page.original_pdf
        self.page_index = original_page.page_index

    def full_page(self):
        return self.original_page.full_page()

    def dmark_line(self, *idx, **kw):
        self.original_page.dmark_line(*idx, **kw)

    def dmark_rect(self, *idx, **kw):
        self.original_page.dmark_rect(*idx, **kw)

    def dmark_text(self, *idx, **kw):
        self.original_page.dmark_text(*idx, **kw)




def pdfxml_to_pages(pdfxml, original_pdf=None):
    root = ET.fromstring(pdfxml)

    pages = []
    for etpage in root:
        page = Page()
        page.original_pdf = original_pdf
        page.page_index = len(pages)
        page.set_bounds(Rectangle.from_bbox_str(etpage.attrib['bbox']))

        for textbox in etpage.findall('textbox'):
            box_text = ""
            boxid_seq = 0
            for textline in textbox.findall('textline'):
                line_chars = []
                for char in textline.findall('text'):
                    if not normalize_text(char.text) and len(char.attrib.keys()) == 0:
                        page.add_text_line(line_chars, boxid="{0}_{1}".format(textbox.attrib['id'], boxid_seq))
                        line_chars = []
                        boxid_seq += 1
                        continue
                    line_chars.append(CharBox(char.text, Rectangle.from_bbox_str(char.attrib.get('bbox')), float(char.attrib.get('size', 0))))

                page.add_text_line(line_chars, boxid="{0}_{1}".format(textbox.attrib['id'], boxid_seq))
        pages.append(page)
    return pages



def pdf_to_pdfxml(pdffn):
    print("Running pdf2txt...")
    cmd = ["python3",
           "/usr/local/bin/pdf2txt.py",
           pdffn, "-t", "xml"]
    proc = subprocess.run(args=cmd, check=True, stdout=subprocess.PIPE)
    xmltxt = proc.stdout
    return xmltxt




def dumppdf(pdffn):
    xmltxt = pdf_to_pdfxml(pdffn)
    return pdfxml_to_pages(xmltxt)


def pdfxmlfile_to_pages(fn, original_pdf=None):
    xmltext = open(fn, 'rb').read()
    return pdfxml_to_pages(xmltext, original_pdf=original_pdf)




class TableRecognizer(tablereader.TableGenerator):

    def __init__(self, page):
        self.page = page
        self.columns = []
        self.rows = []
        self.debug_out = True

    def decl_column(self, label, xpos=None):
        assert label

        if isinstance(label, AbstractTextLine):
            xpos = label.rect.center().x
            label = label.normalized_text

        self.columns.append({
            'col_id': len(self.columns),
            'label': label,
            'x': xpos
        })
        return self

    def decl_row(self, label, ypos=None):
        if isinstance(label, AbstractTextLine):
            ypos = label.rect.center().y
            label = label.normalized_text

        self.rows.append({
            'row_id': len(self.rows),
            'label': label,
            'y': ypos
        })
        return self

    def decl_sequential_rows(self, start_pos, sequence):
        cur = start_pos
        for item in sequence:
            cand = self.page.search_text_contains(str(item), single_label_only=True)
            vlabel = cand.nearest_from(cur)
            if not vlabel:
                return
            self.decl_row(str(item), ypos=vlabel.center_pos.y)
            cur = vlabel
        return self

    def gen_with_table_attrs(self, **attrs):
        table = self.generate_table()
        return table.with_table_atts(**attrs)


    def generate_table(self):
        self.columns.sort(key=lambda item:item['x'])
        self.rows.sort(key=lambda item:-item['y'])

        self.columns[0]['x_min'] = 0
        for i in range(1, len(self.columns)):
            self.columns[i-1]['x_max'] = self.columns[i]['x_min'] = (self.columns[i-1]['x']+self.columns[i]['x'])/2.0
        self.columns[-1]['x_max'] = self.page.bounds.right

        self.rows[0]['y_max'] = self.page.bounds.top
        for i in range(1, len(self.rows)):
            self.rows[i-1]['y_min'] = self.rows[i]['y_max'] = (self.rows[i-1]['y']+self.rows[i]['y'])/2.0
        self.rows[-1]['y_min'] = 0

        self.put_dmarks()

        tdata = []
        for row in self.rows:
            tdata_line = []
            for col in self.columns:
                tdata_line.append(self.get_cell_value_from_rowcol(col=col, row=row))
            tdata.append(tdata_line)

        return tablereader.Table.from_data(
            table_data=tdata,
            columns=[c['label'] for c in self.columns],
            rows=[r['label'] for r in self.rows]
        )

    def get_cell_value_from_rowcol(self, col, row):
        if col is None or row is None:
            return None

        cell_rect = Rectangle(left=col['x_min'], right=col['x_max'], top=row['y_max'], bottom=row['y_min'])
        clipped = self.page.clipped(cell_rect)
        tl = clipped.nearest_textline_from(col['x'], row['y'])
        if not tl:
            return None
        else:
            return tl.normalized_text

    def put_dmarks(self):
        pbnd = self.page.bounds

        for col in self.columns:
            self.page.dmark_line('sub', Point(col['x_min'], pbnd.top), Point(col['x_min'], pbnd.bottom))
            self.page.dmark_line('main', Point(col['x'], pbnd.top), Point(col['x'], pbnd.bottom))
            self.page.dmark_line('sub', Point(col['x_max'], pbnd.top), Point(col['x_max'], pbnd.bottom))
            self.page.dmark_text('main', Point(col['x'], pbnd.top), "COL:" + col['label'])

        for row in self.rows:
            self.page.dmark_line('sub', Point(pbnd.left, row['y_min']), Point(pbnd.right, row['y_min']))
            self.page.dmark_line('main', Point(pbnd.left, row['y']), Point(pbnd.right, row['y']))
            self.page.dmark_line('sub', Point(pbnd.left, row['y_max']), Point(pbnd.right, row['y_max']))
            self.page.dmark_text('main', Point(pbnd.left, row['y']), "ROW:" + row['label'])

