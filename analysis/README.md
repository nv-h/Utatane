# フォント分析ツール（統合版）

analysis ディレクトリの分析スクリプトを整理し、共通機能を統合した CLI を追加しました。

## まとめ

- 新規: `font_analysis.py` に分析サブコマンドを統合
- 共通ユーティリティ: `font_analysis_utils.py`
- 既存の用途特化スクリプトはそのまま（比較・調査用の補助）

## 統合 CLI: font_analysis.py

FontForge の Python で実行してください。

例:
  fontforge -lang=py -script analysis/font_analysis.py <subcommand> [options]

サブコマンド:
- list-fonts: 利用可能フォント一覧
- info: 単一フォントの幅統計とサンプル
- compare: 2フォントの幅比較（不一致の抜粋と範囲別サマリ）
- ranges: Unicode 範囲別の幅分析（複数フォント）
- symbols: 記号カテゴリ別の幅分析
- mismatch: 幅パターンの不一致グリフ抽出（e.g. 500→1000）
- diagnose: 単一フォントの診断（基本情報/分布/サンプル）

使用例:

  # フォント一覧
  fontforge -lang=py -script analysis/font_analysis.py list-fonts

  # 単一フォントの統計
  fontforge -lang=py -script analysis/font_analysis.py info --font mplus --samples

  # 2フォント比較（Unicode名つき、最大100件）
  fontforge -lang=py -script analysis/font_analysis.py compare --base mplus --target utatane --names --max-display 100

  # 範囲別分析（ひらがな、カタカナ）
  fontforge -lang=py -script analysis/font_analysis.py ranges --fonts mplus,ubuntu --ranges ひらがな,カタカナ --max-samples 5

  # 記号カテゴリ（簡潔表示）
  fontforge -lang=py -script analysis/font_analysis.py symbols --fonts mplus,ubuntu,yasashisa --categories 幾何図形,矢印 --brief

  # 幅パターン（500→1000）
  fontforge -lang=py -script analysis/font_analysis.py mismatch --base mplus --target utatane --pattern 500 1000 --format markdown

  # 診断
  fontforge -lang=py -script analysis/font_analysis.py diagnose --font NotoSansMonoCJKjp-VF --max-samples 20

## 依存関係

- FontForge（サブモジュール版推奨）
- Python 3.x（FontForge付属）

フォント配置（例）:
- sourceFonts/: mplus, ubuntu, yasashisa 等
- dist/: 生成済み Utatane / 他

## 旧スクリプトの整理（後方互換なし）

残している専門用途スクリプト（今後も独立運用）:
- `collect_widths_for_doc.py`（Markdown表生成の補助）
- `compare_with_noto_sans_mono_vf.py` / `detailed_noto_comparison_analysis.py`（Notoとの詳細比較検証）
- `accurate_width_transformation_analysis.py` / `trace_processing_path.py`（処理経路・変換検証）
- `investigate_polars_usage.py` / `investigate_yasashisa_gothic_influence.py`（周辺検証）

## よくある問題

- フォントが見つからない: `sourceFonts/` または `dist/` の配置を確認
- FontForge エラー: `fontforge -lang=py -script` で実行しているか確認
- 文字化け: ターミナルのエンコーディング設定を確認

## 今後

- 診断/比較の CSV/JSON 出力
- 複数ジョブの一括実行（バッチ）
- 表示の最適化と可視化