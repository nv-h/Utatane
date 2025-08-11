# Utatane文字幅問題包括的分析・改善提案

## 概要

Utataneフォントの文字幅について、M+ 1mフォントとの比較分析、FontForgeメトリクス処理の問題調査、Cicaプロジェクトとの実装比較を通じて包括的に調査し、実用的な改善提案をまとめます。

## 全体状況

- **調査対象グリフ数**: 8,099グリフ
- **一致率**: 96.2% (7,793グリフ)
- **不一致**: 3.8% (306グリフ)
- **新発見**: FontForgeメトリクス処理に根本的な問題が存在

---

# Part 1: 文字幅不一致の詳細分析

## 不一致の分類と設計意図

### 1. DataFrame表示のための意図的設計（107件）

#### 罫線の半角化（105件） - 設計判断
```
例: ─ │ ┌ ┐ ┬ ┼ ┴ ═ ║ ╔ ╗ ╚ ╝ 等
M+ 1m: 1000 → Utatane: 500（半角化）
設計意図: 「罫線はM+へ置き換えて半角にする(コンソール表示などで半角を期待されることが多かった)」
```

**理由**: Polars等のDataFrameライブラリとの互換性確保
- DataFrameの表組みが期待通りに表示される
- セル幅の計算が正確になる
- TUIライブラリ（Rich, Textual等）との互換性

#### 三点リーダーの半角化（1件） - 設計判断
```
例: … HORIZONTAL ELLIPSIS
M+ 1m: 1000 → Utatane: 500（半角化）
用途: DataFrame内での省略表現
│ …        ┆ …          ┆ …      ┆ …       │
```

#### 一般句読点の半角化（1件） - 設計判断
```
例: ― EM DASH
M+ 1m: 1000 → Utatane: 500（半角化）
```

### 2. 実装済み文字種（15件） - 既に対処済み

#### ローマ数字の全角化（13件） - 実装済み
```
例: Ⅰ Ⅱ Ⅲ Ⅳ Ⅴ Ⅵ Ⅶ Ⅷ Ⅸ Ⅹ Ⅺ Ⅻ 等
現在の実装: WIDTH（全角）で処理
コード: `elif g.encoding in ROMAN_NUMERALS:`
```

#### 特定句読点（2件） - 実装済み
```
例: ‐ ― HYPHEN / EM DASH
現在の実装: WIDTH（全角）で処理
コード: `elif g.encoding in SPECIAL_PUNCTUATION:`
```

### 3. 判定ロジックの副作用（184件）

#### 制御図記号の全角化（37件）
```
例: ␊ ␌ ␍ ␎ ␏ ␐ ␑ ␒ ␓ ␔ ␕ ␖ ␗ ␘ ␙ ␚ ␛ ␜ ␝ ␞ ␟ ␠ ␡
M+ 1m: 500 → Utatane: 1000（全角化）
原因: `g.width > WIDTH * 0.7` の判定ロジックによる誤分類
```

#### その他の記号類（147件）
- **IPA音標文字**（14件）: 500→1000の全角化
- **ギリシャ記号**（8件）: 特殊記号の不整合
- **通貨記号**（7件）: 500→1000の全角化
- **拡張文字**（118件）: 様々な判定ミス

---

# Part 2: FontForgeメトリクス処理の根本的問題

## 発見された重大な問題

### 1. 文字幅調整処理の不整合

#### 問題のあるコード（現在の実装）
```python
# 元の手法
if g.width != width:
    g.transform(psMat.translate((width - g.width)/2, 0))  # 先に平行移動
    g.width = width                                      # 後で幅を設定
```

#### Cicaスタイルの処理（改良版）
```python
def precise_width_adjustment(glyph, target_width):
    if glyph.width != target_width:
        glyph.width = target_width
        bearing_avg = int((glyph.left_side_bearing + glyph.right_side_bearing) / 2)
        glyph.left_side_bearing = glyph.right_side_bearing = bearing_avg
    return glyph
```

### 2. FontForgeメトリクスの正しい理解

```
FontForgeの文字幅構成:
width = left_side_bearing + actual_glyph_width + right_side_bearing
```

### 3. 元の手法の問題点

1. **順序の問題**: transformしてからwidth設定により位置と幅設定が不一致
2. **サイドベアリング未調整**: transformで移動してもbearing値が更新されない
3. **精度の問題**: 小数点座標でレンダリングがぼやける可能性
4. **メトリクス不整合**: 実際の描画位置とメトリクス情報が一致しない

### 4. しかしCicaスタイルにも問題が存在

