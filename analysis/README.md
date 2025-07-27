# 文字幅分析スクリプト

このディレクトリには、Utataneフォントの文字幅問題を調査・分析するために作成されたスクリプトが含まれています。

## スクリプト一覧

### 基本分析
- **`analyze_mplus_widths.py`** - M+ 1m Regular フォントの文字幅を詳細分析
- **`comprehensive_width_check.py`** - M+ 1mとUtataneの全グリフ幅を包括的に比較

### 文字種別分析
- **`analyze_latin_greek.py`** - ラテン文字・ギリシャ文字の文字幅をM+と比較分析
- **`analyze_symbols.py`** - 記号類（○△②×✕等）の文字幅をM+と比較分析

### 現状確認
- **`check_current_widths.py`** - 現在のUtataneフォントとM+の文字幅を比較
- **`check_current_symbols.py`** - 現在のUtataneでの記号類の処理状況を確認
- **`check_current_latin_greek.py`** - 現在のUtataneでのラテン文字・ギリシャ文字処理を確認

### 調査・比較
- **`investigate_polars_usage.py`** - Polars等でのDataFrame表示における罫線使用状況を調査
- **`compare_cica_implementation.py`** - CicaとUtataneの実装を詳細比較

## 実行方法

全てのスクリプトは FontForge の Python 環境で実行する必要があります：

```bash
../fontforge/build/bin/fontforge -lang=py -script <script_name>.py
```

## 依存関係

- FontForge
- sourceFonts/ ディレクトリ内のフォントファイル
- dist/ ディレクトリ内の生成済みUtataneフォント（現状確認系スクリプト）

## 分析結果

詳細な分析結果とその解釈については、`../docs/` ディレクトリ内のドキュメントを参照してください。