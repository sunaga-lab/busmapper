#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from busmap import pdfutil, htmlutil, tablereader, preset_data_reader

from busmap.build_script import *

pdfutil.pdfutil_debug_enabled = False
tablereader.tablereader_debug_enabled = False

debug_pages = []

pdfutil.PDF2TXT_PATH = "/usr/local/bin/pdf2txt.py"

@build_group("木更津-品川")
def parse_kisarazu_shinagawa():

    @build_for('stables')
    def build():
        pages = load_pdfpages_from_url('http://www.nitto-kotsu.co.jp/img/kosoku/shinagawa.pdf')
        page = pages[0]
        debug_pages.append(page)

        dojyujitsu_text = page.search_text_contains("土休日").first()
        weekday_area = page.clipped(page.bounds.left_area_of(dojyujitsu_text.rect), inclusive=False, clip_name='平日')
        kuradi = weekday_area.search_text_contains("下り").first()

        @build_for('T1.json')
        def build():
            # 平日上りのパース
            clipped_page = weekday_area.clipped(weekday_area.bounds.left_area_of(kuradi.rect), inclusive=False, clip_name='上り')
            tr = pdfutil.TableRecognizer(clipped_page)
            tr.decl_column(clipped_page.search_text_contains("平日").first().dmark())
            tr.decl_column(clipped_page.search_text_contains("木更津東口発").first().dmark())
            tr.decl_column(clipped_page.search_text_contains("長浦駅北口発").first().dmark())
            tr.decl_column(clipped_page.search_text_contains("袖ケ浦駅発").first().dmark())
            tr.decl_column(clipped_page.search_text_contains("袖ケ浦BT発").first().dmark())
            tr.decl_column(clipped_page.search_text_contains("金田BT発").first().dmark())
            tr.decl_column(clipped_page.search_text_contains("品川駅東口着").first().dmark())
            tr.decl_sequential_rows(clipped_page.search_text_contains("上り").first(), range(1, 500))
            return tr.gen_with_table_attrs(tablename='T上り', linename='高速バス木更津・品川線', day_options=['weekday'])

        @build_for('T2.json')
        def build():
            # 平日下りのパース
            clipped_page = weekday_area.clipped(weekday_area.bounds.right_area_of(kuradi.rect.left), inclusive=True, clip_name='下り')
            tr = pdfutil.TableRecognizer(clipped_page)
            tr.decl_column(clipped_page.search_text_contains("平日").first().dmark())
            tr.decl_column(clipped_page.search_text_contains("木更津東口着").first().dmark())
            tr.decl_column(clipped_page.search_text_contains("長浦駅北口着").first().dmark())
            tr.decl_column(clipped_page.search_text_contains("袖ケ浦駅着").first().dmark())
            tr.decl_column(clipped_page.search_text_contains("袖ケ浦BT着").first().dmark())
            tr.decl_column(clipped_page.search_text_contains("金田BT着").first().dmark())
            tr.decl_column(clipped_page.search_text_contains("品川駅東口発").first().dmark())
            tr.decl_sequential_rows(clipped_page.search_text_contains("下り").first(), range(1, 500))
            return tr.gen_with_table_attrs(tablename='T下り', linename='高速バス木更津・品川線', day_options=['weekday'])

    import_tables('T1.json', 'T2.json')


