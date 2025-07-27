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

Windows 11、fontforge 20230101で動作確認しています。
fontforgeは、[ここからダウンロード](https://fontforge.org/en-US/downloads/windows-dl/)してインストールします。
それから、fontToolsにも依存しているので`pip install fonttools`などでインストールが必要です。

ビルドは以下のコマンドで行います。

```ps1
git clone git@github.com:nv-h/Utatane.git
cd Utatane
# デフォルトのインストール先なので必要に応じて変更
& 'c:\Program Files (x86)\FontForgeBuilds\bin\fontforge' -lang=py -script .\utatane.py
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

## ディレクトリ構成

```
Utatane/
├── utatane.py              # メインのフォント生成スクリプト
├── sourceFonts/            # ソースフォントファイル
├── dist/                   # 生成されたフォントの出力先
├── tmp/                    # 一時ファイル保存先
├── test/                   # テスト関連ファイル
├── analysis/               # 文字幅分析スクリプト
│   ├── README.md
│   ├── analyze_mplus_widths.py
│   ├── comprehensive_width_check.py
│   └── ... (その他の分析スクリプト)
├── docs/                   # 開発ドキュメント
│   ├── README.md
│   ├── width_improvements.md    # 文字幅改善提案
│   ├── comprehensive_fix_proposal.md
│   └── ... (その他のドキュメント)
├── CLAUDE.md               # Claude Code向け開発ガイダンス
└── README.md               # このファイル
```

## 開発者向け情報

### 文字幅問題について
M+ 1mフォントとの文字幅互換性に関する詳細な調査と改善提案は `docs/width_improvements.md` を参照してください。

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
