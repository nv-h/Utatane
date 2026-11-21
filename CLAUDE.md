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
`uv run` 経由で実行します。`uv run` が `.venv` の `ttx`（fontTools）を PATH に入れるため、FontForge から呼ぶ `ttx` が見つかります。`ttx` が無い場合、`utatane.py` は起動時に止まります。

```bash
# Python 依存（fonttools, matplotlib）のインストール
uv sync

# FontForge でフォント生成（Windows、64bit版インストーラーの既定の場所）
uv run 'C:\Program Files\FontForgeBuilds\bin\fontforge.exe' -lang=py -script .\utatane.py

# FontForge でフォント生成（Unix系、サブモジュール版）
uv run ./fontforge/build/bin/fontforge -lang=py -script ./utatane.py

# FontForge でフォント生成（Unix系、標準版）
uv run fontforge -lang=py -script ./utatane.py
```

### グリフ形状比較ツール
M+、やさしさゴシック、Utataneの3フォントでグリフ形状を詳細比較できます：

```bash
# 基本的な使い方（高影響グリフ32件）
./glyph-compare.sh

# カテゴリ指定
./glyph-compare.sh --category control --category currency

# 判定ロジック副作用の全184件
./glyph-compare.sh --priority all

# 特定グリフの詳細比較
./glyph-compare.sh --unicode U+2400 --unicode U+20A9

# テストファイルから選択
./glyph-compare.sh --from-testfile --section "日本語文字（ひらがな・カタカナ・漢字）"

# カテゴリ一覧
./glyph-compare.sh --list-categories
```

### 重要な実行時の注意
- `import fontforge`を含むPythonスクリプトは、必ず`fontforge -lang=py -script`で実行してください
- Unix系では`./fontforge/build/bin/fontforge`にサブモジュール（FontForge 20251009）からビルドした実行ファイルを使用
- Windowsでは FontForge 20251009 の公式ビルド（`C:\Program Files\FontForgeBuilds`）を使用

### 依存関係
- FontForge がサブモジュールとして含まれています（Unix系はビルドが必要）
- Python パッケージは `pyproject.toml` と `uv.lock` で管理し、`uv sync` でインストールします
  - `fonttools`: xAvgCharWidth 修正の `ttx`、分析スクリプト
  - `matplotlib`: グリフ形状比較用
  - `ruff`（開発用）: リンター・フォーマッター。`uv run ruff check` と `uv run ruff format` で実行（設定は `pyproject.toml` の `[tool.ruff]`。Markdown内のコードは整形しない）
- 生成されたフォントは`dist/`ディレクトリに保存されます

### テスト
```bash
# 生成済みフォント（dist/）のグリフ検査（FontForge の Python で実行）
fontforge -lang=py -script test/test_glyphs.py

# 送り幅の方針チェック（fontTools）
uv run python analysis/check_width_policy.py dist/Utatane-Regular.ttf dist/Utatane-Bold.ttf

# フォントバージョン間比較（FontForgeベース）
python test/font_compare.py --visual -f1 v1.2.1_Utatane-Regular -f2 v1.3.0_Utatane-Regular
```

## 重要な実装詳細

### フォント後処理（`post_process()`）
`post_process()`関数で座標値の最適化を実行:
- `removeOverlap()`: 重複する輪郭を削除
- `round()`: 座標を整数値に丸める  
- `is_quadratic = True`: TrueType の2次曲線へ書き出し前に変換する（書き出し時の変換に任せると、ごく小さい輪郭ができて残るため）
- `remove_degenerate_contours()`: 描画に寄与しない輪郭（点が2つ以下、または縦横2単位以下）を取り除く
- TrueType のヒンティング命令は付けない（以前は3次曲線のまま `autoInstr()` を呼んでいて何も生成されておらず、配布フォントは命令なしだった。それに合わせている）。`--ttf-hinting`（または `TTF_HINTING = True`）で `autoHint()` / `autoInstr()` を実行して付けられる

### 迷子の点（`remove_degenerate_contours()`）
`YasashisaGothicBold-V2_-30.ttf` には、作成時の FontForge の Change Weight（-30）で残った1点だけの輪郭が約7万5千個あります（元の `YasashisaGothicBold-V2.ttf` には無い。同じ処理で再現する）。描画はされませんが、グリフの範囲を押し広げ、ファイルを大きくするため、和文の取り込み時と後処理で取り除いています。

### xAvgCharWidth修正（`fix_xAvgCharWidth()`）
FontForgeで生成されたフォントのxAvgCharWidthが不正になる問題を、`ttx`コマンドを使用して修正します。`ttx`が失敗した場合はその場でエラーになります。

### Windows（GDI）で欠けないための縮小（`fit_within_win_metrics()`）
GDI は usWinAscent / usWinDescent（800 / 200）の外側を描かないため、その範囲からはみ出す入力可能な文字（ベトナム語の大文字など約400字）を、ベースラインと字面の中心を基準に等倍で縮めます。行の高さ（win の値）は変えません。
- 縮めずに元の字形のまま生成するには、`utatane.py` の `FIT_WIN_METRICS` を `False` にするか、`--no-fit-win-metrics` を付けて実行します（例: `uv run fontforge -lang=py -script ./utatane.py --no-fit-win-metrics`）
- はみ出しの一覧は `uv run python analysis/win_clipping_report.py`（`tmp/win-clip/win_clipping.html`）で確認できます

### 版の比較（`analysis/compare_builds_report.py`）
生成したフォントの版どうし（例: 変更前・今回・`--ttf-hinting` 版）を、GDI の描画（グレースケール / ClearType、サイズ別、差分つき）・ブラウザーの描画・字形が変わった文字で比べる HTML を作ります。
`uv run python analysis/compare_builds_report.py --variant 変更前=<dir> --variant 今回=<dir> --output tmp/compare/compare.html`

### デバッグモード
`DEBUG = True`に設定すると:
- 中間ファイル（`.sfd`, `.ttx`）が保持されます
- PDF形式の見本が生成されます

## ファイル構造
- `utatane.py`: メインのフォント生成スクリプト
- `sourceFonts/`: ソースフォントファイル
- `dist/`: 生成されたフォントの出力先
- `tmp/`: 一時ファイル保存先
- `fontforge/`: FontForgeのサブモジュール（リリース 20251009 のソースコード）
- `test/`: テスト関連ファイル
  - `font_disp.txt`: フォント表示テスト用の文字セット（欧文、日本語、罫線、ブロック要素等）
  - `font_compare.py`: 統一フォント比較ツール（FontForge/matplotlib両対応）
  - `compare_fonts_fontforge.py`: FontForgeベースの詳細比較ツール（文字幅・配置可視化）
  - `glyph_data_extractor.py`: グリフデータ抽出スクリプト（FontForge用）
  - `glyph_visualizer.py`: グリフ可視化スクリプト（matplotlib用）
  - `test_glyphs.py`: フォント表示テストスクリプト
- `glyph-compare.sh`: グリフ形状比較統合ツール（3フォント対応、PDF出力）

## 生成されるフォント
- `Utatane-Regular.ttf`: レギュラー体（Weight: 400）
- `Utatane-Bold.ttf`: ボールド体（Weight: 700）