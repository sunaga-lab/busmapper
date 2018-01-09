#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from busmap import pdfutil, tablereader, preset_data_reader
from busmap.datastruct import *

db = Database()

PRESET_DATA_DIR = "./preset_data"

# pdfutil.pdfutil_debug_enabled = True




def parse_kisarazu_shinagawa():
    pages = pdfutil.pdfxmlfile_to_pages("data/parsed-shinagawa.xml", original_pdf="data/shinagawa.pdf")

    page = pages[0]

    dojyujitsu_text = page.search_text_contains("土休日").first()
    weekday_area = page.clipped(page.bounds.left_area_of(dojyujitsu_text.rect), inclusive=False, clip_name='平日')


    # 平日上りのパース
    kuradi = weekday_area.search_text_contains("下り").first()

    clipped_page = weekday_area.clipped(weekday_area.bounds.left_area_of(kuradi.rect), inclusive=False, clip_name='上り')
    table = pdfutil.TableRecognizer(clipped_page)
    table.decl_column(clipped_page.search_text_contains("平日").first().dmark())
    table.decl_column(clipped_page.search_text_contains("木更津東口発").first().dmark())
    table.decl_column(clipped_page.search_text_contains("長浦駅北口発").first().dmark())
    table.decl_column(clipped_page.search_text_contains("袖ケ浦駅発").first().dmark())
    table.decl_column(clipped_page.search_text_contains("袖ケ浦BT発").first().dmark())
    table.decl_column(clipped_page.search_text_contains("金田BT発").first().dmark())
    table.decl_column(clipped_page.search_text_contains("品川駅東口着").first().dmark())

    cur = weekday_area.search_text_contains("上り").first()
    count = 1
    while True:
        cand = weekday_area.search_text_contains(str(count), single_label_only=True)
        vlabel = cand.nearest_from(cur)
        if not vlabel:
            break
        table.decl_row(str(count), ypos=vlabel.center_pos.y)
        cur = vlabel
        count += 1

    table.finish_layout()

    tablereader.table_to_fact(
        db,
        table,
        tablename="T1",
        line=db.get_line('高速バス木更津・品川線'),
        day_options=['weekday']
    )



    # 平日下りのパース
    clipped_page = weekday_area.clipped(weekday_area.bounds.right_area_of(kuradi.rect.left), inclusive=True, clip_name='下り')
    table = pdfutil.TableRecognizer(clipped_page)
    table.decl_column(clipped_page.search_text_contains("平日").first().dmark())
    page.flush_debug_marks()
    table.decl_column(clipped_page.search_text_contains("木更津東口着").first().dmark())
    table.decl_column(clipped_page.search_text_contains("長浦駅北口着").first().dmark())
    table.decl_column(clipped_page.search_text_contains("袖ケ浦駅着").first().dmark())
    table.decl_column(clipped_page.search_text_contains("袖ケ浦BT着").first().dmark())
    table.decl_column(clipped_page.search_text_contains("金田BT着").first().dmark())
    table.decl_column(clipped_page.search_text_contains("品川駅東口発").first().dmark())

    cur = weekday_area.search_text_contains("上り").first()
    count = 1
    while True:
        cand = weekday_area.search_text_contains(str(count), single_label_only=True)
        vlabel = cand.nearest_from(cur)
        if not vlabel:
            break
        table.decl_row(str(count), ypos=vlabel.center_pos.y)
        cur = vlabel
        count += 1

    table.finish_layout()

    print(tablereader.table_to_fact(
        db,
        table,
        tablename="T2",
        line=db.get_line('高速バス木更津・品川線'),
        day_options=['weekday']
    ))


    page.flush_debug_marks()

    db.dump('tmp/dbdump.txt')
    db.dump('www/db.js', format='jsonp', field_name='DB')


def main():
    parse_kisarazu_shinagawa()

if __name__ == '__main__':
    preset_data_reader.read_preset_files(db, PRESET_DATA_DIR)
    main()



