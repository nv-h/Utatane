"""usWinAscent / usWinDescent からはみ出すグリフを一覧する HTML を作る。

Windows の GDI は、win の範囲（Utatane は 800 / 200）の外側を欠けさせる。
はみ出すグリフを1字ずつ、現状（dist/ のフォント）・A（win を広げる）・B（グリフを縮める）で並べ、
欠ける量の大きい順に確認できるようにする。

既定の生成物（fit_within_win_metrics() で縮めたもの）に対して実行すると、入力できる文字で
はみ出すものが残っていないことを確認できる。縮める前の状態を見るには、utatane.py を
--no-fit-win-metrics 付きで実行して dist/ を作り直してから実行する。

リポジトリ直下で実行する:
    uv run python analysis/win_clipping_report.py
出力は tmp/win-clip/win_clipping.html。Windows では GDI で実測した図
（analysis/visualize_win_clipping.py の出力）も作って埋め込む。
"""

import base64
import html
import io
import json
import sys
import unicodedata
from collections import Counter, defaultdict

from fontTools import subset
from fontTools import unicodedata as ft_unicodedata
from fontTools.ttLib import TTFont
from visualize_win_clipping import (
    DIST,
    OUT,
    WEIGHTS,
    encoded_extent,
    glyph_bounds,
    shrink_outside,
)

CSS_WEIGHT = {"Regular": 400, "Bold": 700}
# 欠ける量の区分（1000 UPM の単位）。16px 表示でおよそ 1.6px 以上 / 0.5px 以上
LARGE, MEDIUM = 100, 30
SEVERITY = {"large": "大", "medium": "中", "small": "小"}
# GDI に近づけるため、記号の位置合わせ（GPOS）や合成（GSUB）はかけずに描く
VIEW_TOP, VIEW_BOTTOM = 1020, 360
SVG_HEIGHT = 120  # 表示の高さ（px）
# 文脈置換のルール集合と、その中のルールの属性名
RULE_ATTRS = (
    ("SubRuleSet", "SubRule"),
    ("SubClassSet", "SubClassRule"),
    ("ChainSubRuleSet", "ChainSubRule"),
    ("ChainSubClassSet", "ChainSubClassRule"),
)


def severity(units):
    if units >= LARGE:
        return "large"
    if units >= MEDIUM:
        return "medium"
    return "small"


def base_letter(character):
    """分解したときの先頭の文字（Ằ → A）。分解できなければ None"""
    decomposition = unicodedata.decomposition(character)
    if not decomposition or decomposition.startswith("<"):
        return None
    first = chr(int(decomposition.split()[0], 16))
    return base_letter(first) or first


def sample_text(cp, cmap):
    """結合記号は土台の文字に乗せ、アクセント付きの文字は元の文字と並べて見せる"""
    character = chr(cp)
    if unicodedata.category(character) in {"Mn", "Me"}:
        base = "ב" if 0x0591 <= cp <= 0x05C7 and ord("ב") in cmap else "x"
        return base + character
    base = base_letter(character)
    if base and ord(base) in cmap and unicodedata.category(base).startswith("L"):
        return base + character
    return character


