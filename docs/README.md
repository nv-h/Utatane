# Utatane フォント開発ドキュメント

このディレクトリには、Utataneフォントの文字幅問題調査と改善提案に関するドキュメントが含まれています。

## ドキュメント一覧

### 主要ドキュメント

- **`width_improvements.md`** - 📋 **文字幅改善の最終提案書**
  - M+ 1mとの文字幅比較結果
  - 具体的な修正推奨案
  - 実装方法とコード例

### 詳細分析

- **`comprehensive_fix_proposal.md`** - 包括的な修正提案（初期分析）
  - 306件の不一致の詳細分析
  - 根本原因と修正戦略
  - ⚠️ 注意：最新推奨案は `width_improvements.md` を参照

- **`detailed_cica_comparison.md`** - Cicaプロジェクトとの詳細比較
  - 実装手法の比較
  - 参考にできる優れた実装
  - Utataneの独自の利点

- **`box_drawing_tradeoffs.md`** - 罫線文字の半角/全角トレードオフ分析
  - DataFrame表示 vs M+準拠のメリット・デメリット
  - Unicode East Asian Width問題
  - 第3の解決策案

## 読む順番の推奨

1. **`width_improvements.md`** - まずはこれを読んで全体像を把握
2. **`comprehensive_fix_proposal.md`** - より詳細な分析が必要な場合
3. **`detailed_cica_comparison.md`** - 他プロジェクトとの比較に興味がある場合
4. **`box_drawing_tradeoffs.md`** - 罫線問題の背景を理解したい場合

## 調査の背景

### 発見された問題
- M+ 1mフォントとUtataneの間で306件の文字幅不一致
- 一致率96.2%だが、重要な文字種で大きな不整合

### 重要な発見
- 多くの不一致は**DataFrame表示のための意図的な設計判断**
- 罫線や三点リーダーの半角化はPolars等との互換性のため
- ラテン文字・ギリシャ文字・キリル文字は既に適切に処理済み

### 最終推奨
- DataFrame表示に影響しない15件のみを修正
- 罫線・三点リーダーは現状維持
- 実用性を最大限に保ちつつM+互換性を部分的に向上

## 関連ファイル

- `../analysis/` - 分析に使用したスクリプト
- `../utatane.py` - 修正対象のメインスクリプト
- `../CLAUDE.md` - Claude Code向けの開発ガイダンス