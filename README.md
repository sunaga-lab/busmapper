

Bus Operation Map Visualizer
-------

バス路線の運行状態を可視化するツールです。木更津の高速バスを可視化するため作成。

各バス運行会社公式サイトにあるHTMLやPDFからデータを引っ張ってきています。
ジョルダンとかからデータを引っ張ってきたら負けだと思う。

# 動作確認環境
 - データ生成スクリプト: Gentoo Linux, Mac OS X High Sierra + brew
 - map.html: Firefox 52.5.2, Chrome 63.0

# 実行方法

1. Dependencyにあるライブラリをインストールしておく。
2. build_tables.py先頭のビルド設定を確認する
3. ./build_tables.py (初回はPDFパースにすごい時間がかかります)
4. www/map.html を開く

どうも木更津-品川のPDFパースに時間がかかるようです。(うちでは30分ぐらい)
build_tables.py の @build_group("木更津-品川") に enabled=False をつければスキップできます。


(ていうか、作ってからよく検索すると全部HTMLあったし、PDFパーサー不要だった・・・)

# Supported Routes
 - 木更津駅-品川駅線 (京浜急行バス, 日東交通, 小湊鐵道)
 - 木更津駅-川崎駅線 (京浜急行バス, 川崎鶴見臨港バス, 日東交通, 小湊鐵道, 東京ベイサービス)
 - 木更津駅-東京駅線 (京成バス, 日東交通)
 - 木更津駅-新宿駅線 (小田急バス, 小湊鐵道)
 - 木更津駅-羽田空港線 (京浜急行バス, 東京空港交通, 日東交通, 小湊鐵道)


# Demonstration
 - [Screenshot@github](https://github.com/sunaga-lab/busmapper/wiki/Screenshots)
 - [Working example@github](https://sunaga-lab.github.io/busmapper/www/map.html)

## 動画

[![](https://img.youtube.com/vi/oujR-9GX_kc/0.jpg)](https://www.youtube.com/watch?v=oujR-9GX_kc)


# Files
 - build_tables.py: 時刻表データの作成
 - mkanim.py: と動画のためのフレーム作成ができます。
 - www/map.html

# Dependency
  - Python 3.6
  - Selenium + chromedriver
  - ImageMagick
  - pdfminer.six (pip) https://github.com/pdfminer/pdfminer.six
  - zenhan (pip)

## for media generators (optional)
  - librsvg (rsvg-convert)
  - bash 4.X


# その他使用しているライブラリ
  - jQuery
  - Leaflet
  

# その他
 - 時刻表データ、PDFまではかんばればなんとかなるとて、[PNG画像オンリー](http://www.kamogawanitto.co.jp/timetable)とか本当にやめて欲しい・・・
   - 頑張ってOCRやれってことなのかな・・・
 - あとHTMLでもせめて [マイクロフォーマット](https://ja.wikipedia.org/wiki/%E3%83%9E%E3%82%A4%E3%82%AF%E3%83%AD%E3%83%95%E3%82%A9%E3%83%BC%E3%83%9E%E3%83%83%E3%83%88) とかぐらいでいいので、やって欲しい・・・
 - バス路線は地図にも出てこないし、当然路線も見えないので見逃されがち。なんかこう、路線が人の目に見えるようになる努力をしたほうがいいかと。
   - 鉄道と比較して、この点のみが重大なバス路線の欠点かと


# License

  - Copyright 2018 Sunaga-Lab, Inc.
  - This software is released under the MIT License.
  - Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
  - The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
  - THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

