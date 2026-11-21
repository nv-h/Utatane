# Utatane フォント開発ドキュメント

このディレクトリには、Utataneフォントの調査・改善提案に関するドキュメントが含まれています。

## ドキュメント一覧

- **[Utataneの文字幅監査と設計方針案](character_width_audit.md)** — 完成TTFでの再集計、Unicode・OpenTypeの扱い、M+ 1mを基準とする幅ルールと検査手順。

### 既存の調査資料

- **`character_width_comprehensive_analysis.md`** - **文字幅問題包括的分析・改善提案**
  - M+ 1mとの文字幅比較の旧集計
  - 罫線表示のトレードオフ分析
  - Cicaプロジェクトとの実装比較
  - 段階的改善計画と具体的実装方法
  - os2_stylemapの重要性と修正提案

- **`font_processing_investigation_report.md`** - **フォント処理ライブラリ調査・移行検討レポート**
  - FontForge警告問題の詳細調査
  - 現代的フォント処理ライブラリ（FontTools等）の比較
  - 段階的移行戦略とリスク評価

## 読む順番の推奨

1. **[文字幅監査と設計方針案](character_width_audit.md)** — 文字幅の再集計と改善提案
2. **`font_processing_investigation_report.md`** - 技術的負債解消とライブラリ移行検討

## 調査の背景

### 文字幅問題の発見
- 完成TTFを比較すると、Utatane v1.3.2 Regularと同梱のM+ 1mは共通7,761文字中186文字で送り幅が異なる。
- Utatane v1.3.2のRegularとBoldで39文字の送り幅が異なる。

### FontForge警告問題の発見
- フォント生成時に1500件以上の「Internal Error (overlap)」
- 数値精度問題とアルゴリズム制約による

### 重要な発見
- **文字幅の差分**: コンソール向けに半角化した罫線105文字と、生成時の幅判定に由来する差分がある。
- **FontForge警告**: 現代的なライブラリ移行で根本的解決が可能
- **os2_stylemap**: CicaとUtataneの実装差によるスタイル認識の違い

### 最終推奨
- **文字幅**: [幅のルールと検証](character_width_audit.md#幅のルール)を参照
- **ライブラリ**: FontToolsへの段階的移行でエラー削減
- **スタイル設定**: os2_stylemapの明示的設定でOS互換性向上

## 関連ファイル

- `../analysis/` - 分析に使用したスクリプト
- `../utatane.py` - 修正対象のメインスクリプト
- `../CLAUDE.md` - Claude Code向けの開発ガイダンス
