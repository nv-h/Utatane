"""Build an offline comparison of Utatane and two reference fonts."""

import argparse
import base64
import html
import io
from pathlib import Path
import unicodedata

from fontTools import subset
from fontTools.misc.roundTools import otRound
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont


SAMPLES = (
    ('単独の上付き', 'x\u0301', (0x0301,)),
    ('単独の下付き', 'x\u0323', (0x0323,)),
    ('上付き2つ', 'x\u0301\u0308', (0x0301, 0x0308)),
    ('合成済み文字への追加', '\u1E8D\u0301', (0x0301,)),
    ('2文字にまたがる記号', 'a\u0361b', (0x0361,)),
    ('結合濁点', 'あ\u3099', (0x3099,)),
    ('結合半濁点', 'あ\u309A', (0x309A,)),
    ('合成できる濁点', 'か\u3099', (0x3099,)),
    ('合成済みの「が」', 'が', ()),
)

OVERVIEW_SAMPLES = (
    ('英数字と記号', '0O1Il'),
    ('英数と日本語', 'A漢B'),
    ('アクセント付きラテン文字', 'áḾ'),
    ('罫線', '┌─┐'),
    ('網掛け', '░▒▓'),
    ('矢印', '←→'),
    ('全角英数', 'Ａ０'),
    ('全角スペース', '\u3000'),
    ('ひらがな・カタカナ', 'あア'),
    ('半角カナと濁点', 'ｶﾞ'),
    ('和文の括弧', '「文」'),
    ('和文の句読点', '。、'),
    ('ギリシャ文字', 'αΩ'),
    ('キリル文字', 'ЯЖ'),
    ('省略記号', '…'),
    ('横棒', '―'),
    ('番号記号', '№'),
    ('ウォン記号', '₩'),
    ('空白可視化', '␣'),
    ('山括弧 U+2329/U+232A', '〈文〉'),
    ('山括弧 U+3008/U+3009', '〈文〉'),
)


def is_mark(cp):
    return unicodedata.category(chr(cp)) in {'Mn', 'Me'}


def mark_sample(cp):
    if cp in (0x3099, 0x309A):
        base = 'あ'
    elif 0x0483 <= cp <= 0x0489:
        base = 'а'
    elif 0x0590 <= cp <= 0x05FF:
        base = 'א'
    else:
        base = 'x'
    return base + chr(cp) + ('b' if 0x035C <= cp <= 0x0362 else '')


def font_advances(font, weight):
    location = {'wght': weight} if 'fvar' in font else None
    glyphs = font.getGlyphSet(location=location)
    return {cp: otRound(glyphs[glyph].width) for cp, glyph in font.getBestCmap().items()}


def width_comparison(groups):
    advances = [[None, None] for _ in groups]
    changed_width, changed_outline, changed_coverage = set(), set(), set()
    for index, weight in enumerate((400, 700)):
        for group, (_, paths) in enumerate(groups):
            with TTFont(paths[index]) as font:
                advances[group][index] = font_advances(font, weight)
        before, after = (advances[i][index] for i in (0, 1))
        shared = before.keys() & after.keys()
        width_delta = {cp for cp in shared if before[cp] != after[cp]}
        changed_width.update(width_delta)
        changed_coverage.update(before.keys() ^ after.keys())
        with TTFont(groups[0][1][index]) as old, TTFont(groups[1][1][index]) as new:
            old_glyphs, new_glyphs = old.getGlyphSet(), new.getGlyphSet()
            old_cmap, new_cmap = old.getBestCmap(), new.getBestCmap()
            for cp in shared - width_delta:
                old_pen = DecomposingRecordingPen(old_glyphs)
                new_pen = DecomposingRecordingPen(new_glyphs)
                old_glyphs[old_cmap[cp]].draw(old_pen)
                new_glyphs[new_cmap[cp]].draw(new_pen)
                if old_pen.value != new_pen.value:
                    changed_outline.add(cp)

    changed_outline -= changed_width | changed_coverage
    reference_delta = set()
    for index, after in enumerate(advances[1]):
        for reference in (advances[2][index], advances[3][index]):
            reference_delta.update(cp for cp in after.keys() & reference.keys()
                                   if after[cp] != reference[cp])

    def glyph_row(cp, reason):
        name = unicodedata.name(chr(cp), '')
        return (f'U+{cp:04X}', f'{name} · {reason}', mark_sample(cp) if is_mark(cp) else chr(cp), (cp,))

    changed = changed_width | changed_outline | changed_coverage
    changes = [glyph_row(cp, '送り幅を変更' if cp in changed_width else
                         '輪郭を変更' if cp in changed_outline else '収録範囲を変更') for cp in sorted(changed)]
    references = [glyph_row(cp, '参照先と送り幅が異なる') for cp in sorted(reference_delta)]
    return changes, references, len(changed_width), len(changed_outline), len(changed_coverage)


