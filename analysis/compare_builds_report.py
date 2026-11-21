"""生成したフォントの版どうしを見比べる HTML を作る。

各版（ラベル=フォントのあるディレクトリ）について、次を並べる。
  - 概要: ファイルサイズ、ヒンティング命令、描画されない輪郭、win からのはみ出し
  - Windows GDI での描画（グレースケール / ClearType、サイズ別、前の列との差分つき）
  - ブラウザーでの描画
  - 1列目と2列目で字形が変わった文字

例（リポジトリ直下で実行する）:
    uv run python analysis/compare_builds_report.py \
        --variant 変更前=tmp/compare/before \
        --variant 今回=tmp/compare/current \
        --variant ヒンティングあり=tmp/compare/hinted \
        --output tmp/compare/compare.html
GDI の描画は Windows でのみ作る。
"""

import argparse
import base64
import ctypes
import ctypes.wintypes as wt
import html
import io
import os
import sys
import unicodedata
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from fontTools import subset
from fontTools.ttLib import TTFont
from visualize_win_clipping import (
    BITMAPINFOHEADER,
    FR_PRIVATE,
    TEXTMETRICW,
    WEIGHTS,
    load_gdi,
    outline_bounds,
    rename,
)

CSS_WEIGHT = {"Regular": 400, "Bold": 700}
SIZES = (10, 12, 14, 16, 20, 28)
QUALITIES = {"gray": ("グレースケール", 4), "cleartype": ("ClearType", 5)}
SAMPLES = {
    "コード": (
        "def fit(glyph, scale=0.81):",
        "    return {'a': [1, 2], \"b\": x != y}",
        "0O 1lI| ;: ,. `'\" {}[]()<> #$%&*",
    ),
    "日本語": (
        "あいうえお　アイウエオ　ｱｲｳｴｵ",
        "日本語の文章と漢字の表示「氵江湖」",
        "①②③ ←→↑↓ ※〒〜 ＡＢＣ１２３",
    ),
    "アクセント付きの欧文": (
        "ÀÉÎÕÜ àéîõü ĀĒĪŌŪ Ωαβγ Жжщ",
        "Tiếng Việt: Ầ Ấ Ẩ Ẫ Ề Ế Ể Ễ Ồ Ố Ổ Ỗ",
        "Ḗ Ḯ Ṍ Ṹ Ằ Ắ ⚤ ⚥ Ѽ Ѿ",
    ),
    "罫線・記号": (
        "┌──┬──┐ ▀▄█░▒▓",
        "│ab│あい│ ■□●○",
        "└──┴──┘ ±×÷≠≦≧",
    ),
}


# ---------------------------------------------------------------- 集計


def degenerate_contours(font):
    glyf = font["glyf"]
    count = 0
    for name in font.getGlyphOrder():
        glyph = glyf[name]
        if glyph.isComposite() or glyph.numberOfContours <= 0:
            continue
        coords, ends, _ = glyph.getCoordinates(glyf)
        start = 0
        for end in ends:
            points = coords[start : end + 1]
            start = end + 1
            xs, ys = [p[0] for p in points], [p[1] for p in points]
            if len(points) <= 2 or max(max(xs) - min(xs), max(ys) - min(ys)) <= 2:
                count += 1
    return count


def instructed_glyphs(font):
    glyf = font["glyf"]
    return sum(
        1
        for name in font.getGlyphOrder()
        if glyf[name].numberOfContours
        and getattr(glyf[name], "program", None) is not None
        and len(glyf[name].program.getBytecode()) > 0
    )


def encoded_bounds(font):
    glyph_set = font.getGlyphSet()
    return {
        cp: box
        for cp, name in font.getBestCmap().items()
        if (box := outline_bounds(glyph_set, name))
    }


def summarize(path):
    font = TTFont(path)
    os2 = font["OS/2"]
    bounds = encoded_bounds(font)
    outside = sum(
        1
        for _, y_min, _, y_max in bounds.values()
        if y_max > os2.usWinAscent or y_min < -os2.usWinDescent
    )
    return {
        "size": path.stat().st_size,
        "instructed": instructed_glyphs(font),
        "degenerate": degenerate_contours(font),
        "outside": outside,
        "bounds": bounds,
    }


