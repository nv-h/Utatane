# フォント分析ツール

このディレクトリには、Utataneフォントの文字幅問題を調査・分析するための汎用的なツールが含まれています。

## 🚀 新機能: 統一された分析フレームワーク

### 共通ユーティリティ
- **`font_analysis_utils.py`** - 全スクリプト共通のユーティリティクラス・関数群
  - `FontAnalyzer`: フォント読み込み・幅比較・分析の統一インターフェース
  - `ReportGenerator`: 結果出力の統一フォーマット
  - エラーハンドリング・Unicode範囲定義などの共通機能

## 📊 分析スクリプト

### 基本分析（リファクタリング済み）
- **`analyze_mplus_widths.py`** - 任意フォントの文字幅を詳細分析（汎用化済み）
  ```bash
  # M+ 1mの分析（デフォルト）
  fontforge -lang=py -script analyze_mplus_widths.py
  
  # Utataneフォントの分析
  fontforge -lang=py -script analyze_mplus_widths.py utatane
  
  # サンプル文字非表示
  fontforge -lang=py -script analyze_mplus_widths.py mplus false
  ```

- **`comprehensive_width_check.py`** - 2フォント間の全グリフ幅包括比較（汎用化済み）
  ```bash
  # M+ vs Utatane（デフォルト）
  fontforge -lang=py -script comprehensive_width_check.py
  
  # Ubuntu vs Yasashisa
  fontforge -lang=py -script comprehensive_width_check.py --base ubuntu --target yasashisa
  
  # Unicode文字名付きで表示
  fontforge -lang=py -script comprehensive_width_check.py --names --max-display 100
  ```

- **`analyze_symbols.py`** - 記号類の文字幅を複数フォント間で比較（汎用化済み）
  ```bash
  # デフォルト（mplus, ubuntu, yasashisa）
  fontforge -lang=py -script analyze_symbols.py
  
  # 特定フォントのみ
  fontforge -lang=py -script analyze_symbols.py --fonts mplus,utatane
  
  # 特定カテゴリのみ
  fontforge -lang=py -script analyze_symbols.py --categories 幾何図形,矢印
  
  # 簡潔な出力
  fontforge -lang=py -script analyze_symbols.py --brief
  ```

- **`analyze_ranges.py`** - Unicode範囲別文字分析（新規）
  ```bash
  # 利用可能な範囲一覧を表示
  fontforge -lang=py -script analyze_ranges.py --list-ranges
  
  # ラテン・ギリシャ文字のみ分析
  fontforge -lang=py -script analyze_ranges.py --ranges 'ギリシャ,基本ラテン拡張'
  
  # 特定フォント間の範囲比較
  fontforge -lang=py -script analyze_ranges.py --fonts 'mplus,utatane' --ranges 'ひらがな,カタカナ'
  ```

### 特化分析スクリプト（一部汎用化済み）
以下のスクリプトは特定の目的に特化した分析を行います：

#### 汎用化済みツール
- **`diagnose_noto_font.py`** - 任意フォントの詳細診断（汎用化済み）
  ```bash
  # Utataneフォントの診断
  fontforge -lang=py -script diagnose_noto_font.py --font utatane --max-samples 50
  
  # サンプル非表示での診断
  fontforge -lang=py -script diagnose_noto_font.py --font mplus --no-samples
  ```

- **`generate_misclassified_glyph_list.py`** - 幅不一致グリフレポート生成（汎用化済み）
  ```bash
  # M+ 500 → Utatane 1000 の不一致（デフォルト）
  fontforge -lang=py -script generate_misclassified_glyph_list.py
  
  # Ubuntu vs Yasashisaの比較
  fontforge -lang=py -script generate_misclassified_glyph_list.py --base ubuntu --target yasashisa
  
  # CSV形式で出力
  fontforge -lang=py -script generate_misclassified_glyph_list.py --format csv
  ```

#### 特化ツール（固定フォント対応）
- **`compare_with_noto_sans_mono.py`** - Noto Sans Mono CJK JPとの詳細比較分析
- **`compare_with_noto_sans_mono_vf.py`** - Noto Sans Mono可変フォント版との比較
- **`compare_cica_implementation.py`** - Cicaフォントとの実装比較
- **`investigate_polars_usage.py`** - DataFrameでの罫線使用状況調査
- **`investigate_yasashisa_gothic_influence.py`** - やさしさゴシックの影響調査
- **`accurate_width_transformation_analysis.py`** - 幅変換の精度分析
- **`analyze_judgment_logic_side_effects.py`** - 判定ロジックの副作用分析
- **`detailed_noto_comparison_analysis.py`** - Noto詳細比較分析
- **`trace_processing_path.py`** - 処理パスの追跡

## 実行方法

### 基本的な実行方法
全てのスクリプトは FontForge の Python 環境で実行する必要があります：

```bash
# サブモジュール版FontForgeを使用（推奨）
../fontforge/build/bin/fontforge -lang=py -script <script_name>.py

# システム版FontForgeを使用
fontforge -lang=py -script <script_name>.py
```