**句読点・括弧類への悪影響**:
- 句読点（。、）: 左寄りに配置されるべき → 中央配置で不自然
- 開き括弧（「（[{）: 右寄りに配置されるべき → 中央配置で間隔異常
- 閉じ括弧（」）]}）: 左寄りに配置されるべき → 中央配置で間隔異常

### 5. 現在の実装と改善の方向性

現在のUtataneでは`precise_width_adjustment()`関数が中央配置による強制調整を行っているため、句読点・括弧の本来の配置が失われています。

しかし、`improved_width_adjustment()`では**ベアリング比率を保持**するため、合成元フォント（やさしさゴシック等）で正しく配置されている句読点・括弧類は、その配置を維持したまま幅調整されます：

```python
# improved_width_adjustment の重要な特徴
if total_bearing > 0:
    left_ratio = glyph.left_side_bearing / total_bearing  # 元の比率を保持
    # → 句読点の左寄り、開き括弧の右寄り等が維持される
```

つまり、**追加の句読点・括弧配置調整機能は不要**で、`improved_width_adjustment()`だけで適切な日本語配置が実現できます。

---

# Part 3: 推奨される改善方法

## 元の手法を拡張した改善案

強制的な中央配置の危険性を避け、元の手法を改良してサイドベアリングも適切に調整：

```python
def improved_width_adjustment(glyph, target_width):
    """元の手法を拡張した安全な幅調整"""
    if glyph.width != target_width:
        # 現在のベアリング比率を保持
        total_bearing = glyph.left_side_bearing + glyph.right_side_bearing
        if total_bearing != 0:
            left_ratio = glyph.left_side_bearing / total_bearing
            right_ratio = glyph.right_side_bearing / total_bearing
        else:
            # ベアリングがゼロの場合は均等分散
            left_ratio = right_ratio = 0.5
            
        # 幅差分をベアリングに配分
        width_diff = target_width - glyph.width
        new_total_bearing = total_bearing + width_diff
        
        # 新しいベアリング値を計算
        new_left_bearing = int(new_total_bearing * left_ratio)
        new_right_bearing = int(new_total_bearing * right_ratio)
        
        # メトリクスを直接設定（transformは使用しない）
        glyph.left_side_bearing = new_left_bearing
        glyph.right_side_bearing = new_right_bearing
        glyph.width = target_width
    
    return glyph
```

### この改善案の利点

1. **メトリクス整合性**: FontForgeの原理に従った正しい処理
2. **配置保持**: 句読点・括弧の元の配置比率を維持
3. **transformなし**: より確実で予測可能な結果
4. **配置保持**: 合成元フォントの正しい句読点・括弧配置を自動的に維持

---

# Part 4: 他の問題箇所の調査結果

## 既存コードで発見された類似問題

### 1. add_smalltriangle()関数の問題
```python
# line 298-299: 重複設定と同様の問題
g.width = int(WIDTH//2)
g.left_side_bearing = g.right_side_bearing = int((g.left_side_bearing + g.right_side_bearing)/2)
g.width = int(WIDTH//2)  # 重複！
```

### 2. 罫線処理での潜在的問題
```python
# 罫線の半角化処理
g.transform(psMat.translate(-WIDTH//4, 0))  # 物理移動
# その後のメトリクス調整が不十分な可能性
```

### 3. 日本語フォント縮小処理
```python
g.transform(JP_REDUCTION_MAT)  # 縮小変換
g.transform(JP_REDUCTION_FIX_MAT_NOHEIGHT)  # 位置補正
# この後の幅調整でメトリクス不整合が発生する可能性
```

---

# Part 5: Cicaプロジェクトとの実装比較

## 共通点と相違点

### 共通の基本アプローチ
- **文字幅閾値**: 両方とも700を使用
- **2段階幅システム**: Cica(512/1024), Utatane(500/1000)
- **基本的な判定ロジック**: 類似

### Cicaの実装
```python
def align_to_center(_g):
    width = 1024 if _g.width > 700 else 512
    _g.width = width
    _g.left_side_bearing = _g.right_side_bearing = (_g.left_side_bearing + _g.right_side_bearing)/2
    return _g
```

### Utataneの実装（現在）
```python
if g.width > WIDTH * 0.7:
    width = WIDTH
else:
    width = int(WIDTH//2)

if g.width != width:
    g.transform(psMat.translate((width - g.width)/2, 0))
    g.width = width
```

## Cicaから学ぶべき改善点

### 1. os2_stylemapの明示的設定（実装済み）

