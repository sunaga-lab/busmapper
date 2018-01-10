#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from busmap import pdfutil, htmlutil, tablereader, preset_data_reader
from busmap.datastruct import *
from busmap import blobdb

db = Database()
PRESET_DATA_DIR = "./preset_data"

blobstore = blobdb.BlobStore('./blob')

# pdfutil.pdfutil_debug_enabled = True

debug_pages = []

def parse_kisarazu_shinagawa():
    pages = pdfutil.pdfxmlfile_to_pages("data/parsed-shinagawa.xml", original_pdf="data/shinagawa.pdf")
    page = pages[0]
    debug_pages.append(page)

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
    table.decl_sequential_rows(clipped_page.search_text_contains("上り").first(), range(1, 500))
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
    table.decl_sequential_rows(clipped_page.search_text_contains("下り").first(), range(1, 500))

    table.finish_layout()

    tablereader.table_to_fact(
        db,
        table,
        tablename="T2",
        line=db.get_line('高速バス木更津・品川線'),
        day_options=['weekday']
    )

    page.flush_debug_marks()



def parse_kisarazu_haneda():

    pages = pdfutil.pdfxmlfile_to_pages("data/parsed_kosoku-kisarazu-haneda.xml", original_pdf="data/kosoku-kisarazu-haneda.pdf")
    page = pages[0]
    debug_pages.append(page)

    kuradi = page.search_text_contains("【下り】").first()
    nobori = page.search_text_contains("【上り】").first()
    noriba_goannai = page.search_text_contains("【のりばご案内】").first()

    # 平日上りのパース
    clipped_page = page.clipped(
        page.bounds.left_area_of(kuradi.rect).bottom_area_of(nobori.rect).top_area_of(noriba_goannai.rect),
        inclusive=False, clip_name='上り')
    table = pdfutil.TableRecognizer(clipped_page)
    table.decl_column(clipped_page.search_text_contains("便").first().dmark())
    table.decl_column(clipped_page.search_text_contains("会社").first().dmark())
    table.decl_column(clipped_page.search_text_contains("木更津駅").first().dmark())
    table.decl_column(clipped_page.search_text_contains("袖ヶ浦BT").first().dmark())
    table.decl_column(clipped_page.search_text_contains("金田BT").first().dmark())
    table.decl_column(clipped_page.search_text_contains("第1ターミナル").first().dmark())
    table.decl_column(clipped_page.search_text_contains("第2ターミナル").first().dmark())
    table.decl_column(clipped_page.search_text_contains("国際ターミナル").first().dmark())
    table.decl_sequential_rows(clipped_page.search_text_contains("便").first(), range(1, 500))
    table.finish_layout()

    tablereader.table_to_fact(
        db,
        table,
        tablename="T1",
        line=db.get_line('高速バス木更津・羽田空港線'),
        day_options=['weekday']
    )

    # 平日下りのパース
    clipped_page = page.clipped(page.bounds.right_area_of(kuradi.rect.left).bottom_area_of(nobori.rect).top_area_of(noriba_goannai.rect), inclusive=False,
                                clip_name='下り')
    table = pdfutil.TableRecognizer(clipped_page)
    table.decl_column(clipped_page.search_text_contains("便").first().dmark())
    table.decl_column(clipped_page.search_text_contains("会社").first().dmark())
    table.decl_column(clipped_page.search_text_contains("木更津駅").first().dmark())
    table.decl_column(clipped_page.search_text_contains("袖ヶ浦BT").first().dmark())
    table.decl_column(clipped_page.search_text_contains("金田BT").first().dmark())
    table.decl_column(clipped_page.search_text_contains("第1ターミナル").first().dmark())
    table.decl_column(clipped_page.search_text_contains("第2ターミナル").first().dmark())
    table.decl_column(clipped_page.search_text_contains("国際ターミナル").first().dmark())
    table.decl_sequential_rows(clipped_page.search_text_contains("便").first(), range(1, 500))
    table.finish_layout()

    tablereader.table_to_fact(
        db,
        table,
        tablename="T2",
        line=db.get_line('高速バス木更津・羽田空港線'),
        day_options=['weekday']
    )


def parse_kisarazu_kawasaki():
    print("Reading http://www.keikyu-bus.co.jp/highway/k-sodegaura/...")
    reader = htmlutil.HTMLReader("http://www.keikyu-bus.co.jp/highway/k-sodegaura/")

    print("Parsing tables [袖ヶ浦バスターミナル・木更津駅ゆき]...")
    tbls = reader.make_table_readers("//*[text()='袖ヶ浦バスターミナル・木更津駅ゆき']/following::table")
    table = tbls[0].concat_vert_with(tbls[1])
    print("Building facts...")
    tablereader.table_to_fact(
        db,
        table,
        tablename="T1",
        line=db.get_line('高速バス木更津・川崎線'),
        day_options=['weekday']
    )

    print("Parsing tables [川崎駅ゆき]...")
    tbls = reader.make_table_readers("//*[text()='川崎駅ゆき']/following::table")
    table = tbls[0].concat_vert_with(tbls[1])
    print("Building facts...")
    tablereader.table_to_fact(
        db,
        table,
        tablename="T2",
        line=db.get_line('高速バス木更津・川崎線'),
        day_options=['weekday']
    )



def main():
    try:
        parse_kisarazu_shinagawa()
        parse_kisarazu_haneda()
        parse_kisarazu_kawasaki()

        db.dump('tmp/dbdump.txt', format='json', for_debug=True)
        db.dump('www/db.js', format='jsonp', field_name='DB')
    finally:
        print("Building debug pages...")
        for p in debug_pages:
            p.flush_debug_marks()


if __name__ == '__main__':
    preset_data_reader.read_preset_files(db, PRESET_DATA_DIR)
    main()