def changed_glyphs(before, after, threshold=3):
    """描画される輪郭の範囲が threshold を超えて変わった文字（縮小率の小さい順）"""
    rows = []
    for cp, box in before.items():
        other = after.get(cp)
        if other is None:
            continue
        if max(abs(a - b) for a, b in zip(box, other)) > threshold:
            height, new_height = box[3] - box[1], other[3] - other[1]
            rows.append((new_height / height if height else 1, cp, box, other))
    return sorted(rows)


# ---------------------------------------------------------------- GDI 描画


def text_width(gdi, hdc, line):
    """GDI が実際に送る幅（px）"""
    size = wt.SIZE()
    gdi.GetTextExtentPoint32W(hdc, line, len(line), ctypes.byref(size))
    return size.cx


def render_gdi(family, weight, px, lines, quality):
    gdi = load_gdi()
    gdi.GetTextExtentPoint32W.argtypes = [
        wt.HDC,
        wt.LPCWSTR,
        ctypes.c_int,
        ctypes.POINTER(wt.SIZE),
    ]
    hdc = gdi.CreateCompatibleDC(None)
    font = gdi.CreateFontW(
        -px, 0, 0, 0, CSS_WEIGHT[weight], 0, 0, 0, 1, 7, 0, quality, 0, family
    )
    gdi.SelectObject(hdc, font)
    width = max(text_width(gdi, hdc, line) for line in lines) + 16
    metrics = TEXTMETRICW()
    gdi.GetTextMetricsW(hdc, ctypes.byref(metrics))
    height = metrics.tmHeight * len(lines) + 8
    header = BITMAPINFOHEADER(
        ctypes.sizeof(BITMAPINFOHEADER), width, -height, 1, 32, 0, 0, 0, 0, 0, 0
    )
    bits = ctypes.c_void_p()
    bitmap = gdi.CreateDIBSection(
        hdc, ctypes.byref(header), 0, ctypes.byref(bits), None, 0
    )
    gdi.SelectObject(hdc, bitmap)
    gdi.SelectObject(hdc, font)
    ctypes.memset(bits, 0xFF, width * height * 4)
    gdi.SetBkMode(hdc, 1)
    for i, line in enumerate(lines):
        gdi.TextOutW(hdc, 6, 4 + i * metrics.tmHeight, line, len(line))
    pixels = np.ctypeslib.as_array(
        ctypes.cast(bits, ctypes.POINTER(ctypes.c_ubyte)), shape=(height, width, 4)
    )
    rgb = pixels[:, :, 2::-1].copy()  # BGRA → RGB
    gdi.DeleteObject(font)
    gdi.DeleteObject(bitmap)
    gdi.DeleteDC(hdc)
    return rgb


def png(rgb):
    buffer = io.BytesIO()
    plt.imsave(buffer, rgb, format="png")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def diff_image(previous, current):
    """違うピクセルを赤、同じところを薄い灰色で示す"""
    changed = (np.abs(previous.astype(int) - current.astype(int)) > 16).any(axis=2)
    gray = current.mean(axis=2, keepdims=True)
    faint = (255 - (255 - gray) * 0.25).repeat(3, axis=2)
    out = faint.astype(np.uint8)
    out[changed] = (208, 59, 59)
    return out, int(changed.sum())


def gdi_section(variants):
    paths = []
    for index, (_, directory) in enumerate(variants):
        for weight in WEIGHTS:
            font = TTFont(directory / f"Utatane-{weight}.ttf")
            family = f"UtaCmp {index} {weight}"
            rename(font, family)
            path = OUT_FONTS / f"{index}-{weight}.ttf"
            font.save(path)
            load_gdi().AddFontResourceExW(os.fspath(path), FR_PRIVATE, None)
            paths.append(path)

    rows = []
    for sample_name, lines in SAMPLES.items():
        rows.append(
            f'<tr class="group"><th colspan="{len(variants) + 1}">{html.escape(sample_name)}</th></tr>'
        )
        for px in SIZES:
            cells_html = {i: [] for i in range(len(variants))}
            for weight in WEIGHTS:
                for quality_key, (_, quality) in QUALITIES.items():
                    images = [
                        render_gdi(f"UtaCmp {i} {weight}", weight, px, lines, quality)
                        for i in range(len(variants))
                    ]
                    attrs = f'data-weight="{CSS_WEIGHT[weight]}" data-quality="{quality_key}"'
                    for i, image in enumerate(images):
                        note = ""
                        diff = ""
                        if i:
                            picture, count = diff_image(images[i - 1], image)
                            note = (
                                f'<small class="{"changed" if count else "same"}">'
                                f"{html.escape(variants[i - 1][0])}との差 {count}px</small>"
                            )
                            diff = f'<img class="diff" src="data:image/png;base64,{png(picture)}" alt="差分">'
                        cells_html[i].append(
                            f"<div {attrs}><img class='shot' src='data:image/png;base64,{png(image)}' alt=''>"
                            f"{diff}{note}</div>"
                        )
            rows.append(
                f'<tr><th scope="row">{px}px</th>'
                + "".join(
                    f"<td>{''.join(cells_html[i])}</td>" for i in range(len(variants))
                )
                + "</tr>"
            )
    for path in paths:
        load_gdi().RemoveFontResourceExW(os.fspath(path), FR_PRIVATE, None)
    return "".join(rows)


