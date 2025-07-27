# Utatane フォント開発ドキュメント

このディレクトリには、Utataneフォントの調査・改善提案に関するドキュメントが含まれています。

## ドキュメント一覧

### 📋 統合ドキュメント（推奨）

- **`character_width_comprehensive_analysis.md`** - **文字幅問題包括的分析・改善提案**
  - M+ 1mとの文字幅比較結果（306件の不一致分析）
  - 罫線表示のトレードオフ分析
  - Cicaプロジェクトとの実装比較
  - 段階的改善計画と具体的実装方法
  - os2_stylemapの重要性と修正提案

- **`font_processing_investigation_report.md`** - **フォント処理ライブラリ調査・移行検討レポート**
  - FontForge警告問題の詳細調査
  - 現代的フォント処理ライブラリ（FontTools等）の比較
  - 段階的移行戦略とリスク評価

## 読む順番の推奨

1. **`character_width_comprehensive_analysis.md`** - 文字幅問題の全体像と改善提案
2. **`font_processing_investigation_report.md`** - 技術的負債解消とライブラリ移行検討

## 調査の背景

### 文字幅問題の発見
- M+ 1mフォントとUtataneの間で306件の文字幅不一致
- 一致率96.2%だが、重要な文字種で大きな不整合

### FontForge警告問題の発見
- フォント生成時に1500件以上の「Internal Error (overlap)」
- 数値精度問題とアルゴリズム制約による

### 重要な発見
- **文字幅不一致**: 多くは**DataFrame表示のための意図的な設計判断**
- **FontForge警告**: 現代的なライブラリ移行で根本的解決が可能
- **os2_stylemap**: CicaとUtataneの実装差によるスタイル認識の違い

### 最終推奨
- **文字幅**: DataFrame表示に影響しない15件のみを修正
- **ライブラリ**: FontToolsへの段階的移行でエラー削減
- **スタイル設定**: os2_stylemapの明示的設定でOS互換性向上

## 関連ファイル

- `../analysis/` - 分析に使用したスクリプト
- `../utatane.py` - 修正対象のメインスクリプト
- `../CLAUDE.md` - Claude Code向けの開発ガイダンス