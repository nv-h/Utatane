# プログラミング用フォント Utatane

![on Windows](screenshots/ss1.png)

## ダウンロード

[リリースページ](https://github.com/nv-h/Utatane/releases/latest)にビルド済みのフォントを配置しています。

## 概要

Ricty生成スクリプトをフォークして生成したプログラミング用の等幅フォント[Cica](https://github.com/miiton/Cica)からさらにフォークしたフォントです。
[Ubuntu Mono](http://font.ubuntu.com/) と
[やさしさゴシック](http://www.fontna.com/blog/379/) と [やさしさゴシックボールド](http://www.fontna.com/blog/736/) を合成して少し調整しています。

```
o Utatane
|\
* * Ubuntu Mono
 \
  * やさしさゴシック
  |\
  | * IPA Fonts
  |\
  | * M+ FONTS
  |
  * やさしさゴシックボールド
   \
    * M+ FONTS
```

IPAフォントに置き換える場合 [IPAフォント](http://ossipedia.ipa.go.jp/ipafont/index.html) のページでIPAゴシックを入手してください。

## ビルド

Ubuntu 16.04 (WSL)で動作確認しています。

fontforgeとfonttoolsが必要です。fontforgeはppaの現時点での最新版(20170731)を使用しています。

```sh
sudo add-apt-repository ppa:fontforge/fontforge
sudo apt install fontforge fonttools unar
```

環境準備は適当な場所で以下を実行すると完了します。

```sh
git clone git@github.com:nv-h/Utatane.git
wget https://assets.ubuntu.com/v1/fad7939b-ubuntu-font-family-0.83.zip
unar fad7939b-ubuntu-font-family-0.83.zip
cp ubuntu-font-family-0.83/UbuntuMono-R.ttf Utatane/sourceFonts/
cp ubuntu-font-family-0.83/UbuntuMono-B.ttf Utatane/sourceFonts/
wget https://github.com/nv-h/Utatane/releases/download/Utatane_v1.0.6/Utatane_v1.0.6.7z
unar Utatane_v1.0.6.7z
cp Utatane_v1.0.6/07Yasashisa/07やさしさゴシック.ttf Utatane/sourceFonts/07YasashisaGothic-R.ttf
cp Utatane_v1.0.6/07YasashisaBold/07やさしさゴシックボールド.ttf Utatane/sourceFonts/07YasashisaGothic-B.ttf
```

ビルドは以下のコマンドで行います。

```sh
cd Utatane
fontforge -lang=py -script utatane.py
```

## Rictyからの変更点

* 英数字に Ubutnu Mono を使用しています
* それ以外の文字に やさしさゴシック を使用しています
* 非HiDPI（非Retina）のWindowsでも文字が欠けません


## バリエーション

| ファイル名                  | 説明     |
| ----                        | ----     |
| Utatane-Regular.ttf         | 通常     |
| Utatane-Bold.ttf            | 太字     |

斜体はおかしくなるので未対応。

# ライセンス

* [LICENSE.txt](LICENSE.txt)

# 謝辞

Utataneフォントの合成にあたり[フォーク元のCicaフォント作成者](https://github.com/miiton)に感謝します。
また、以下の素晴らしいフォントを作成してくださった方々もありがとうございます。ありがたく使わせていただきます。

- [Ubuntu Font Family](http://font.ubuntu.com/)
- [やさしさゴシック](http://www.fontna.com/blog/379/)
- [やさしさゴシックボールド](http://www.fontna.com/blog/736/)
- [M\+ FONTS](https://mplus-fonts.osdn.jp/)
- [IPAフォント](http://ossipedia.ipa.go.jp/ipafont/index.html)
