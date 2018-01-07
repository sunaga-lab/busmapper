#!/usr/bin/env python3

import subprocess
import random
from PIL import Image
import zenhan

import xml.etree.ElementTree as ET

import math

def random_tmp_fn(suffix = ""):
    ri = random.randint(10000000,99999999)
    return "tmp/" + str(ri) + suffix


def pdf_filename_to_rasterized_image_fn(pdffn, page):
    int_filename = random_tmp_fn("_inter.png")
    rasterized_image_filename = random_tmp_fn("_raster.png")
    cmd = ["convert",
           "-density", "600", "-geometry", "2000",
           "-background", "white", "-alpha", "remove",
           # "-colorspace", "sRGB", "-type", "truecolor",
           "{0}[{1}]".format(pdffn,page), int_filename]
    subprocess.run(args=cmd)

    cmd = ["convert",
           "-colorspace", "sRGB", "-type", "truecolor",
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
        print("[{0}] {1}".format(l, lineval))
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
        return Rectangle(*bboxstr_to_float(bbox_str))


    @staticmethod
    def covered_rect(*rects):
        return Rectangle(
            left=min(r.left for r in rects),
            right=max(r.right for r in rects),
            top=max(r.top for r in rects),
            bottom=min(r.bottom for r in rects)
        )

    def __init__(self, left, bottom, right, top):
        assert left <= right
        assert bottom <= top
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

    def contains(self, rect):
        return self.left <= rect.left and rect.right <= self.right and self.bottom <= rect.bottom and rect.top <= self.top

    def is_touching(self, rect):
        return rect.left <= self.right and self.bottom <= rect.top \
               and self.left <= rect.right and rect.bottom <= self.top

    def __repr__(self):
        return "<Rect: {0}>".format(self.coords)



def sq(v):
    return v*v

class Point:
    def __init__(self, x, y):
        self.coords = [x,y]

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


def normalize_text(text):
    text = text.replace(' ', '').replace('　', '').strip()
    return zenhan.z2h(text, mode=7)


class AbstractTextLine:

    def center_pos(self):
        raise NotImplementedError()


class TextLine(AbstractTextLine):
    def __init__(self, text, rect):
        self.text = text
        self.normalized_text = normalize_text(text)
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


class Page:

    def __init__(self):
        self.lines = TextLineSet()
        self.bounds = None

    def set_bounds(self, bounds):
        self.bounds = bounds

    def clipped(self, bounds, inclusive=True):
        clipped_page = Page()
        clipped_page.bounds = bounds

        for tl in self.lines.items:
            if bounds.contains(tl.rect):
                clipped_page.lines.add(tl)
                continue

            if inclusive and bounds.is_touching(tl.rect):
                clipped_page.lines.add(tl)
                continue

        return clipped_page

    def add_text_line(self, text, pos_text, boxid, char_size_max=None):
        tl = TextLine(text, Rectangle.from_bbox_str(pos_text))
        tl.boxid = boxid
        tl.char_size_max = char_size_max
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
        return result

    def num_nodes_at_line(self, val, vert=False):
        return len(list(filter(lambda tl: tl.is_in_line(val, vert), self.lines)))

    def nearest_textline_from(self, x, y):
        return self.lines.nearest_from(Point(x,y))


def pdfxml_to_boxes(pdfxml):
    print("Parsing xml...")
    root = ET.fromstring(pdfxml)
    print("Boxes:")

    pages = []
    for etpage in root:
        print("[Page={0}]".format(etpage.attrib['id']))
        page = Page()
        page.set_bounds(Rectangle.from_bbox_str(etpage.attrib['bbox']))

        for textbox in etpage.findall('textbox'):
            box_text = ""
            for textline in textbox.findall('textline'):
                line_text = ""
                char_size_max = 0
                for char in textline.findall('text'):
                    if not char.text:
                        continue
                    line_text += char.text
                    char_size_max = max(char_size_max, float(char.attrib.get('size', 0)))
                page.add_text_line(line_text,
                               pos_text=textline.attrib['bbox'],
                               boxid=textbox.attrib['id'],
                               char_size_max=char_size_max)
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
    return pdfxml_to_boxes(xmltxt)




class TableRecognizer:

    def __init__(self, page):
        self.page = page
        self.columns = []
        self.rows = []

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

    def decl_row(self, label, ypos=None):
        if isinstance(label, AbstractTextLine):
            ypos = label.rect.center().y
            label = label.normalized_text

        self.rows.append({
            'row_id': len(self.rows),
            'label': label,
            'y': ypos
        })

    def finish_layout(self):
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


    def get_value(self, col_label, row_label):
        selcol = None
        selrow = None
        for col in self.columns:
            if col['label'] == normalize_text(col_label):
                selcol = col
                break
        for row in self.rows:
            if row['label'] == normalize_text(row_label):
                selrow = row
                break

        cell_rect = Rectangle(left=selcol['x_min'], right=selcol['x_max'], top=selrow['y_max'], bottom=selrow['y_min'])
        clipped = self.page.clipped(cell_rect)
        tl = clipped.nearest_textline_from(selcol['x'],selrow['y'])
        if not tl:
            return None
        else:
            return tl.normalized_text




def main():
    xmltext = open("data/parsed-shinagawa.xml", 'rb').read()
    pages = pdfxml_to_boxes(xmltext)

    page = pages[0]
    print("Num all at page:", len(page.lines))

    print("君津:", page.search_text_contains("市役所"))
    print("袖ケ浦駅発:", page.search_text_contains("袖ケ浦駅発"))
    print("木更津東口:", page.search_text_contains("木更津東口"))

    kuradi = page.search_text_contains("下り").first()
    print("left:", kuradi)

    clipped_page = page.clipped(Rectangle(top=page.bounds.top, bottom=page.bounds.bottom, left=page.bounds.left, right=kuradi.rect.left))
    print("Num clipped:", len(clipped_page.lines))

    print("木更津東口:", clipped_page.search_text_contains("木更津東口"))

    table = TableRecognizer(clipped_page)
    table.decl_column(clipped_page.search_text_contains("平日").first())
    table.decl_column(clipped_page.search_text_contains("木更津東口発").first())
    table.decl_column(clipped_page.search_text_contains("長浦駅北口発").first())
    table.decl_column(clipped_page.search_text_contains("袖ケ浦駅発").first())
    table.decl_column(clipped_page.search_text_contains("袖ケ浦BT発").first())
    table.decl_column(clipped_page.search_text_contains("金田BT発").first())
    table.decl_column(clipped_page.search_text_contains("品川駅東口着").first())

    cur = page.search_text_contains("上り").first()
    count = 1
    while True:
        cand = page.search_text_contains(str(count), single_label_only=True)
        vlabel = cand.nearest_from(cur)
        if not vlabel:
            break
        table.decl_row(str(count), ypos=vlabel.center_pos.y)
        cur = vlabel
        count += 1

    table.finish_layout()
    print("Value:", table.get_value('木更津東口発', '10'))


    # return dumppdf("data/kosoku-kimitsu-tokyo.pdf")

if __name__ == '__main__':
    main()