@build_group("木更津-羽田")
def parse_kisarazu_haneda():

    @build_for('tables')
    def build():
        pages = load_pdfpages_from_url('http://www.nitto-kotsu.co.jp/img/kosoku/kosoku-kisarazu-haneda.pdf')
        page = pages[0]
        debug_pages.append(page)

        kuradi = page.search_text_contains("【下り】").first()
        nobori = page.search_text_contains("【上り】").first()
        noriba_goannai = page.search_text_contains("【のりばご案内】").first()

        @build_for('T1.json')
        def build():
            # 平日上りのパース
            clipped_page = page.clipped(
                page.bounds.left_area_of(kuradi.rect).bottom_area_of(nobori.rect).top_area_of(noriba_goannai.rect),
                inclusive=False, clip_name='上り')
            r = pdfutil.TableRecognizer(clipped_page)
            r.decl_column(clipped_page.search_text_contains("便").first().dmark())
            r.decl_column(clipped_page.search_text_contains("会社").first().dmark())
            r.decl_column(clipped_page.search_text_contains("木更津駅").first().dmark())
            r.decl_column(clipped_page.search_text_contains("袖ヶ浦BT").first().dmark())
            r.decl_column(clipped_page.search_text_contains("金田BT").first().dmark())
            r.decl_column(clipped_page.search_text_contains("第1ターミナル").first().dmark())
            r.decl_column(clipped_page.search_text_contains("第2ターミナル").first().dmark())
            r.decl_column(clipped_page.search_text_contains("国際ターミナル").first().dmark())
            r.decl_sequential_rows(clipped_page.search_text_contains("便").first(), range(1, 500))
            return r.gen_with_table_attrs(tablename='T上り', linename='高速バス木更津・羽田空港線', day_options=['weekday'])


        @build_for('T2.json')
        def build():
            # 平日下りのパース
            clipped_page = page.clipped(page.bounds.right_area_of(kuradi.rect.left).bottom_area_of(nobori.rect).top_area_of(noriba_goannai.rect), inclusive=False,
                                        clip_name='下り')
            r = pdfutil.TableRecognizer(clipped_page)
            r.decl_column(clipped_page.search_text_contains("便").first().dmark())
            r.decl_column(clipped_page.search_text_contains("会社").first().dmark())
            r.decl_column(clipped_page.search_text_contains("木更津駅").first().dmark())
            r.decl_column(clipped_page.search_text_contains("袖ヶ浦BT").first().dmark())
            r.decl_column(clipped_page.search_text_contains("金田BT").first().dmark())
            r.decl_column(clipped_page.search_text_contains("第1ターミナル").first().dmark())
            r.decl_column(clipped_page.search_text_contains("第2ターミナル").first().dmark())
            r.decl_column(clipped_page.search_text_contains("国際ターミナル").first().dmark())
            r.decl_sequential_rows(clipped_page.search_text_contains("便").first(), range(1, 500))
            return r.gen_with_table_attrs(tablename='T下り', linename='高速バス木更津・羽田空港線', day_options=['weekday'])

    import_tables(
        'T1.json',
        'T2.json'
    )

@build_group("木更津-川崎")
def parse_kisarazu_kawasaki():

    @build_for('tables')
    def build():
        reader = htmlutil.HTMLReader("http://www.keikyu-bus.co.jp/highway/k-sodegaura/")

        @build_for('T1.json')
        def build():
            tbls = reader.make_table_readers("//*[text()='袖ヶ浦バスターミナル・木更津駅ゆき']/following::table")
            table = tbls[0].concat_vert_with(tbls[1])
            return table.with_table_atts(tablename="T下り", linename='高速バス木更津・川崎線', day_options=['weekday'])

        @build_for('T2.json')
        def build():
            tbls = reader.make_table_readers("//*[text()='川崎駅ゆき']/following::table")
            table = tbls[0].concat_vert_with(tbls[1])
            return table.with_table_atts(tablename="T上り", linename='高速バス木更津・川崎線', day_options=['weekday'])

    import_tables(
        'T1.json',
        'T2.json'
    )


@build_group("木更津-新宿")
def parse_kisarazu_shinjuku():

    @build_for('tables.json')
    def build():
        reader = htmlutil.HTMLReader("http://www.odakyubus.co.jp/highway/line/aqualine.html")
        tables = reader.make_table_readers("//*[text()='平日(月～金)']/following::table")
        tables[0].with_table_atts(
            tablename="T下り",
            linename='高速バス木更津・新宿線',
            day_options=['weekday']
        )
        tables[1].with_table_atts(
            tablename="T上り",
            linename='高速バス木更津・新宿線',
            day_options=['weekday']
        )
        return tables

    import_tables(
        'tables.json'
    )


@build_group("木更津-東京")
def parse_kisarazu_tokyo():

    @build_for('tables')
    def build():
        reader = htmlutil.HTMLReader("http://www.keiseibus.co.jp/kousoku/timetable.php?id=38")

        @build_for('for-tokyo-tables.json')
        def build():
            tables = reader.make_table_readers(
                "//*[text()='東雲車庫・東京駅行き']/following::dd[1]//table",
                head_column_index=1
            )
            for i, table in enumerate(tables):
                table.with_table_atts(
                    tablename="T上り" + str(i + 1),
                    linename='高速バス木更津・東京線',
                    day_options=['weekday'],
                    invert_axis=True
                )
            return tables

        @build_for('for-kisarazu-tables.json')
        def build():

            tables = reader.make_table_readers(
                "//*[text()='木更津駅・君津行き']/following::dd[1]//table",
                head_column_index=1
            )
            for i, table in enumerate(tables):
                table.with_table_atts(
                    tablename="T下り" + str(i + 1),
                    linename='高速バス木更津・東京線',
                    day_options=['weekday'],
                    invert_axis=True
                )
            return tables

    import_tables(
        'for-tokyo-tables.json',
        'for-kisarazu-tables.json'
    )


def main():
    try:
        build_all()
        db.dump('tmp/dbdump.txt', format='json', for_debug=True)
        db.dump('www/db.js', format='jsonp', field_name='DB')
        db.dump('www/db.json', format='json')
        db.dump('tmp/db_debug.txt', format='debug_text')

    finally:
        print("Building debug pages...")
        for p in debug_pages:
            p.flush_debug_marks()

if __name__ == '__main__':
    main()