def gsub_outputs(font):
    """GSUB で作られるグリフ → それを出す機能タグ"""
    if "GSUB" not in font:
        return {}
    table = font["GSUB"].table
    lookups = table.LookupList.Lookup

    def subtables(index):
        for st in lookups[index].SubTable:
            yield getattr(st, "ExtSubTable", st)

    def nested(index, seen):
        if index in seen:
            return
        seen.add(index)
        for st in subtables(index):
            for record in getattr(st, "SubstLookupRecord", None) or []:
                nested(record.LookupListIndex, seen)
            for set_attr, rule_attr in RULE_ATTRS:
                for rule_set in getattr(st, set_attr, None) or []:
                    if rule_set is None:
                        continue
                    for rule in getattr(rule_set, rule_attr, None) or []:
                        for record in rule.SubstLookupRecord:
                            nested(record.LookupListIndex, seen)

    produced = defaultdict(set)
    for record in table.FeatureList.FeatureRecord:
        indexes = set()
        for index in record.Feature.LookupListIndex:
            nested(index, indexes)
        for index in indexes:
            for st in subtables(index):
                outputs = []
                if hasattr(st, "mapping"):
                    outputs = st.mapping.values()
                elif hasattr(st, "alternates"):
                    outputs = [g for gs in st.alternates.values() for g in gs]
                elif hasattr(st, "ligatures"):
                    outputs = [
                        lig.LigGlyph for ligs in st.ligatures.values() for lig in ligs
                    ]
                for glyph in outputs:
                    if isinstance(glyph, (list, tuple)):
                        for g in glyph:
                            produced[g].add(record.FeatureTag)
                    else:
                        produced[glyph].add(record.FeatureTag)
    return produced