### 新しい統一フレームワークの利点

1. **パラメータ化**: フォント名や出力オプションをコマンドライン引数で指定可能
2. **エラーハンドリング**: 一貫したエラー処理と分かりやすいエラーメッセージ
3. **出力の統一**: 結果表示形式が統一され、比較しやすい
4. **拡張性**: 新しいフォントや分析項目を簡単に追加可能

### 実行例

```bash
# 基本的な分析
../fontforge/build/bin/fontforge -lang=py -script analyze_mplus_widths.py

# より詳細な比較
../fontforge/build/bin/fontforge -lang=py -script comprehensive_width_check.py --base mplus --target utatane --names

# 記号類の問題調査
../fontforge/build/bin/fontforge -lang=py -script analyze_symbols.py --categories 幾何図形,演算記号・×類
```

## 依存関係

### 必須
- FontForge（サブモジュール版推奨）
- Python 3.x（FontForge付属）

### フォントファイル
- `sourceFonts/` ディレクトリ内のフォントファイル：
  - `mplus-1m-regular.ttf` - M+ 1m Regular
  - `UbuntuMono-Regular_modify.ttf` - Ubuntu Mono Regular
  - `YasashisaGothicBold-V2_-30.ttf` - やさしさゴシックボールド V2
- `dist/` ディレクトリ内の生成済みフォント：
  - `Utatane-Regular.ttf` - 生成済みUtataneレギュラー

### オプション（拡張機能用）
- `unicodedata` - Unicode文字名取得（Python標準ライブラリ）

## 🔧 カスタマイズ

### 新しいフォントの追加

#### 自動検索機能
新しいフォントファイルを `sourceFonts/` や `dist/` ディレクトリに配置するだけで、自動的に検出され利用可能になります。

#### 手動でフォントパスを追加
`font_analysis_utils.py` の `get_default_font_paths()` 関数にエイリアスを追加：

```python
def get_default_font_paths() -> Dict[str, str]:
    return {
        'mplus': './sourceFonts/mplus-1m-regular.ttf',
        'ubuntu': './sourceFonts/UbuntuMono-Regular_modify.ttf',
        'yasashisa': './sourceFonts/YasashisaGothicBold-V2_-30.ttf',
        'utatane': './dist/Utatane-Regular.ttf',
        'my_font': './path/to/my_custom_font.ttf'  # カスタムフォントのエイリアス
    }
```

#### 利用可能なフォント確認
```bash
# 現在利用可能な全フォントを表示
fontforge -lang=py -script font_analysis_utils.py --list-fonts
```

### 新しい記号カテゴリの追加
`FontAnalyzer.get_symbol_categories()` メソッドにカテゴリを追加：

```python
@staticmethod
def get_symbol_categories() -> Dict[str, List[int]]:
    return {
        # 既存のカテゴリ...
        "新カテゴリ": [0x1234, 0x5678, ...]  # 新しいカテゴリを追加
    }
```

## 📝 分析結果の解釈

分析結果とトラブルシューティングについては、プロジェクトルートの `CLAUDE.md` および `docs/` ディレクトリ内のドキュメントを参照してください。

### よくある問題
- **フォントが見つからない**: `sourceFonts/` または `dist/` ディレクトリのパスを確認
- **FontForgeエラー**: `fontforge -lang=py -script` で実行していることを確認
- **文字化け**: ターミナルのエンコーディング設定を確認

## 📋 移行完了した機能

### ✅ **基本分析の汎用化**
- `analyze_mplus_widths.py`, `comprehensive_width_check.py`, `analyze_symbols.py`
- 任意のフォント組み合わせに対応、柔軟なパラメータ指定

### ✅ **新規汎用ツール**
- `analyze_ranges.py`: Unicode範囲別分析（ラテン・ギリシャ文字分析を統合）
- `diagnose_noto_font.py` → 汎用フォント診断ツール
- `generate_misclassified_glyph_list.py` → 汎用幅不一致レポートツール

### ✅ **動的フォント検索**
- dist/ディレクトリの全バージョンフォント（24個）を自動検出
- test/font_compare.pyの手法を採用した柔軟なフォント管理

### ✅ **重複機能の整理**
- **削除**: `check_current_*`系スクリプト（3個）、`analyze_latin_greek.py`、`mplus_noto_width_differences.py`
- **統合**: 削除機能は汎用化されたツールで完全代替可能

### ✅ **統一された開発体験**
- 全ツールで一貫したコマンドライン引数体系
- 分かりやすいエラーメッセージと自動提案機能
- `--help`オプションによる詳細な使用法説明

## 🚧 今後の予定

- [ ] 特化分析スクリプトの段階的リファクタリング
- [ ] バッチ分析機能（複数スクリプトの一括実行）
- [ ] 結果のCSV/JSON出力機能
- [ ] 分析結果の可視化ツール（オプション）
- [ ] CI/CDでの自動フォント品質チェック統合