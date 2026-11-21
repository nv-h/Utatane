# Utataneの文字幅と検証

Utataneは半角500・全角1000の1:2グリッドを使う。RegularとBoldの既定送り幅を揃え、幅に選択の余地がある文字は同梱のM+ 1m 1.063aを参照する。

## 仕様と実装例

- **Unicode** の East Asian Width（EAW）は文字の既定の幅分類。`F/W` は全角、`H/Na` は半角の設計に使える。`A` は文脈依存で、`N` にもフォントごとの設計余地がある。UAX #11はフォントの送り幅を規定しておらず、端末への適用にも調整が要る。非スペーシング結合記号の送りはEAWとは別に扱う。[Unicode UAX #11](https://www.unicode.org/reports/tr11/tr11-44.html)
- **OpenType** では `cmap` が文字をグリフに対応付け、`hmtx` が既定の横送り幅と左サイドベアリングを持つ。字形の外接範囲は送り幅と独立しており、合字や `fwid` / `hwid` などを適用した結果はシェーピング後に測る。[cmap](https://learn.microsoft.com/en-us/typography/opentype/spec/cmap)・[hmtx](https://learn.microsoft.com/en-us/typography/opentype/spec/hmtx)・[幅を変更するOpenType機能](https://learn.microsoft.com/en-us/typography/opentype/spec/features_fj#tag-fwid)
- **端末** は1列・2列などの割り当てを個別に決める。たとえばxtermは既定で `cjkWidth` が無効で、有効にすると `A` を2列として扱う。PolarsはUTF-8のフォーマットで罫線素片を使う。実際の表組みは、アプリの文字列幅計算、端末の列割り当て、フォントの描画を合わせて確かめる。[xtermのcjkWidth](https://invisible-island.net/xterm/manpage/xterm.html)・[Polarsの表組み仕様](https://docs.pola.rs/api/python/stable/reference/api/polars.Config.set_tbl_formatting.html)

| フォント | 横送り幅の方針 |
| --- | --- |
| 同梱 M+ 1m 1.063a | 1000 UPM。Unicode `cmap` の7,761文字は500が1,487、1000が6,274。RegularとBoldで全件一致。収録する罫線105字とローマ数字32字、矢印45字は1000。ブロック要素32字のうち29字は500、`░▒▓` は1000。制御図記号39字は500。 |
| M PLUS 1 Code | M PLUS 1の全角和文とCode Latin 50の半角英数字を組み合わせる。[M+ FONTS公式](https://mplusfonts.github.io/) |
| Noto Sans Mono CJK JP VF 2.004 | 配布元が明示するMonoの範囲は既定のASCII半角。実測した既定インスタンスではASCIIは500、漢字やかなの代表は1000、`á` は563、`Ḿ` は812。M+ 1mと異なる用途の比較資料として使える。[Noto CJK Sansの配布仕様](https://github.com/notofonts/noto-cjk/blob/main/Sans/README.md) |
| 源ノ等幅（Source Han Mono） | Adobeの設計仕様は0・667・1000。欧文の1セルに対する和文の幅は約1.5セル。日本語と欧文を混植する等幅フォントにも幅比の選択肢がある。[Adobeの設計解説](https://ccjktype.fonts.adobe.com/2019/05/source-han-mono-v1000.html) |

## 既存調査の再検証

FontTools 4.63.0で完成TTFのUnicode `cmap` と `hmtx` を比較した。Utataneはタグ `Utatane_v1.3.1` と作業ツリー `0fa670a`（バージョン表記1.3.2）をFontForge 20251009で隔離ビルドし、ローカルにあった同バージョンのTTFと比較した。v1.3.1 Regularとv1.3.2 Regular/Boldは全収録コードポイントの送り幅がそれぞれ一致した。Notoはローカルの `NotoSansMonoCJKjp-VF.ttf`（Version 2.004、`wght=400` が既定）。比較対象はいずれも1000 UPM。

| 比較（左 → 右） | 共通コードポイント | 一致 | 差分 |
| --- | ---: | ---: | ---: |
| M+ 1m → Utatane v1.3.1 Regular | 7,761 | 7,550（97.28%） | 211 |
| M+ 1m → Utatane v1.3.2 Regular | 7,761 | 7,575（97.60%） | 186 |
| M+ 1m → Utatane v1.3.2 Bold | 7,761 | 7,553（97.32%） | 208 |
| Noto → Utatane v1.3.1 Regular | 6,920 | 6,335（91.55%） | 585 |
| Noto → Utatane v1.3.2 Regular | 6,920 | 6,318（91.30%） | 602 |
| M+ 1m → Noto | 6,810 | 6,371（93.55%） | 439 |
| Utatane v1.3.2 Regular → Bold | 8,635 | 8,596（99.55%） | 39 |

### 再現した点と訂正点

- **罫線105字の半角化は意図的。** M+ 1mで1000の罫線を、生成時に500のセル用に切り出している。v1.3.1とv1.3.2で M+ 1mの1000から500に変わる残り2字は `…` U+2026 と `―` U+2015。`―` は HORIZONTAL BARで、EM DASHは `—` U+2014。現行の和文処理はU+2015に1000を指定する一方、Ubuntu Mono側にも500で収録されており、完成TTFは500。和文側の条件だけでは完成品の幅を判断できない。[生成コード](../utatane.py#L376)
- **旧集計の8,099はM+ 1mの全グリフ数。** 旧ツールの `g.encoding` で比較すると、Unicodeの最大値U+10FFFFを超える内部スロットがM+側だけで338件含まれる。U+110150・U+110151はこれに該当する。旧方式でv1.3.1を測ると8,099件中291差分で、記載の306件は再現しなかった。一方、Noto対Utataneの8,622件中816差分、M+対Notoの6,647件中535差分は同じ旧方式で再現した。フォント間で内部スロット番号を照合していたため、これらの値や「業界コンセンサス違反」の判定は更新が必要。[旧ツール](../analysis/font_analysis_utils.py#L68)・[FontForgeのencoding定義](https://fontforge.org/docs/scripting/python/fontforge.html#fontforge.glyph.encoding)
- **`g.width > WIDTH * 0.7` の副作用は実在する。** 現行RegularではM+が500、Utataneが1000の文字が79件あり、うち36件が制御図記号。RegularとBoldで幅の異なる39件はすべてEAW `N` で、Regularが500、Boldが1000。39件のうちM+にある22件は全て500で、残る17件はM+に未収録。`ɝ` U+025Dや `ϒ` U+03D2はv1.3.1 Regularの1000からv1.3.2 Regularの500に変わったが、Boldは1000のまま。ローマ数字はv1.3.1の時点でM+との共通32字すべて1000で一致しており、「15件だけ修正」を現行版の対象数としては使えない。[現行の幅判定](../utatane.py#L440)
- **中央寄せの不具合は字形ごとに検証する。** FontForge 20251009の単純な矩形（advance 800、左100、右200）を `translate(50, 0)` で移動すると、advance 850、左150、右200になった。その後に `width=900` を代入すると、左150、右250で整合した。旧資料の「平行移動でベアリングが更新されない」は再現しない。ただし、幅指定だけでは輪郭は縮まらない。v1.3.2 Regularの `ɝ` はadvance 500に対し輪郭のx範囲が−63〜546で、両側にはみ出す。`₩` と `␣` の輪郭幅も現状は約852と664あり、500化には輪郭の調整または適切な字形への差し替えが要る。[FontForgeのメトリクス解説](https://fontforge.org/docs/tutorial/editexample5.html)・[現在の幅調整関数](../utatane.py#L153)

## 幅のルール

- 非スペーシング結合記号は0。罫線・`…`・`―`・`░▒▓` は端末向けに500。エン空白は500、エム空白は1000。
- Unicode East Asian Widthの `F/W` は1000、`H/Na` は500。`₩` は500、`〈〉` とテキスト表示の `⚪⚫` は1000。`〈〉` は正準等価の `〈〉` と輪郭・余白を揃える。`⚪⚫` を1セルに割り当てるxterm.jsの表示では後続文字と干渉しうる。
- `A/N` は同梱のM+ 1mを参照。M+未収録のラテン・ギリシャ・キリル文字は500とし、その他は既存の幅を使う。`₩` と制御図記号はM+の半角用輪郭を採用する。[幅ルール](../width_policy.py)

## 生成結果の検証

RegularとBoldの8,635コードポイントが同じ幅表に合格した。v1.3.2から送り幅が変わったのは両ウェイトの和集合で285字。Polars 1.44.2の比較表では、Chromiumで縦罫線が揃い、xterm.js 6.1.0-beta.337（`customGlyphs: false`）で半角化した文字と直後のASCII文字の干渉が解消した。`post.isFixedPitch`、PANOSE、OS/2の分類値は別のメトリクスであり、実際の送り幅の検査には `hmtx` を使う。[OpenType hmtx](https://learn.microsoft.com/en-us/typography/opentype/spec/hmtx)・[OpenType OS/2](https://learn.microsoft.com/en-us/typography/opentype/spec/os2)

生成済みのフォントはリポジトリ直下から次のコマンドで検査できる。依存パッケージはFontTools。

```sh
python -m analysis.check_width_policy dist/Utatane-Regular.ttf dist/Utatane-Bold.ttf
```

4フォントの比較HTMLは、下記の生成スクリプトに `--overview --baseline 0fa670a` を追加し、`--previous` にそのコミットのTTFを指定すると再作成できる。Regular/Boldの和集合で、修正前後の送り幅差は285字、輪郭のみの差は159字、収録差は0字。修正後とNoto・M PLUS 1 Codeの少なくとも一方に共通収録され、送り幅が異なる文字は600字。対象は符号化されたグリフで、シェーピングの差は代表例で確認する。

## 結合記号の位置と送り幅

公式配布のNoto Sans Mono CJK JP 2.004とM PLUS 1 Code 1.100を、Utataneの前回案・修正後と比較した。Utataneの141字および参照先との共通文字（Notoは7字、M PLUS 1 Codeは25字）は、既定の送り幅がすべて0。ChromiumとHarfBuzzでは、NotoとM PLUS 1 Codeの `x`＋U+0301 は全体の送りが500のまま、アクセントが次のセル側にも描かれる。送り幅と輪郭の位置をそれぞれ確認する。[Noto公式配布](https://github.com/notofonts/noto-cjk/blob/main/Sans/README.md)・[M PLUS 1 Code公式配布](https://fonts.google.com/specimen/M+PLUS+1+Code)

- ラテン文字に付く上付き記号は、基底文字と結合記号にアンカーを設定する。HarfBuzzで `x`＋U+0301＋U+0308 と `ẍ`＋U+0301 の輪郭が重ならず、幅500を保つことをRegular・Boldで確認した。
- 2文字にまたがる記号（U+035C〜U+0362の収録分）はセル境界に寄せる。`a`＋U+0361＋`b` は幅1000のまま、記号の輪郭が `a` と `b` の両方にかかる。
- `か`＋U+3099と `が` はともに1000。`あ`＋U+3099も1000で、濁点は右上に描く。半角濁点U+FF9Eはスペーシング文字として500。ラテン上付き記号以外の組み合わせの一括位置調整や、縦組みの表示は未検証。

[HTML生成スクリプト](../analysis/compare_combining_marks.py)は各ウェイトのTTFと2つの比較用可変フォントを受け取り、記号単体の `hmtx` とブラウザー上の文字列幅を表示する。文字名は折り返し、未収録の組み合わせは明示する。

```sh
python -m analysis.compare_combining_marks --previous PREV_REGULAR.ttf PREV_BOLD.ttf --utatane NEW_REGULAR.ttf NEW_BOLD.ttf --noto NOTO.ttf --mplus MPLUS.ttf --output combining-marks.html
```

## 他の日本語等幅フォントとの比較

Regular（可変フォントは既定インスタンス）の `cmap` → `hmtx` を調べ、各フォントのASCII `A` の送り幅を1セルとして換算した。`─│` と `░▒▓` はそれぞれのグループ内で同じ幅だった。`—` は対象の文字が未収録であることを示す。

| フォント | `─│` | `░▒▓` | `―` | `…` | `〈〉` | 結合濁点 U+3099 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Utatane 修正候補 | 1 | 1 | 1 | 1 | 2 | 0 |
| M+ 1m 1.063a | 2 | 2 | 2 | 2 | 1 | 2 |
| M PLUS 1 Code 1.100 | 1 | 1 | — | 1 | — | 0 |
| Cica 5.0.3 | 1 | 1 | 1 | 1 | 1 | 2 |
| HackGen 2.10.0 | 2 | 2 | 2 | 2 | 2 | 2 |
| HackGen Console 2.10.0 | 1 | 1 | 1 | 1 | 2 | 2 |
| UDEV Gothic 2.2.0 | 1 | 1 | 2 | 1 | — | 2 |
| UDEV Gothic JPDOC 2.2.0 | 2 | 1 | 2 | 2 | — | 2 |
| PlemolJP 3.1.0 | 2 | 1 | 2 | 2 | 2 | 2 |
| PlemolJP Console 3.1.0 | 1 | 1 | 1 | 1 | 2 | 2 |
| Noto Sans Mono CJK JP 2.004 | 2 | 2 | 2 | 2 | 2 | 0 |
| MS Gothic 5.32 | 2 | 1 | 2 | 2 | — | 2 |
| BIZ UDGothic 2.02 | 2 | — | 2 | 2 | — | — |

Cica、HackGen、UDEV Gothic、PlemolJPは公式配布ZIPのTTF、Windowsの2種はインストール済みのTTCを使った。NotoとM PLUS 1 Codeは結合記号の比較と同じ公式TTFを使った。[Cica 5.0.3](https://github.com/miiton/Cica/releases/tag/v5.0.3)・[HackGen 2.10.0](https://github.com/yuru7/HackGen/releases/tag/v2.10.0)・[UDEV Gothic 2.2.0](https://github.com/yuru7/udev-gothic/releases/tag/v2.2.0)・[PlemolJP 3.1.0](https://github.com/yuru7/PlemolJP/releases/tag/v3.1.0)

- Cica、HackGen Console、UDEV Gothic通常版、PlemolJP Consoleでは、U+2500〜U+257Fの128字すべてが1セル。HackGenとPlemolJPの通常版は128字すべて2セル。MS Gothicは `─│` を含む32字が2セル、残る96字は1セルだった。JPDOCの `…` の幅は、UDEV Gothicの公式説明にも記載がある。[UDEV Gothicのバリエーション](https://github.com/yuru7/udev-gothic#バリエーション)
- `␣` はCica・PlemolJP・Notoで1セル、HackGen Console・MS Gothic・BIZ UDGothicで2セルだった。PlemolJPはv3.1.0でこの文字を半角に変更したと明記している。[PlemolJP 3.1.0の変更履歴](https://github.com/yuru7/PlemolJP/releases/tag/v3.1.0)
- すべての実測フォントで、HarfBuzzを使った分解表記 `か`＋U+3099 は合成済みの `が` と同じ送りだった。`あ`＋U+3099は、比較した1:2版ではUtatane修正候補・M PLUS 1 Code・Noto・HackGen・MS Gothicで2セル、M+ 1m・Cica・UDEV Gothic・PlemolJPで4セルだった。通常の合成例と、合成済みグリフに置換できない例を両方見ると違いを確認できる。

## 差分の再現方法

FontToolsを使い、比較したい完成TTFを2つ指定する。7,761などの分母はコードポイント数で、収録が片方に限られる文字は別に数える。異なるUPMのフォントも比べられるよう、em比率で照合する。

```python
from fractions import Fraction
from sys import argv

from fontTools.ttLib import TTFont


def advances(path):
    with TTFont(path) as font:
        upm = font["head"].unitsPerEm
        metrics = font["hmtx"].metrics
        return {
            cp: Fraction(metrics[glyph][0], upm)
            for cp, glyph in font.getBestCmap().items()
        }


left, right = map(advances, argv[1:3])
common = left.keys() & right.keys()
different = sorted(cp for cp in common if left[cp] != right[cp])
print(f"共通 {len(common)}, 差分 {len(different)}, "
      f"左のみ {len(left.keys() - right.keys())}, 右のみ {len(right.keys() - left.keys())}")
for cp in different:
    print(f"U+{cp:04X}\t{left[cp]} em\t{right[cp]} em")
```
