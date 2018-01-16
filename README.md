

# 実行方法

(Mac OS X High Sierra + brew の環境のみで検証済み)

1. Dependencyにあるライブラリをインストールしておく。
2. build_tables.py先頭のビルド設定を確認する
3. ./build_tables.py (初回はPDFパースにすごい時間がかかります)
4. www/map.html を開く

どうも木更津-品川のPDFパースに時間がかかるようです。(うちでは30分ぐらい)
build_tables.py の @build_group("木更津-品川") に enabled=False をつければスキップできます。


# Files
 - build_tables.py: 時刻表データの作成
 - mkanim.py: と動画のためのフレーム作成ができます。
 - www/map.html

# Dependency
  - Python 3.6
  - phantomjs + chromedriver
  - PDFMiner
  - ImageMagick

## for media generators (optional)
  - librsvg (rsvg-convert)
  - bash 4.X

# Used Libraries
  - jQuery
  - Leaflet
  

# License

Copyright 2018 Sunaga-Lab, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

