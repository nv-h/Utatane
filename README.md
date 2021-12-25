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

Ubuntu 20.04で動作確認しています。

fontforgeとfonttoolsが必要です。fontforgeは現時点での最新版(20201107)を使用しています。
このfontforgeは以下の手順でビルドする必要があります。

```sh
sudo apt-get install libjpeg-dev libtiff5-dev libpng-dev libfreetype6-dev libgif-dev libgtk-3-dev libxml2-dev libpango1.0-dev libcairo2-dev libspiro-dev libuninameslist-dev python3-dev ninja-build cmake build-essential gettext unar fonttools

git clone https://github.com/fontforge/fontforge
cd fontforge
git checkout 20201107
mkdir build && cd build
cmake -GNinja ..
ninja

cd ../../
```

ビルドは以下のコマンドで行います。

```sh
git clone git@github.com:nv-h/Utatane.git
cd Utatane
# さっきビルドしたfontforge
../fontforge/build/bin/fontforge -lang=py -script utatane.py
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
