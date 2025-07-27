# 罫線文字の半角/全角トレードオフ分析

## 現状の理解

Utataneでは意図的に罫線を半角化している理由：
> 罫線はM+へ置き換えて半角にする(コンソール表示などで半角を期待されることが多かった)

## メリット・デメリット比較

### 🔄 現在の方針：罫線を半角化

#### ✅ メリット
1. **Polars/DataFrame表示の正常化**
   - DataFrameの表組みが期待通りに表示される
   - セル幅の計算が正確になる

2. **TUIライブラリとの互換性**
   - Rich, Textual, CLI表示ツールが正常動作
   - ターミナルアプリケーションの表示崩れ防止

3. **既存エコシステムとの整合性**
   - 多くのフォントで半角実装が主流
   - ライブラリ側の期待値と一致

#### ❌ デメリット  
1. **M+ 1mとの非互換性**
   - 306件中105件が罫線関連の不整合
   - ベースフォントとの哲学的な乖離

2. **視覚的な違和感**
   - 罫線が他の記号より細く見える可能性
   - 全角文字との組み合わせ時の不整合

### 🔄 代替案：M+ 1m準拠（全角化）

#### ✅ メリット
1. **M+ 1mとの完全互換**
   - ベースフォントの設計思想を尊重
   - 一貫した文字幅ポリシー

2. **視覚的な統一感**
   - 他の全角記号との整合性
   - より重厚感のある罫線表示

#### ❌ デメリット
1. **DataFrame表示の破綻**
   - Polarsなどの表組みが崩れる可能性
   - レイアウト計算の狂い

2. **TUIライブラリの対応負担**
   - 既存アプリケーションの調整が必要
   - エコシステム全体への影響

## 実際の影響調査が必要な項目

### 検証したい具体例

1. **Polars DataFrame**
```python
import polars as pl
df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
print(df)  # 罫線の表示がどうなるか
```

2. **Rich Tables**
```python
from rich.table import Table
table = Table()
table.add_column("Name")
table.add_row("Alice")
# 罫線の表示確認
```

3. **その他のツール**
- `ls --color=always` での罫線
- `htop`, `btop` などのモニタリングツール
- Vim/Neovimのウィンドウ境界

## 第3の選択肢：設定可能な仕様

### ユーザー選択式の実装

```python
# utatane.py での設定例
BOX_DRAWING_STYLE = "halfwidth"  # or "fullwidth" or "mplus_compatible"

if BOX_DRAWING_STYLE == "halfwidth":
    # 現在の実装（Polars対応）
    width = int(WIDTH//2)
elif BOX_DRAWING_STYLE == "fullwidth": 
    # M+準拠
    width = WIDTH
elif BOX_DRAWING_STYLE == "mplus_compatible":
    # M+の幅をそのまま使用
    width = mplus_font[g.encoding].width if g.encoding in mplus_font else WIDTH
```

### フォントバリアント案

- `Utatane-Regular.ttf` (現在仕様：DataFrame対応)
- `Utatane-MPlus.ttf` (M+完全互換)
- `Utatane-Console.ttf` (コンソール最適化)

## 推奨される検証手順

1. **現状の影響範囲確認**
   - 実際にM+ 1mフォントでPolarsを使用
   - DataFrameの表示崩れの程度を測定

2. **他フォントとの比較**
   - Nerd Fonts等の人気フォントでの罫線幅
   - 業界標準的な実装の調査

3. **ユーザーニーズの調査**
   - DataFrame使用頻度 vs TUI使用頻度
   - ユーザーの優先度確認

## 結論

現在の半角化は**合理的な設計判断**ですが、M+ 1mとの互換性を重視するなら再検討の余地があります。ただし、変更する場合はDataFrame表示への影響を慎重に評価する必要があります。