def build_face(path, weight, characters, family):
    with TTFont(path) as font:
        options = subset.Options()
        if 'fvar' in font:
            options.layout_features = ['ccmp', 'locl', 'mark', 'mkmk', 'liga']
        sub = subset.Subsetter(options)
        sub.populate(text=characters)
        sub.subset(font)
        if 'fvar' in font:
            instantiateVariableFont(font, {'wght': weight}, inplace=True)
        if font['head'].unitsPerEm != 1000:
            raise ValueError(f'{path} must use 1000 units per em')
        metrics = {cp: font['hmtx'][glyph][0] for cp, glyph in font.getBestCmap().items()}
        font.flavor = 'woff'
        output = io.BytesIO()
        font.save(output)
    data = base64.b64encode(output.getvalue()).decode('ascii')
    rule = f'@font-face{{font-family:{family};font-weight:{weight};src:url(data:font/woff;base64,{data})}}'
    return metrics, rule


def review_cell(font_faces, candidate_faces, family, sample, targets, metric_label):
    boxes = []
    for weight, widths, candidate in zip((400, 700), font_faces, candidate_faces):
        missing = sorted({ord(character) for character in sample if ord(character) not in widths})
        if missing:
            label = '・'.join(f'U+{cp:04X}' for cp in missing)
            box = f'<span class="muted">未収録 {label}</span>'
        else:
            nominal = ' + '.join(str(widths[cp]) for cp in targets) or '—'
            if any(cp in candidate and widths[cp] != candidate[cp] for cp in targets):
                nominal = f'<strong class="different">{nominal}</strong>'
            box = (f'<div class="grid" style="font-family:{family}"><span class="run" dir="auto">'
                   f'{html.escape(sample)}</span><span class="edge" aria-hidden="true"></span></div>'
                   f'<div class="numbers">{metric_label} {nominal} · 文字列 <output></output></div>')
        hidden = '' if weight == 400 else ' hidden'
        boxes.append(f'<div data-weight="{weight}"{hidden}>{box}</div>')
    return '<td>' + ''.join(boxes) + '</td>'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', nargs=2, required=True, type=Path, metavar=('REGULAR', 'BOLD'))
    parser.add_argument('--utatane', nargs=2, required=True, type=Path, metavar=('REGULAR', 'BOLD'))
    parser.add_argument('--noto', required=True, type=Path)
    parser.add_argument('--mplus', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--overview', action='store_true', help='include baseline glyph changes and reference-width differences')
    parser.add_argument('--baseline', help='revision label in the before column')
    args = parser.parse_args()
    before_label = 'Utatane 修正前' if args.overview else 'Utatane 前回案'
    groups = ((before_label, args.previous), ('Utatane 修正後', args.utatane),
              ('Noto Sans Mono CJK JP', [args.noto] * 2), ('M PLUS 1 Code', [args.mplus] * 2))
    samples = [(label, ' · '.join(f'U+{cp:04X}' for cp in marks), sample, marks)
               for label, sample, marks in SAMPLES]
    if args.overview:
        changes, references, width_count, outline_count, coverage_count = width_comparison(groups)
        ordinary = [(label, ' '.join(f'U+{ord(char):04X}' for char in sample), sample, tuple(map(ord, sample)))
                    for label, sample in OVERVIEW_SAMPLES]
        sections = [('samples', '普段使う文字・フォント差の見本', ordinary),
                    ('marks', '結合記号の配置', samples),
                    ('changes', f'Utataneの変更 {len(changes):,}字', changes),
                    ('references', f'参照フォントとの幅差 {len(references):,}字', references)]
        title = 'Utatane 文字幅と字形の比較'
        summary = (f'<p>修正前後で送り幅が変わった文字 <b>{width_count:,}字</b>、'
                   f'送り幅が同じで輪郭が変わった文字 <b>{outline_count:,}字</b>、'
                   f'収録の追加・削除 <b>{coverage_count:,}字</b>。結合時の配置は専用の見本で確認できます。</p>')
        navigation = '<nav>' + ' '.join(f'<a href="#{anchor}">{label}</a>' for anchor, label, _ in sections) + '</nav>'
    else:
        with TTFont(args.utatane[0]) as font:
            codes = sorted(cp for cp in font.getBestCmap() if is_mark(cp))
        cases = [(f'U+{cp:04X}', unicodedata.name(chr(cp), ''), mark_sample(cp), (cp,)) for cp in codes]
        sections = [('samples', '代表例', samples), ('all-marks', f'収録している結合記号 {len(cases)}字', cases)]
        title, summary, navigation = 'Utatane 結合記号の比較', '', ''
    characters = ''.join(sorted({char for _, _, rows in sections for _, _, sample, _ in rows for char in sample}))
    columns, rules, headers = [], [], []
    for index, (label, paths) in enumerate(groups):
        family = f'AuditMarks{index}'
        with TTFont(paths[0]) as font:
            version = font['name'].getDebugName(5).split(';')[0].removeprefix('Version ')
        if index == 0 and args.baseline:
            version += f' · {args.baseline}'
        headers.append(f'<th scope="col">{html.escape(label)}<small>{html.escape(version)}</small></th>')
        faces = []
        for path, weight in zip(paths, (400, 700)):
            metrics, rule = build_face(path, weight, characters, family)
            faces.append(metrics)
            rules.append(rule)
        columns.append((family, faces))

    def table(rows, heading, anchor):
        lines = []
        for label, description, sample, targets in rows:
            metric_label = '記号' if not args.overview or anchor == 'marks' or any(map(is_mark, targets)) else '字幅'
            cells = ''.join(review_cell(faces, columns[1][1], family, sample, targets, metric_label)
                            for family, faces in columns)
            lines.append(f'<tr><th scope="row">{html.escape(label)}<small>{html.escape(description)}</small></th>{cells}</tr>')
        return (f'<section id="{anchor}"><h2>{heading}</h2><div class="table-wrap"><table><colgroup><col class="labels">'
                '<col span="4"></colgroup><thead><tr><th scope="col">比較文字</th>'
                + ''.join(headers) + '</tr></thead><tbody>' + '\n'.join(lines) + '</tbody></table></div></section>')

    output = (TEMPLATE.replace('PAGE_TITLE', title).replace('SUMMARY', summary)
              .replace('NAVIGATION', navigation)
              .replace('FONT_RULES', '\n'.join(rules))
              .replace('TABLES', '\n'.join(table(rows, heading, anchor) for anchor, heading, rows in sections)))
    args.output.write_text(output, encoding='utf-8')


TEMPLATE = '''<!doctype html><html lang="ja"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PAGE_TITLE</title>
<style>
FONT_RULES
:root{color:#192b30;background:#f6f8f7;font:15px/1.5 system-ui,sans-serif}
body{width:min(1450px,calc(100% - 32px));margin:20px auto}h1{margin:0;font-size:29px}h2{font-size:18px;margin:20px 0 6px}
p{margin:5px 0 12px}.table-wrap{overflow-x:auto}table{width:100%;min-width:780px;table-layout:fixed;border-collapse:collapse;background:white}
.labels{width:19%}th,td{padding:6px 10px;border-bottom:1px solid #d8e1df;text-align:left;overflow-wrap:anywhere}
thead{background:#e6efed}small,.muted,.numbers{color:#52666b;font-size:13px}small{display:block;font-weight:400}
button{font:inherit;padding:4px 12px;border-radius:4px;border:1px solid #afc5bf;background:white;color:inherit}
button[aria-pressed=true]{background:#12685e;color:white;border-color:#12685e}
nav{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}nav a{padding:4px 10px;color:#12685e;border:1px solid #afc5bf;border-radius:4px;text-decoration:none}
nav a[aria-current=true]{background:#12685e;color:white}.controls{position:sticky;top:0;z-index:1;padding:3px 0 7px;background:#f6f8f7}
input[type=search]{padding:5px 8px;border:1px solid #afc5bf;border-radius:4px;font:inherit;margin-left:10px;max-width:56vw}
.grid{display:flex;align-items:center;height:58px;padding:0 4px;background:repeating-linear-gradient(90deg,#dce7e4 0 1px,#f4f8f7 1px 18px);background-position:4px;color:#16322e;font-size:36px;font-weight:var(--sample-weight,400);line-height:1;white-space:nowrap}
.run{display:inline-block;font-kerning:none}.edge{height:38px;border-left:2px solid #078875}
.numbers{font-variant-numeric:tabular-nums}.different{color:#8b4612}[hidden]{display:none!important}
</style>
<h1>PAGE_TITLE</h1>
<p>縦の目盛りは半角1セル、緑線は後続文字が始まる位置です。数値は1000 UPM換算です。字幅・記号はTTF上の値、文字列はブラウザーで組んだ全体の送り幅です。<strong class="different">茶色</strong>はUtatane修正後と異なる幅です。</p>
SUMMARY
<div class="controls">
NAVIGATION
<button type="button" data-select="400" aria-pressed="true">Regular</button>
<button type="button" data-select="700" aria-pressed="false">Bold</button>
<input type="search" placeholder="文字名・U+コードを検索" aria-label="文字名・U+コードを検索" hidden>
</div>
TABLES
<p><a href="https://github.com/notofonts/noto-cjk/blob/main/Sans/README.md">Notoの公式配布</a> · <a href="https://fonts.google.com/specimen/M+PLUS+1+Code">M PLUS 1 Codeの公式配布</a></p>
<script>
const navigation = document.querySelector('nav');
const sections = [...document.querySelectorAll('section')];
const search = document.querySelector('input[type=search]');
const buttons = document.querySelectorAll('[data-select]');
let view = '';
let currentWeight = '400';
let generation = 0;

function filterRows() {
  if (!view) return;
  const query = search.value.trim().toLowerCase();
  for (const row of document.querySelectorAll('section:not([hidden]) tbody tr')) {
    row.hidden = !!query && !row.textContent.toLowerCase().includes(query);
  }
}

async function select(weight) {
  const render = ++generation;
  currentWeight = weight;
  document.body.style.setProperty('--sample-weight', weight);
  for (const button of buttons) button.setAttribute('aria-pressed', button.dataset.select === weight);
  for (const box of document.querySelectorAll('[data-weight]')) box.hidden = box.dataset.weight !== weight;
  filterRows();
  await document.fonts.ready;
  if (render !== generation) return;
  for (const sample of document.querySelectorAll('section:not([hidden]) tr:not([hidden]) [data-weight]:not([hidden]) .run')) {
    const measured = sample.getBoundingClientRect().width;
    sample.closest('td').querySelector('[data-weight]:not([hidden]) output').value = Math.round(measured * 1000 / 36);
  }
  document.body.dataset.ready = weight;
}
function showSection() {
  view = sections.some(section => '#' + section.id === location.hash) ? location.hash.slice(1) : sections[0].id;
  for (const section of sections) section.hidden = section.id !== view;
  for (const link of navigation.querySelectorAll('a')) link.setAttribute('aria-current', link.hash === '#' + view);
  search.hidden = view !== 'changes' && view !== 'references';
  search.value = '';
  select(currentWeight);
}
for (const button of buttons) button.addEventListener('click', () => select(button.dataset.select));
search.addEventListener('input', () => select(currentWeight));
if (navigation) {
  addEventListener('hashchange', showSection);
  showSection();
} else {
  select('400');
}
</script></html>'''


if __name__ == '__main__':
    main()