def webfont(font, text, family):
    options = subset.Options()
    options.layout_features = []
    options.hinting = False
    options.name_IDs = []
    subsetter = subset.Subsetter(options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    font.flavor = "woff"
    buffer = io.BytesIO()
    font.save(buffer)
    data = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"@font-face{{font-family:'{family}';src:url(data:font/woff;base64,{data})}}"


def collect():
    sources = {w: TTFont(DIST / f"Utatane-{w}.ttf") for w in WEIGHTS}
    a_top, a_bottom = encoded_extent(sources.values())
    rows = defaultdict(dict)
    unencoded = defaultdict(dict)
    fonts = {}
    samples = set()
    for weight, font in sources.items():
        os2 = font["OS/2"]
        top, bottom = os2.usWinAscent, os2.usWinDescent
        bounds = glyph_bounds(font)
        cmap = font.getBestCmap()
        shrunk = TTFont(DIST / f"Utatane-{weight}.ttf")
        scales = shrink_outside(shrunk, top, bottom)
        reverse = defaultdict(list)
        for cp, glyph in cmap.items():
            reverse[glyph].append(cp)
        produced = gsub_outputs(font)
        for glyph, (_, y_min, _, y_max) in bounds.items():
            above, below = max(0, y_max - top), max(0, -bottom - y_min)
            if not (above or below):
                continue
            entry = {
                "glyph": glyph,
                "yMax": y_max,
                "yMin": y_min,
                "above": above,
                "below": below,
                "worst": max(above, below),
                "scale": scales.get(glyph, 1),
            }
            if glyph not in reverse:
                entry["features"] = sorted(produced.get(glyph, ()))
                unencoded[glyph][weight] = entry
                continue
            for cp in reverse[glyph]:
                text = sample_text(cp, cmap)
                samples.add(text)
                entry_cp = dict(entry, sample=text)
                entry_cp["advance"] = sum(
                    font["hmtx"][cmap[ord(c)]][0] for c in text if ord(c) in cmap
                )
                rows[cp][weight] = entry_cp
        fonts[weight] = {"current": font, "B": shrunk, "win": (top, bottom)}
    return rows, unencoded, fonts, samples, (a_top, a_bottom)


def svg(sample, family, weight, top, bottom, advance, clip_id):
    width = max(advance, 500) + 300
    view = f"-150 {-VIEW_TOP} {width} {VIEW_TOP + VIEW_BOTTOM}"
    text = html.escape(sample)
    style = f"font-family:'{family}';font-weight:{weight}"
    return (
        f'<svg viewBox="{view}" height="{SVG_HEIGHT}" width="{round(width * SVG_HEIGHT / (VIEW_TOP + VIEW_BOTTOM))}"'
        f' role="img" aria-label="{text}">'
        f'<rect class="box" x="-150" y="{-top}" width="{width}" height="{top + bottom}"/>'
        f'<line class="baseline" x1="-150" x2="{width - 150}" y1="0" y2="0"/>'
        f'<text class="lost" x="0" y="0" style="{style}">{text}</text>'
        f'<text class="ink" x="0" y="0" style="{style}" clip-path="url(#{clip_id})">{text}</text>'
        "</svg>"
    )


def render_html(rows, unencoded, fonts, samples, a_win, gdi_png):
    text = "".join(sorted(samples)) + "xב"
    rules = []
    for weight in WEIGHTS:
        for key in ("current", "B"):
            rules.append(webfont(fonts[weight][key], text, f"uta-{key}-{weight}"))
    top, bottom = fonts[WEIGHTS[0]]["win"]
    a_top, a_bottom = a_win
    clips = {
        "clip-current": (top, bottom),
        "clip-a": (a_top, a_bottom),
    }
    defs = "".join(
        f'<clipPath id="{cid}" clipPathUnits="userSpaceOnUse">'
        f'<rect x="-5000" y="{-t}" width="20000" height="{t + b}"/></clipPath>'
        for cid, (t, b) in clips.items()
    )

    body = []
    counts = {w: Counter() for w in WEIGHTS}
    blocks = {w: defaultdict(Counter) for w in WEIGHTS}
    for cp in sorted(rows):
        per_weight = rows[cp]
        character = chr(cp)
        name = unicodedata.name(character, "")
        block = ft_unicodedata.block(character)
        attrs = [f'data-cp="{cp}"', f'data-block="{html.escape(block)}"']
        cells = {"metric": [], "current": [], "a": [], "b": []}
        for weight in WEIGHTS:
            css = CSS_WEIGHT[weight]
            data = per_weight.get(weight)
            hidden = "" if weight == WEIGHTS[0] else " hidden"
            if data is None:
                attrs.append(f'data-worst-{css}="-1"')
                for column in cells.values():
                    column.append(f'<div data-weight="{css}"{hidden}></div>')
                continue
            level = severity(data["worst"])
            counts[weight][level] += 1
            blocks[weight][block][level] += 1
            attrs += [
                f'data-worst-{css}="{data["worst"]}"',
                f'data-level-{css}="{level}"',
            ]
            parts = []
            if data["above"]:
                parts.append(f"上 +{data['above']}")
            if data["below"]:
                parts.append(f"下 +{data['below']}")
            px = data["worst"] * 16 / 1000
            cells["metric"].append(
                f'<div data-weight="{css}"{hidden}><span class="level {level}">'
                f"{SEVERITY[level]}</span> {' · '.join(parts)}"
                f"<small>16pxで約{px:.1f}px · 範囲 {data['yMin']}〜{data['yMax']}</small></div>"
            )
            family = f"uta-current-{weight}"
            cells["current"].append(
                f'<div data-weight="{css}"{hidden}>'
                + svg(
                    data["sample"],
                    family,
                    css,
                    top,
                    bottom,
                    data["advance"],
                    "clip-current",
                )
                + "</div>"
            )
            cells["a"].append(
                f'<div data-weight="{css}"{hidden}>'
                + svg(
                    data["sample"],
                    family,
                    css,
                    a_top,
                    a_bottom,
                    data["advance"],
                    "clip-a",
                )
                + "</div>"
            )
            cells["b"].append(
                f'<div data-weight="{css}"{hidden}>'
                + svg(
                    data["sample"],
                    f"uta-B-{weight}",
                    css,
                    top,
                    bottom,
                    data["advance"],
                    "clip-current",
                )
                + f"<small>{data['scale']:.0%} に縮小</small></div>"
            )
        label = (
            f'<th scope="row"><span class="char">{html.escape(character)}</span>'
            f"U+{cp:04X}<small>{html.escape(name)}</small><small>{html.escape(block)}</small></th>"
        )
        body.append(
            f"<tr {' '.join(attrs)}>{label}"
            + "".join(
                f"<td>{''.join(cells[key])}</td>"
                for key in ("metric", "current", "a", "b")
            )
            + "</tr>"
        )

    summary = []
    for weight in WEIGHTS:
        css = CSS_WEIGHT[weight]
        hidden = "" if weight == WEIGHTS[0] else " hidden"
        total = sum(counts[weight].values())
        block_rows = "".join(
            f"<tr><th scope='row'>{html.escape(block)}</th>"
            + "".join(f"<td>{levels[k] or ''}</td>" for k in SEVERITY)
            + f"<td>{sum(levels.values())}</td></tr>"
            for block, levels in sorted(
                blocks[weight].items(),
                key=lambda item: (
                    -item[1]["large"],
                    -item[1]["medium"],
                    -sum(item[1].values()),
                ),
            )
        )
        summary.append(
            f'<div data-weight="{css}"{hidden}>'
            f"<p class='totals'>入力できる文字で <strong>{total}字</strong> がはみ出す："
            + " · ".join(
                f"<span class='level {k}'>{v}</span> {counts[weight][k]}字"
                for k, v in SEVERITY.items()
            )
            + "</p><div class='table-wrap'><table class='blocks'><thead><tr><th>ブロック</th>"
            + "".join(f"<th>{v}</th>" for v in SEVERITY.values())
            + f"<th>計</th></tr></thead><tbody>{block_rows}</tbody></table></div></div>"
        )

    hidden_rows = []
    for glyph in sorted(
        unencoded, key=lambda g: -max(d["worst"] for d in unencoded[g].values())
    ):
        cells = []
        for weight in WEIGHTS:
            data = unencoded[glyph].get(weight)
            cells.append(
                f"<td>{data['worst']}（{data['yMin']}〜{data['yMax']}）</td>"
                if data
                else "<td>—</td>"
            )
        features = sorted({f for d in unencoded[glyph].values() for f in d["features"]})
        hidden_rows.append(
            f"<tr><th scope='row'>{html.escape(glyph)}</th>{''.join(cells)}"
            f"<td>{html.escape(', '.join(features) or '（機能から参照なし）')}</td></tr>"
        )

    gdi = (
        f'<figure><img src="data:image/png;base64,{gdi_png}" alt="GDI で実際に描画した比較図">'
        "<figcaption>Windows GDI（TextOut）で実際に描画した結果。赤が欠けた部分。</figcaption></figure>"
        if gdi_png
        else "<p class='muted'>GDI の実測図は Windows で analysis/visualize_win_clipping.py を実行すると入ります。</p>"
    )
    line_ratio = (a_top + a_bottom) / (top + bottom)
    replacements = {
        "FONT_RULES": "\n".join(rules),
        "CLIP_DEFS": defs,
        "WIN_TOP": str(top),
        "WIN_BOTTOM": str(bottom),
        "A_TOP": str(a_top),
        "A_BOTTOM": str(a_bottom),
        "A_RATIO": f"{line_ratio:.2f}",
        "SUMMARY": "".join(summary),
        "GDI_FIGURE": gdi,
        "ROWS": "".join(body),
        "HIDDEN_ROWS": "".join(hidden_rows),
        "HIDDEN_COUNT": str(len(unencoded)),
        "LARGE": str(LARGE),
        "MEDIUM": str(MEDIUM),
        "WEIGHTS_JSON": json.dumps([CSS_WEIGHT[w] for w in WEIGHTS]),
    }
    fonts_css = replacements.pop("FONT_RULES")
    page = TEMPLATE
    for key, value in replacements.items():
        page = page.replace("{{" + key + "}}", value)
    # base64 の中身が置換キーと衝突しないよう、フォントは最後に入れる
    return page.replace("{{FONT_RULES}}", fonts_css)


def main():
    gdi_png = ""
    if sys.platform == "win32":
        import visualize_win_clipping

        visualize_win_clipping.main()
        gdi_png = base64.b64encode((OUT / "win_clipping.png").read_bytes()).decode(
            "ascii"
        )
    rows, unencoded, fonts, samples, a_win = collect()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "win_clipping.html"
    path.write_text(
        render_html(rows, unencoded, fonts, samples, a_win, gdi_png), encoding="utf-8"
    )
    print(f"HTML: {path}")


TEMPLATE = """<!doctype html><html lang="ja"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Utatane Windows で欠けるグリフ</title>
<style>
{{FONT_RULES}}
:root{color:#192b30;background:#f6f8f7;font:15px/1.5 system-ui,sans-serif}
body{width:min(1450px,calc(100% - 32px));margin:20px auto}h1{margin:0;font-size:29px}h2{font-size:18px;margin:22px 0 6px}
p{margin:5px 0 12px}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;background:white}
th,td{padding:6px 10px;border-bottom:1px solid #d8e1df;text-align:left;vertical-align:middle}
thead{background:#e6efed}small,.muted{color:#52666b;font-size:13px}small{display:block;font-weight:400}
button,select{font:inherit;padding:4px 12px;border-radius:4px;border:1px solid #afc5bf;background:white;color:inherit}
button[aria-pressed=true]{background:#12685e;color:white;border-color:#12685e}
.controls{position:sticky;top:0;z-index:1;display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:6px 0 8px;background:#f6f8f7}
.controls .sep{width:12px}input[type=search]{padding:5px 8px;border:1px solid #afc5bf;border-radius:4px;font:inherit;min-width:240px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px;margin:8px 0 4px}
.card{background:white;border:1px solid #d8e1df;border-radius:6px;padding:10px 14px}.card h3{margin:0 0 4px;font-size:15px}
.level{display:inline-block;min-width:1.6em;padding:0 6px;border-radius:4px;text-align:center;font-weight:600;font-size:13px}
.level.large{background:#d03b3b;color:white}.level.medium{background:#f3c6b5;color:#5a1f0e}.level.small{background:#e6efed;color:#33494e}
.char{display:block;font-size:26px;line-height:1.2;font-family:'uta-current-Regular'}
table.list th[scope=row]{width:17%}table.list td:nth-child(2){width:15%}
svg{display:block;overflow:visible}svg .box{fill:#eef4f2;stroke:#2a78d6;stroke-width:6}
svg .baseline{stroke:#afc5bf;stroke-width:4;stroke-dasharray:24 18}
svg text{font-size:1000px}svg .lost{fill:#d03b3b}svg .ink{fill:#16322e}
figure{margin:8px 0;background:white;border:1px solid #d8e1df;border-radius:6px;padding:8px}figure img{max-width:100%}
figcaption{color:#52666b;font-size:13px}table.blocks{max-width:620px}table.blocks td{text-align:right;font-variant-numeric:tabular-nums}
details{margin:10px 0}summary{cursor:pointer;font-weight:600}.count{color:#52666b;margin-left:8px}
[hidden]{display:none!important}
</style>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{{CLIP_DEFS}}</defs></svg>
<h1>Utatane Windows（GDI）で欠けるグリフ</h1>
<p>Windows の GDI は usWinAscent / usWinDescent（現状 {{WIN_TOP}} / {{WIN_BOTTOM}}）の外側を描かない。各セルは
<span style="color:#2a78d6">青枠</span>が GDI の行の箱（この範囲だけ描かれる）、<strong style="color:#d03b3b">赤</strong>が欠ける部分。
数値は 1000 UPM の単位。DirectWrite で描くアプリ（Windows Terminal、Chromium 系など）は USE_TYPO_METRICS により欠けない。</p>
<div class="cards">
<div class="card"><h3>A: win を広げる（{{A_TOP}} / {{A_BOTTOM}}）</h3>字形はそのまま。入力できる文字は欠けなくなる。
GDI で描くアプリの行の高さが <strong>{{A_RATIO}} 倍</strong>になる。</div>
<div class="card"><h3>B: はみ出すグリフを縮める</h3>行の高さはそのまま。はみ出す字をベースライン基準で等倍に縮める
（この一覧の B 列。字ごとの調整はしていない単純な縮小）。</div>
<div class="card"><h3>区分</h3><span class="level large">大</span> {{LARGE}} 以上（16pxで約1.6px以上）
<span class="level medium">中</span> {{MEDIUM}}〜{{LARGE}} <span class="level small">小</span> {{MEDIUM}} 未満（16pxで0.5px未満）</div>
</div>
<div class="controls">
<button type="button" data-select="400" aria-pressed="true">Regular</button>
<button type="button" data-select="700" aria-pressed="false">Bold</button>
<span class="sep"></span>
<button type="button" data-level="all" aria-pressed="true">すべて</button>
<button type="button" data-level="large" aria-pressed="false">大</button>
<button type="button" data-level="medium" aria-pressed="false">中</button>
<button type="button" data-level="small" aria-pressed="false">小</button>
<span class="sep"></span>
<select aria-label="並び順"><option value="worst">欠ける量の大きい順</option><option value="cp">コード順</option><option value="block">ブロック順</option></select>
<input type="search" placeholder="文字・U+コード・名前・ブロックで絞り込み" aria-label="絞り込み">
<span class="count"></span>
</div>
<h2>概要</h2>
{{SUMMARY}}
{{GDI_FIGURE}}
<h2>一覧</h2>
<div class="table-wrap"><table class="list"><thead><tr><th>文字</th><th>はみ出し</th><th>現状</th><th>A: win を広げる</th><th>B: 縮める</th></tr></thead>
<tbody>{{ROWS}}</tbody></table></div>
<details><summary>cmap に無いグリフ（{{HIDDEN_COUNT}} 個）</summary>
<p class="muted">文字として直接は入力できず、GSUB の機能でだけ使われるグリフ。A の値（{{A_TOP}} / {{A_BOTTOM}}）では覆っていない。</p>
<div class="table-wrap"><table><thead><tr><th>グリフ名</th><th>Regular はみ出し（範囲）</th><th>Bold はみ出し（範囲）</th><th>出す機能</th></tr></thead>
<tbody>{{HIDDEN_ROWS}}</tbody></table></div></details>
<script>
const weights = {{WEIGHTS_JSON}};
const tbody = document.querySelector('table.list tbody');
const rows = [...tbody.rows];
const search = document.querySelector('input[type=search]');
const order = document.querySelector('select');
const count = document.querySelector('.count');
let weight = 400, level = 'all';
function apply() {
  for (const b of document.querySelectorAll('[data-select]')) b.setAttribute('aria-pressed', +b.dataset.select === weight);
  for (const b of document.querySelectorAll('[data-level]')) b.setAttribute('aria-pressed', b.dataset.level === level);
  for (const box of document.querySelectorAll('[data-weight]')) box.hidden = +box.dataset.weight !== weight;
  const query = search.value.trim().toLowerCase();
  const key = order.value;
  const sorted = [...rows].sort((a, b) => key === 'cp' ? a.dataset.cp - b.dataset.cp
    : key === 'block' ? a.dataset.block.localeCompare(b.dataset.block) || a.dataset.cp - b.dataset.cp
    : b.dataset['worst-' + weight] - a.dataset['worst-' + weight] || a.dataset.cp - b.dataset.cp);
  let shown = 0;
  for (const row of sorted) {
    const worst = +row.dataset['worst-' + weight];
    const visible = worst >= 0 && (level === 'all' || row.dataset['level-' + weight] === level)
      && (!query || row.textContent.toLowerCase().includes(query));
    row.hidden = !visible;
    shown += visible;
    tbody.append(row);
  }
  count.textContent = shown + '字';
}
for (const b of document.querySelectorAll('[data-select]')) b.addEventListener('click', () => { weight = +b.dataset.select; apply(); });
for (const b of document.querySelectorAll('[data-level]')) b.addEventListener('click', () => { level = b.dataset.level; apply(); });
search.addEventListener('input', apply);
order.addEventListener('change', apply);
apply();
</script></html>"""


if __name__ == "__main__":
    main()
