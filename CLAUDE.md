# CLAUDE.md

このファイルは、このリポジトリでコードを操作する際のClaude Code (claude.ai/code)向けのガイダンスを提供します。

## プロジェクト概要

Utataneは、Ubuntu MonoとやさしさゴシックボールドV2を合成したプログラミング用等幅フォントです。FontForgeを使用してPythonスクリプトでフォント生成を行います。

## フォント生成アーキテクチャ

### フォント合成プロセス
1. **ベースフォント**: `sourceFonts/`ディレクトリの3つのフォントファミリを使用
   - Ubuntu Mono（欧文文字）: `UbuntuMono-Regular_modify.ttf`, `UbuntuMono-Bold_modify.ttf`
   - やさしさゴシックボールドV2（日本語文字）: `YasashisaGothicBold-V2_-30.ttf`, `YasashisaGothicBold-V2.ttf`
   - M+ 1m（罫線・ブロック要素）: `mplus-1m-regular.ttf`, `mplus-1m-bold.ttf`

2. **文字種別処理**:
   - 欧文文字: Ubuntu Monoをそのまま使用
   - 全角文字: やさしさゴシックを縮小して配置（`JP_A_RAT`比率で縮小）
   - 半角カタカナ: やさしさゴシックを縮小して半角幅に調整
   - 罫線素片(`0x2500-0x257F`): M+フォントを使用、半角化処理
   - ブロック要素(`0x2580-0x259F`): M+フォントを使用

3. **幅調整**:
   - 全角文字: `WIDTH` (1000) の幅
   - 半角文字: `WIDTH//2` (500) の幅
   - フォントメトリクス: `ASCENT=800`, `DESCENT=200`

## ビルドコマンド

### FontForge のセットアップ
このプロジェクトでは、FontForgeをサブモジュールとして含んでいます。初回セットアップ時は以下を実行：

```bash
# サブモジュールの初期化・取得
git submodule update --init --recursive

# FontForge のビルド
cd fontforge

# ビルド依存関係の確認（Ubuntu/Debian系）
# 以下パッケージがインストールされていることを確認：
# libjpeg-dev libtiff5-dev libpng-dev libfreetype-dev libgif-dev 
# libgtk-3-dev libxml2-dev libpango1.0-dev libcairo2-dev 
# libspiro-dev libwoff-dev python3-dev ninja-build cmake build-essential gettext

# ビルドディレクトリ作成・設定
mkdir -p build
cd build
cmake -GNinja ..

# ビルド実行（約5-10分）
ninja

# ビルド完了後、実行可能ファイルの確認
ls -la bin/fontforge
./bin/fontforge --version
```

### フォント生成
```bash
# FontForge でフォント生成（Windows）
& 'c:\Program Files (x86)\FontForgeBuilds\bin\fontforge' -lang=py -script .\utatane.py

# FontForge でフォント生成（Unix系、サブモジュール版）
./fontforge/build/bin/fontforge -lang=py -script ./utatane.py

# FontForge でフォント生成（Unix系、標準版）
fontforge -lang=py -script ./utatane.py
```

### 重要な実行時の注意
- `import fontforge`を含むPythonスクリプトは、必ず`fontforge -lang=py -script`で実行してください
- 現在は`./fontforge/build/bin/fontforge`にサブモジュールの最新ソースコードでビルドした実行ファイルを使用

### 依存関係
- FontForge がサブモジュールとして含まれています（ビルドが必要）
- `fonttools`パッケージ: `pip install fonttools`
- 生成されたフォントは`dist/`ディレクトリに保存されます

### テスト
```bash
# フォント表示テスト（test/ディレクトリ内）
python test/test_glyphs.py

# フォントバージョン間比較（FontForgeベース）
python test/font_compare.py --visual -f1 v1.2.1_Utatane-Regular -f2 v1.3.0_Utatane-Regular
```

## 重要な実装詳細

### フォント後処理（utatane.py:276-290）
`post_process()`関数で座標値の最適化を実行:
- `removeOverlap()`: 重複する輪郭を削除
- `round()`: 座標を整数値に丸める  
- `autoHint()`, `autoInstr()`: ヒンティング情報を自動生成

### xAvgCharWidth修正（utatane.py:440-469）
FontForgeで生成されたフォントのxAvgCharWidthが不正になる問題を、`ttx`コマンドを使用して修正します。

### デバッグモード
`DEBUG = True`に設定すると:
- 中間ファイル（`.sfd`, `.ttx`）が保持されます
- PDF形式の見本が生成されます

## ファイル構造
- `utatane.py`: メインのフォント生成スクリプト
- `sourceFonts/`: ソースフォントファイル
- `dist/`: 生成されたフォントの出力先
- `tmp/`: 一時ファイル保存先
- `fontforge/`: FontForgeのサブモジュール（最新版のソースコード）
- `test/`: テスト関連ファイル
  - `font_disp.txt`: フォント表示テスト用の文字セット（欧文、日本語、罫線、ブロック要素等）
  - `font_compare.py`: 統一フォント比較ツール（FontForge/matplotlib両対応）
  - `compare_fonts_fontforge.py`: FontForgeベースの詳細比較ツール（文字幅・配置可視化）
  - `test_glyphs.py`: フォント表示テストスクリプト

## 生成されるフォント
- `Utatane-Regular.ttf`: レギュラー体（Weight: 400）
- `Utatane-Bold.ttf`: ボールド体（Weight: 700）