# ---------------------------------------------------------------- HTML


def webfont(path, text, family):
    font = TTFont(path)
    options = subset.Options()
    options.hinting = True
    options.name_IDs = []
    subsetter = subset.Subsetter(options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    font.flavor = "woff"
    buffer = io.BytesIO()
    font.save(buffer)
    data = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"@font-face{{font-family:'{family}';src:url(data:font/woff;base64,{data})}}"


def glyph_svg(character, family, weight, box, win):
    top, bottom = win
    advance = 1000 if unicodedata.east_asian_width(character) in "FW" else 500
    width = advance + 200
    return (
        f'<svg viewBox="-100 -1000 {width} 1300" height="104" width="{round(width * 0.08)}">'
        f'<rect class="win" x="-100" y="{-top}" width="{width}" height="{top + bottom}"/>'
        f'<line class="baseline" x1="-100" x2="{width - 100}" y1="0" y2="0"/>'
        f'<text x="0" y="0" style="font-family:\'{family}\';font-weight:{weight}">'
        f"{html.escape(character)}</text></svg>"
        f"<small>{round(box[1])}〜{round(box[3])}</small>"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--variant", action="append", required=True, help="ラベル=ディレクトリ"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    variants = [
        (label, Path(path)) for label, path in (v.split("=", 1) for v in args.variant)
    ]

    summaries = {
        (label, weight): summarize(directory / f"Utatane-{weight}.ttf")
        for label, directory in variants
        for weight in WEIGHTS
    }

    # 1列目と2列目で字形が変わった文字
    changed = {
        weight: changed_glyphs(
            summaries[(variants[0][0], weight)]["bounds"],
            summaries[(variants[1][0], weight)]["bounds"],
        )
        for weight in WEIGHTS
    }
    changed_text = "".join(chr(cp) for rows in changed.values() for _, cp, _, _ in rows)
    sample_text = "".join("".join(lines) for lines in SAMPLES.values())

    rules = [
        webfont(
            directory / f"Utatane-{weight}.ttf",
            sample_text + changed_text,
            f"v{i}-{weight}",
        )
        for i, (_, directory) in enumerate(variants)
        for weight in WEIGHTS
    ]

    # 概要
    def mb(size):
        return f"{size / 1_000_000:.2f}MB"

    summary_rows = []
    for label, fields in (
        ("ファイルサイズ", lambda s: mb(s["size"])),
        ("ヒンティング命令のあるグリフ", lambda s: f"{s['instructed']:,}"),
        ("描画されない輪郭（迷子の点など）", lambda s: f"{s['degenerate']:,}"),
        ("win の範囲からはみ出す文字", lambda s: f"{s['outside']:,}"),
    ):
        summary_rows.append(
            f"<tr><th scope='row'>{label}</th>"
            + "".join(
                "<td>"
                + " / ".join(fields(summaries[(name, weight)]) for weight in WEIGHTS)
                + "</td>"
                for name, _ in variants
            )
            + "</tr>"
        )
    head = "".join(
        f"<th>{html.escape(name)}<small>Regular / Bold</small></th>"
        for name, _ in variants
    )

    # GDI
    gdi_rows = gdi_section(variants) if sys.platform == "win32" else ""

    # ブラウザー
    browser_rows = []
    for sample_name, lines in SAMPLES.items():
        browser_rows.append(
            f'<tr class="group"><th colspan="{len(variants) + 1}">{html.escape(sample_name)}</th></tr>'
        )
        for px in (12, 16, 28):
            cells_html = []
            for i in range(len(variants)):
                boxes = "".join(
                    f'<div data-weight="{CSS_WEIGHT[w]}" class="live" '
                    f"style=\"font-family:'v{i}-{w}';font-weight:{CSS_WEIGHT[w]};font-size:{px}px\">"
                    + "<br>".join(html.escape(line) for line in lines)
                    + "</div>"
                    for w in WEIGHTS
                )
                cells_html.append(f"<td>{boxes}</td>")
            browser_rows.append(
                f'<tr><th scope="row">{px}px</th>{"".join(cells_html)}</tr>'
            )

    # 字形が変わった文字
    changed_rows = []
    for weight in WEIGHTS:
        css = CSS_WEIGHT[weight]
        win_before = (800, 200)
        for ratio, cp, before, after in changed[weight]:
            character = chr(cp)
            name = unicodedata.name(character, "")
            changed_rows.append(
                f'<tr data-weight="{css}"><th scope="row"><span class="char">{html.escape(character)}</span>'
                f"U+{cp:04X}<small>{html.escape(name)}</small></th>"
                f"<td>{ratio:.0%}</td>"
                f"<td>{glyph_svg(character, f'v0-{weight}', css, before, win_before)}</td>"
                f"<td>{glyph_svg(character, f'v1-{weight}', css, after, win_before)}</td></tr>"
            )

    page = TEMPLATE
    replacements = {
        "{{HEAD}}": head,
        "{{SUMMARY}}": "".join(summary_rows),
        "{{GDI_HEAD}}": "".join(
            f"<th>{html.escape(name)}</th>" for name, _ in variants
        ),
        "{{GDI_ROWS}}": gdi_rows
        or f'<tr><td colspan="{len(variants) + 1}">GDI の描画は Windows で実行すると入ります。</td></tr>',
        "{{BROWSER_ROWS}}": "".join(browser_rows),
        "{{CHANGED_ROWS}}": "".join(changed_rows),
        "{{CHANGED_FROM}}": html.escape(variants[0][0]),
        "{{CHANGED_TO}}": html.escape(variants[1][0]),
        "{{CHANGED_COUNT}}": " / ".join(
            f"{weight} {len(changed[weight])}字" for weight in WEIGHTS
        ),
    }
    for key, value in replacements.items():
        page = page.replace(key, value)
    page = page.replace("{{FONT_RULES}}", "\n".join(rules))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page, encoding="utf-8")
    print(f"HTML: {args.output}")