Utataneでは既に実装済み：
```python
# os2_stylemapの明示的設定（実装済み）
style_name = _info.get('style_name')
if style_name == 'Regular':
    _font.os2_stylemap = 64      # Regular
elif style_name == 'Bold':
    _font.os2_stylemap = 32      # Bold
elif style_name == 'Italic':
    _font.os2_stylemap = 1       # Italic
elif style_name == 'Bold Italic':
    _font.os2_stylemap = 33      # Bold + Italic
```

### 2. タイムスタンプ付きログ（実装済み）

Utataneでは既に実装済み：
```python
def timestamped_log(message):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{now} {message}")
```

### 3. より安全な文字幅調整手法

Cicaの中央配置手法は参考になるが、句読点・括弧への配慮が必要。

---

# Part 6: 最終推奨案

## 基本方針

1. **DataFrame表示の完全維持**: 罫線の半角化は継続
2. **メトリクス処理の改善**: FontForgeの原理に従った正しい実装
3. **段階的改善**: 既存の安定性を保ちつつ改善

## 具体的な改善提案

### Phase 1: メトリクス処理の根本改善（最優先）

```python
def improved_width_adjustment(glyph, target_width):
    """FontForgeメトリクスを正しく理解した幅調整"""
    if glyph.width != target_width:
        # ベアリング比率を保持して調整
        total_bearing = glyph.left_side_bearing + glyph.right_side_bearing
        if total_bearing > 0:
            left_ratio = glyph.left_side_bearing / total_bearing
        else:
            left_ratio = 0.5  # デフォルトは均等分散
        
        width_diff = target_width - glyph.width
        new_total_bearing = total_bearing + width_diff
        
        glyph.left_side_bearing = int(new_total_bearing * left_ratio)
        glyph.right_side_bearing = int(new_total_bearing * (1 - left_ratio))
        glyph.width = target_width
    
    return glyph

# 使用箇所の変更
if width is not None:
    g = improved_width_adjustment(g, width)
```

### Phase 2: 他の問題箇所の修正

1. **add_smalltriangle()の重複設定除去**
2. **罫線処理のメトリクス整合性確保**
3. **日本語フォント縮小後の適切な幅調整**

### Phase 3: 設定の外部化（将来対応）

```python
# 設定可能な罫線描画モード
BOX_DRAWING_MODE = "console_optimized"  # 現在仕様（実装済み）
# BOX_DRAWING_MODE = "mplus_compatible"  # M+完全準拠
# BOX_DRAWING_MODE = "user_defined"      # カスタム設定
```

---

# Part 7: 期待される効果とリスク評価

## 期待される効果

### 1. フォント品質の向上
- **メトリクス整合性**: 文字間隔、カーソル位置、選択範囲の正確性向上
- **レンダリング品質**: 座標の整数化によるクリアな表示
- **テキストエディタ対応**: VSCode、Vim等での正確な表示

### 2. 現在の機能性維持
- **DataFrame表示**: 完全に現状維持（表示崩れなし）
- **TUI互換性**: Rich、Textual等のライブラリとの互換性維持
- **実用性**: 最大限に保持

### 3. 開発・デバッグの改善
- **予測可能性**: transformを使わない確実な処理
- **保守性**: FontForgeの原理に従った理解しやすいコード

## リスク評価

### 主要リスク
1. **微細な表示変化**: メトリクス変更による細かな表示差異
2. **互換性問題**: 既存のレイアウトに依存するアプリケーション

### 軽減策
1. **段階的適用**: 影響の少ない部分から開始
2. **詳細テスト**: 修正前後の比較検証
3. **ロールバック準備**: 問題発生時の復旧手順

---

# 結論

Utataneフォントの文字幅問題について包括的に調査した結果、以下の重要な発見がありました：

## 主要発見

1. **設計判断の妥当性**: DataFrame表示への配慮は適切な判断
2. **メトリクス処理の問題**: FontForge APIの不適切な使用による根本的な品質問題
3. **改善の方向性**: メトリクス処理を根本改善しつつ実用性を維持

## 推奨する行動

### 最優先（Phase 1）
1. **メトリクス処理の根本改善**: `improved_width_adjustment()`の導入
2. **既存問題の修正**: `add_smalltriangle()`等の修正

### 中期（Phase 2）
1. **包括的な品質向上**: 全ての変換処理でのメトリクス整合性確保
2. **テスト機能の拡充**: 自動品質検証の導入

### 長期（Phase 3）
1. **設定外部化**: ユーザーの多様なニーズに対応
2. **フォントバリアント**: DataFrame特化版とM+互換版の提供

この改善により、Utataneは現在の実用性を完全に維持しながら、技術的品質を大幅に向上させることができます。