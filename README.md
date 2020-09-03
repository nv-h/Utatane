# プログラミング用フォント Utatane

![on Windows](screenshots/ss1.png)

## ダウンロード

[リリースページ](https://github.com/nv-h/Utatane/releases/latest)にビルド済みのフォントを配置しています。

## 概要

Ricty生成スクリプトをフォークして生成したプログラミング用の等幅フォント[Cica](https://github.com/miiton/Cica)からさらにフォークしたフォントです。
[Ubuntu Mono](http://font.ubuntu.com/) と
[やさしさゴシックボールドV2](https://booth.pm/ja/items/1833993) を合成して少し調整しています。

```
o Utatane
|\
* * Ubuntu Mono
 \
  * やさしさゴシックボールドV2
   \
    * M+ FONTS
```

## ビルド

Ubuntu 18.04で動作確認しています。

fontforgeとfonttoolsが必要です。fontforgeはppaの現時点での最新版(20200314)を使用しています。
このfontforgeは以下の手順でビルドする必要があります。

```sh
sudo apt-get install libjpeg-dev libtiff5-dev libpng-dev libfreetype6-dev libgif-dev libgtk-3-dev libxml2-dev libpango1.0-dev libcairo2-dev libspiro-dev libuninameslist-dev python3-dev ninja-build cmake build-essential

git clone https://github.com/fontforge/fontforge
cd fontforge
mkdir build && cd build
cmake -GNinja ..
ninja

cd ../../
```

環境準備は適当な場所で以下を実行すると完了します。

```sh
# このリポジトリをクローン
git clone git@github.com:nv-h/Utatane.git

# Ubuntu fontをダウンロードして配置
wget https://assets.ubuntu.com/v1/fad7939b-ubuntu-font-family-0.83.zip
unar fad7939b-ubuntu-font-family-0.83.zip
cp ubuntu-font-family-0.83/UbuntuMono-R.ttf Utatane/sourceFonts/
cp ubuntu-font-family-0.83/UbuntuMono-B.ttf Utatane/sourceFonts/

# YasashisaGothicBold-V2をダウンロードして配置
# ※パブリックなダウンロード元がないので、自分のリポジトリでホストしているものから抜き出し
wget https://github.com/nv-h/Utatane/releases/download/Utatane_v1.0.8/Utatane_v1.0.8.7z
unar Utatane_v1.0.8.7z
# このttfファイルは、付属のotf2ttf.peスクリプトで元のotfファイルを変換したもの
cp Utatane_v1.0.8/Yasashisa/YasashisaGothicBold-V2.ttf Utatane/sourceFonts/
```

ビルドは以下のコマンドで行います。

```sh
cd Utatane
# さっきビルドしたfontforge
../../fontforge/build/bin/fontforge -lang=py -script utatane.py
```

## Rictyからの変更点

* 英数字に Ubutnu Mono を使用しています
* それ以外の文字に やさしさゴシックボールドV2 を使用しています
* 非HiDPI（非Retina）のWindowsでも文字が欠けません


## バリエーション

| ファイル名                  | 説明     |
| ----                        | ----     |
| Utatane-Regular.ttf         | 通常     |
| Utatane-Bold.ttf            | 太字     |

斜体はおかしくなるので未対応。

## ライセンス

フォント本体は、[Ubuntu Font License](https://ubuntu.com/legal/font-licence)で、生成スクリプトなどはMITライセンスとしています。


## 謝辞

Utataneフォントの合成にあたり[フォーク元のCicaフォント作成者](https://github.com/miiton)に感謝します。
また、以下の素晴らしいフォントを作成してくださった方々もありがとうございます。ありがたく使わせていただきます。

- [Ubuntu Font Family](http://font.ubuntu.com/)
- [やさしさゴシックボールドV2](https://booth.pm/ja/items/1833993)
- [M+ FONTS](https://mplus-fonts.osdn.jp/)
