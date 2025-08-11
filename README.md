# プログラミング用フォント Utatane

![on Windows](screenshots/ss1.png)

（Color scheme は [gruvbox-material](https://github.com/sainnhe/gruvbox-material) を使用）

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

### 依存関係
- FontForge（このリポジトリにサブモジュールとして含まれています）
- fontTools: `pip install fonttools`
- ビルドツール：cmake, ninja-build, build-essential
- 開発ライブラリ：libjpeg-dev, libtiff5-dev, libpng-dev, libfreetype-dev, libgif-dev, libgtk-3-dev, libxml2-dev, libpango1.0-dev, libcairo2-dev, libspiro-dev, libwoff-dev, python3-dev, gettext

### ビルド手順

```bash
git clone git@github.com:nv-h/Utatane.git
cd Utatane

# サブモジュールの初期化・取得
git submodule update --init --recursive

# 必要な依存関係のインストール（Ubuntu/Debian系の場合）
sudo apt-get install libjpeg-dev libtiff5-dev libpng-dev libfreetype-dev libgif-dev libgtk-3-dev libxml2-dev libpango1.0-dev libcairo2-dev libspiro-dev libwoff-dev python3-dev ninja-build cmake build-essential gettext

# fontToolsのインストール
pip install fonttools

# FontForgeのビルド
cd fontforge
mkdir -p build
cd build
cmake -GNinja ..
ninja

# フォント生成
cd ../..
./fontforge/build/bin/fontforge -lang=py -script ./utatane.py
```

**Windows環境の場合:**
```ps1
# デフォルトのインストール先を使用する場合
& 'c:\Program Files (x86)\FontForgeBuilds\bin\fontforge' -lang=py -script .\utatane.py
```

### 生成確認
生成が成功すると、`dist/`ディレクトリに以下のファイルが作成されます：
- `Utatane-Regular.ttf` （約3MB）
- `Utatane-Bold.ttf` （約3MB）

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

## ディレクトリ構成

```
Utatane/
├── utatane.py              # メインのフォント生成スクリプト
├── glyph-compare.sh        # グリフ形状比較統合ツール
├── sourceFonts/            # ソースフォントファイル
├── fontforge/              # FontForgeサブモジュール（最新版ソースコード）
├── dist/                   # 生成されたフォントの出力先
├── tmp/                    # 一時ファイル・PDF出力先
├── test/                   # テスト関連ファイル
│   ├── font_disp.txt       # フォント表示テスト用文字セット
│   ├── glyph_data_extractor.py   # グリフデータ抽出（FontForge用）
│   ├── glyph_visualizer.py       # グリフ可視化（matplotlib用）
│   └── ... (その他のテストスクリプト)
├── analysis/               # 文字幅分析スクリプト
│   ├── README.md
│   ├── font_analysis.py
│   └── ... (その他の分析スクリプトなど)
├── docs/                   # 開発ドキュメント
│   ├── README.md
│   ├── character_width_comprehensive_analysis.md    # 文字幅問題包括的分析
│   ├── font_processing_investigation_report.md     # フォント処理ライブラリ調査
│   └── ... (その他のドキュメント)
├── CLAUDE.md               # Claude Code向け開発ガイダンス
└── README.md               # このファイル
```

## 開発者向け情報

### 文字幅問題について
M+ 1mフォントとの文字幅互換性に関する詳細な調査と改善提案は `docs/character_width_comprehensive_analysis.md` を参照してください。

### 分析ツール
文字幅の詳細分析を行うスクリプトは `analysis/` ディレクトリに格納されています。使用方法は `analysis/README.md` を参照してください。

## ライセンス

フォント本体は、[Ubuntu Font License](https://ubuntu.com/legal/font-licence)で、生成スクリプトなどはMITライセンスとしています。


## 謝辞

Utataneフォントの合成にあたり[フォーク元のCicaフォント作成者](https://github.com/miiton)に感謝します。
また、以下の素晴らしいフォントを作成してくださった方々もありがとうございます。ありがたく使わせていただきます。

- [Ubuntu Font Family](http://font.ubuntu.com/)
- [やさしさゴシックボールドV2](https://booth.pm/ja/items/1833993)
- [M+ FONTS](https://mplus-fonts.osdn.jp/)