OUT_FONTS = Path(__file__).resolve().parents[1] / "tmp" / "compare" / "gdi-fonts"
OUT_FONTS.mkdir(parents=True, exist_ok=True)

TEMPLATE = """<!doctype html><html lang="ja"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Utatane 版の比較</title>
<style>
{{FONT_RULES}}
:root{color:#192b30;background:#f6f8f7;font:15px/1.5 system-ui,sans-serif}
body{width:min(1600px,calc(100% - 32px));margin:20px auto}h1{margin:0;font-size:29px}h2{font-size:19px;margin:26px 0 6px}
p{margin:5px 0 12px}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;background:white}
th,td{padding:6px 10px;border-bottom:1px solid #d8e1df;text-align:left;vertical-align:top}
thead{background:#e6efed}small,.muted{color:#52666b;font-size:13px}small{display:block;font-weight:400}
tr.group th{background:#eef4f2;font-size:15px}
button{font:inherit;padding:4px 12px;border-radius:4px;border:1px solid #afc5bf;background:white;color:inherit}
button[aria-pressed=true]{background:#12685e;color:white;border-color:#12685e}
.controls{position:sticky;top:0;z-index:2;display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:6px 0 8px;background:#f6f8f7}
.controls .sep{width:14px}
table.summary td{font-variant-numeric:tabular-nums}
img.shot,img.diff{display:block;image-rendering:pixelated;zoom:var(--zoom,1);background:white;border:1px solid #e3ebe9}
img.diff{margin-top:4px}body:not(.show-diff) img.diff{display:none}
small.changed{color:#b3261e;font-weight:600}small.same{color:#52666b}
.live{white-space:pre;line-height:1.35;color:#16322e;background:white;overflow-x:auto;max-width:520px}
.char{display:block;font-size:24px;font-family:'v1-Regular'}
svg{display:block;overflow:visible}svg .win{fill:#eef4f2;stroke:#2a78d6;stroke-width:8}
svg .baseline{stroke:#afc5bf;stroke-width:5;stroke-dasharray:24 18}svg text{font-size:1000px;fill:#16322e}
[hidden]{display:none!important}
</style>
<h1>Utatane 版の比較</h1>
<p>フォントの版どうしを並べて比べる。GDI の画像は Windows の GDI（TextOut）で実際に描いたもの。
各列の「差」は左隣の列とのピクセル差で、「差分を表示」で違う場所を赤く示す。
ヒンティング命令は、GDI ではグレースケール・ClearType とも、どのサイズでも描画を変える。</p>
<p class="muted">注意: GDI は日本語フォントの2バイト文字（かな・漢字、Shift_JIS で2バイトになる罫線・±・× など）を
OS/2 の xAvgCharWidth の2倍の幅で送る。Utatane は xAvgCharWidth がやさしさゴシックの値（Regular 463 / Bold 510）なので、
GDI ではこれらの文字の間隔が 926 / 1020 になり、罫線が途切れて見える。どの版にも共通する以前からの問題。</p>
<div class="controls">
<button type="button" data-weight-select="400" aria-pressed="true">Regular</button>
<button type="button" data-weight-select="700" aria-pressed="false">Bold</button>
<span class="sep"></span>
<button type="button" data-quality-select="gray" aria-pressed="true">グレースケール</button>
<button type="button" data-quality-select="cleartype" aria-pressed="false">ClearType</button>
<span class="sep"></span>
<button type="button" data-zoom="1" aria-pressed="true">等倍</button>
<button type="button" data-zoom="2" aria-pressed="false">2倍</button>
<button type="button" data-zoom="3" aria-pressed="false">3倍</button>
<span class="sep"></span>
<button type="button" data-diff aria-pressed="false">差分を表示</button>
</div>
<h2>概要</h2>
<div class="table-wrap"><table class="summary"><thead><tr><th></th>{{HEAD}}</tr></thead><tbody>{{SUMMARY}}</tbody></table></div>
<h2>Windows GDI での描画</h2>
<div class="table-wrap"><table><thead><tr><th>サイズ</th>{{GDI_HEAD}}</tr></thead><tbody>{{GDI_ROWS}}</tbody></table></div>
<h2>ブラウザーでの描画</h2>
<p class="muted">このブラウザーの文字描画（Windows の Chrome / Edge なら DirectWrite）で表示している。GDI とは見え方が異なる。</p>
<div class="table-wrap"><table><thead><tr><th>サイズ</th>{{GDI_HEAD}}</tr></thead><tbody>{{BROWSER_ROWS}}</tbody></table></div>
<h2>字形が変わった文字（{{CHANGED_FROM}} → {{CHANGED_TO}}：{{CHANGED_COUNT}}）</h2>
<p class="muted">描画される輪郭の範囲が3単位を超えて変わった文字。青枠は win の範囲（800 / 200）、数字は輪郭の下端〜上端。縮小率の大きい順。</p>
<div class="table-wrap"><table><thead><tr><th>文字</th><th>高さの比</th><th>{{CHANGED_FROM}}</th><th>{{CHANGED_TO}}</th></tr></thead><tbody>{{CHANGED_ROWS}}</tbody></table></div>
<script>
let weight = '400', quality = 'gray';
function apply() {
  for (const b of document.querySelectorAll('[data-weight-select]')) b.setAttribute('aria-pressed', b.dataset.weightSelect === weight);
  for (const b of document.querySelectorAll('[data-quality-select]')) b.setAttribute('aria-pressed', b.dataset.qualitySelect === quality);
  for (const el of document.querySelectorAll('[data-weight]')) {
    el.hidden = el.dataset.weight !== weight || (el.dataset.quality !== undefined && el.dataset.quality !== quality);
  }
}
for (const b of document.querySelectorAll('[data-weight-select]')) b.addEventListener('click', () => { weight = b.dataset.weightSelect; apply(); });
for (const b of document.querySelectorAll('[data-quality-select]')) b.addEventListener('click', () => { quality = b.dataset.qualitySelect; apply(); });
for (const b of document.querySelectorAll('[data-zoom]')) b.addEventListener('click', () => {
  document.body.style.setProperty('--zoom', b.dataset.zoom);
  for (const o of document.querySelectorAll('[data-zoom]')) o.setAttribute('aria-pressed', o === b);
});
const diff = document.querySelector('[data-diff]');
diff.addEventListener('click', () => { document.body.classList.toggle('show-diff'); diff.setAttribute('aria-pressed', document.body.classList.contains('show-diff')); });
apply();
</script></html>"""


if __name__ == "__main__":
    main()
