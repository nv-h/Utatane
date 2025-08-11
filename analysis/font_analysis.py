#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Font Analysis CLI for the Utatane project

Run with FontForge Python:
  fontforge -lang=py -script analysis/font_analysis.py <subcommand> [options]

Subcommands:
  list-fonts                   Show available font keys and paths
  info                         Per-font width stats and samples
  compare                      Compare widths between two fonts
  ranges                       Analyze widths by Unicode ranges
  symbols                      Analyze symbol-category widths
  mismatch                     Report glyphs that match a width pattern
  diagnose                     Diagnose a single font (basic info, widths)

Examples:
  fontforge -lang=py -script analysis/font_analysis.py list-fonts
  fontforge -lang=py -script analysis/font_analysis.py info --font mplus --samples
  fontforge -lang=py -script analysis/font_analysis.py compare --base mplus --target utatane --names --max-display 100
  fontforge -lang=py -script analysis/font_analysis.py ranges --fonts mplus,ubuntu --ranges ひらがな,カタカナ --max-samples 5
  fontforge -lang=py -script analysis/font_analysis.py symbols --fonts mplus,ubuntu,yasashisa --categories 幾何図形,矢印 --brief
  fontforge -lang=py -script analysis/font_analysis.py mismatch --base mplus --target utatane --pattern 500 1000 --format markdown
  fontforge -lang=py -script analysis/font_analysis.py diagnose --font NotoSansMonoCJKjp-VF --max-samples 20
"""

from typing import List, Dict
import sys

try:
    import argparse
except Exception:
    argparse = None  # Fallback to manual parsing if needed

# FontForge is required via font_analysis_utils. Import checks happen there.


# Shared utils
from font_analysis_utils import (
    create_analyzer_with_error_handling,
    ReportGenerator,
    FontAnalyzer,
    list_available_fonts,
)


def cmd_list_fonts(_args):
    list_available_fonts()


def cmd_info(args):
    font_name = args.font
    show_samples = args.samples

    analyzer = create_analyzer_with_error_handling([font_name])
    if not analyzer:
        return 1

    try:
        ReportGenerator.print_font_info(analyzer, font_name)

        ranges = {
            "ASCII": list(range(0x0020, 0x007F + 1)),
            "ひらがな": list(range(0x3040, 0x309F + 1)),
            "カタカナ": list(range(0x30A0, 0x30FF + 1)),
            "半角カタカナ": list(range(0xFF61, 0xFF9F + 1)),
            "罫線": list(range(0x2500, 0x257F + 1)),
            "ブロック要素": list(range(0x2580, 0x259F + 1)),
        }

        width_stats: Dict[str, Dict] = {}
        for range_name, codes in ranges.items():
            widths = []
            samples = []
            for code in codes:
                w = analyzer.get_glyph_width(font_name, code)
                if w is not None:
                    widths.append(w)
                    samples.append((code, analyzer._format_char(code), w))
            if widths:
                width_stats[range_name] = {
                    "count": len(widths),
                    "min": min(widths),
                    "max": max(widths),
                    "avg": sum(widths) / len(widths),
                    "unique": sorted(set(widths)),
                    "samples": samples[:10],
                }

        for range_name, st in width_stats.items():
            print(f"\n【{range_name}】")
            print(f"  文字数: {st['count']}")
            print(f"  幅の範囲: {st['min']} - {st['max']}")
            print(f"  平均幅: {st['avg']:.1f}")
            print(f"  固有の幅: {st['unique']}")
            if show_samples:
                print("  サンプル:")
                for code, ch, w in st["samples"]:
                    try:
                        print(f"    U+{code:04X} '{ch}' width={w}")
                    except Exception:
                        print(f"    U+{code:04X} [表示不可] width={w}")

        if "ASCII" in width_stats and "ひらがな" in width_stats:
            ascii_u = width_stats["ASCII"]["unique"]
            hira_u = width_stats["ひらがな"]["unique"]
            ascii_w = ascii_u[0] if len(ascii_u) == 1 else None
            hira_w = hira_u[0] if len(hira_u) == 1 else None
            print("\n【全角/半角基準の推定】")
            print(f"  ASCII幅: {ascii_w}  ひらがな幅: {hira_w}")
            if ascii_w and hira_w:
                print(f"  全角/半角比率: {hira_w/ascii_w:.3f}")
            else:
                if len(ascii_u) > 1:
                    print(f"  ASCII幅のばらつき: {ascii_u}")
                if len(hira_u) > 1:
                    print(f"  ひらがな幅のばらつき: {hira_u}")
    finally:
        analyzer.close_fonts()


def cmd_compare(args):
    base = args.base
    target = args.target
    names = args.names
    max_display = args.max_display

    analyzer = create_analyzer_with_error_handling([base, target])
    if not analyzer:
        return 1

    try:
        for fn in [base, target]:
            ReportGenerator.print_font_info(analyzer, fn)
        print()

        base_codes = analyzer.get_glyph_set(base)
        target_codes = analyzer.get_glyph_set(target)
        common = base_codes & target_codes
        print(f"{base.upper()}のグリフ数: {len(base_codes)}")
        print(f"{target.upper()}のグリフ数: {len(target_codes)}")
        print(f"共通グリフ数: {len(common)}\n")

        results = analyzer.compare_widths(sorted(common), [base, target])
        inconsistencies = ReportGenerator.print_width_comparison_summary(
            results, f"{base.upper()} vs {target.upper()} 幅比較結果"
        )
        if not inconsistencies:
            return 0
        print("\n【幅不一致グリフ（抜粋）】")
        print(f"{'文字':<8} {'コード':<12} {base.upper()+'幅':<8} {target.upper()+'幅':<8} 差分" + ("  文字名" if names else ""))
        print("-" * (70 + (40 if names else 0)))
        shown = 0
        for r in inconsistencies:
            if shown >= max_display:
                break
            code = r["code"]
            ch = r["char"]
            bw = r["widths"].get(base)
            tw = r["widths"].get(target)
            if bw is None or tw is None:
                continue
            row = f"{ch:<8} U+{code:04X}     {bw:<8} {tw:<8} {tw-bw:+d}"
            if names:
                row += f"  {get_unicode_name(code)}"
            print(row)
            shown += 1
        if len(inconsistencies) > shown:
            print(f"... 他{len(inconsistencies)-shown}件")

        # Range breakdown
        print("\n【Unicode範囲別の不一致サマリ】")
        breakdown = categorize_by_ranges(inconsistencies)
        for rn, items in breakdown.items():
            print(f"{rn}: {len(items)}件")
    finally:
        analyzer.close_fonts()


def cmd_ranges(args):
    fonts = args.fonts.split(",") if args.fonts else ["mplus", "ubuntu"]
    range_names = args.ranges.split(",") if args.ranges else None
    show_samples = not args.no_samples
    max_samples = args.max_samples

    analyzer = create_analyzer_with_error_handling(fonts)
    if not analyzer:
        return 1

    try:
        for fn in fonts:
            ReportGenerator.print_font_info(analyzer, fn)
        unicode_ranges = FontAnalyzer.get_unicode_ranges()
        if range_names:
            unicode_ranges = {k: v for k, v in unicode_ranges.items() if k in range_names}

        total = 0
        mismatches = 0
        for rn, (start, end) in unicode_ranges.items():
            codes = list(range(start, end + 1))
            presence = {}
            for fn in fonts:
                present = [c for c in codes if analyzer.get_glyph_width(fn, c) is not None]
                presence[fn] = set(present)
                print(f"\n【{rn}】(U+{start:04X}-U+{end:04X})  {fn}: {len(present)}文字")

            common = list(set.intersection(*presence.values())) if fonts else []
            print(f"  共通文字: {len(common)}文字")
            if not common:
                continue

            comp = analyzer.compare_widths(common, fonts)
            inc = [r for r in comp if r["has_inconsistency"]]
            if inc:
                print(f"  ⚠ 幅不整合: {len(inc)}/{len(common)}文字")
                mismatches += len(inc)
                if show_samples:
                    print(f"  不整合サンプル(最大{max_samples}件):")
                    for r in inc[:max_samples]:
                        parts = ", ".join([f"{fn}={r['widths'].get(fn)}" for fn in fonts if r['widths'].get(fn) is not None])
                        print(f"    U+{r['code']:04X} '{r['char']}': {parts}")
            else:
                print(f"  ✓ 全て一致: {len(common)}文字")
            total += len(common)

        print("\n" + "=" * 70)
        print("【総合結果】")
        if total:
            print(f"分析文字数: {total}  幅不整合: {mismatches} ({mismatches/total*100:.1f}%)")
        else:
            print("分析対象なし")
    finally:
        analyzer.close_fonts()


def cmd_symbols(args):
    fonts = args.fonts.split(",") if args.fonts else ["mplus", "ubuntu", "yasashisa"]
    categories = args.categories.split(",") if args.categories else None
    brief = args.brief

    analyzer = create_analyzer_with_error_handling(fonts)
    if not analyzer:
        return 1

    try:
        for fn in fonts:
            ReportGenerator.print_font_info(analyzer, fn)
        print("=" * 70)

        cats = FontAnalyzer.get_symbol_categories()
        if categories:
            cats = {k: v for k, v in cats.items() if k in categories}

        for cat, codes in cats.items():
            print(f"\n【{cat}】")
            mism = 0
            for code in codes:
                wi = {}
                vals = []
                for fn in fonts:
                    w = analyzer.get_glyph_width(fn, code)
                    wi[fn] = w
                    if w is not None:
                        vals.append(w)
                status = ""
                if len(set(vals)) > 1:
                    status = "⚠ 幅不統一"
                    mism += 1
                elif len(vals) == 0:
                    status = "全フォントに無し"
                elif len(vals) == 1 and len([v for v in wi.values() if v is not None]) == 1:
                    only = [fn for fn, v in wi.items() if v is not None][0]
                    status = f"{only}のみ"
                else:
                    status = "統一済み"

                if not brief:
                    row = f"{analyzer._format_char(code):<8} U+{code:04X}"
                    for fn in fonts:
                        w = wi.get(fn)
                        row += f"  {str(w) if w is not None else 'なし':<8}"
                    row += f" {status}"
                    print(row)
            if mism:
                print(f"  → {mism}件の幅不統一を発見")
    finally:
        analyzer.close_fonts()


def cmd_mismatch(args):
    base = args.base
    target = args.target
    bw = args.pattern[0]
    tw = args.pattern[1]
    fmt = args.format

    analyzer = create_analyzer_with_error_handling([base, target])
    if not analyzer:
        return 1

    try:
        base_codes = analyzer.get_glyph_set(base)
        target_codes = analyzer.get_glyph_set(target)
        common = sorted(base_codes & target_codes)

        hits = []
        for code in common:
            b = analyzer.get_glyph_width(base, code)
            t = analyzer.get_glyph_width(target, code)
            if b == bw and t == tw:
                hits.append(code)

        if fmt == "csv":
            print("Unicode,Character,Name,Block,BaseWidth,TargetWidth")
        if fmt == "markdown":
            print(f"## 幅不一致グリフ一覧（{len(hits)}件）")
            print()

        for code in hits:
            ch = FontAnalyzer._format_char(code)
            name = get_unicode_name(code)
            block = get_unicode_block_name(code)
            if fmt == "csv":
                # escape commas
                def esc(s: str) -> str:
                    return s.replace(",", "\\,")
                print(f"U+{code:04X},{esc(ch)},{esc(name)},{esc(block)},{bw},{tw}")
            elif fmt == "text":
                print(f"U+{code:04X} '{ch}' {name} [{block}] {bw}->{tw}")
            else:
                # markdown
                # print header for each block grouped output later if needed; keep simple list
                print(f"- U+{code:04X} '{ch}' {name} ({block})")

        if fmt == "markdown" and not hits:
            print("一致するグリフはありませんでした。")
    finally:
        analyzer.close_fonts()


def cmd_diagnose(args):
    font_name = args.font
    show_samples = not args.no_samples
    max_samples = args.max_samples

    analyzer = create_analyzer_with_error_handling([font_name])
    if not analyzer:
        return 1

    try:
        font = analyzer.fonts[font_name]
        info = analyzer.get_font_info(font_name)
        print(f"{font_name.upper()} フォント診断")
        print("=" * 80)
        print(f"パス: {info['path']}")
        print(f"em: {info['em_square']}  ascent: {info['ascent']}  descent: {info['descent']}")

        total = 0
        worth = 0
        enc = 0
        glyphs = []
        for g in font.glyphs():
            total += 1
            if g.isWorthOutputting:
                worth += 1
                if g.encoding >= 0:
                    enc += 1
                    glyphs.append(g)
        print("【グリフ統計】")
        print(f"  総数: {total}  出力対象: {worth}  エンコード済: {enc}")

        if enc and show_samples:
            print("\n【サンプル】")
            for i, g in enumerate(sorted(glyphs, key=lambda x: x.encoding)[:max_samples]):
                ch = FontAnalyzer._format_char(g.encoding)
                name = get_unicode_name(g.encoding)
                print(f"  {i+1:3d}. U+{g.encoding:04X} '{ch}' width={g.width} {name}")

        # Width distribution
        widths: Dict[int, int] = {}
        for g in glyphs:
            widths[g.width] = widths.get(g.width, 0) + 1
        print("\n【幅分布（上位10）】")
        for w, c in sorted(widths.items(), key=lambda x: -x[1])[:10]:
            print(f"  幅{w}: {c}件")
    finally:
        analyzer.close_fonts()


# Helpers

def get_unicode_name(code: int) -> str:
    try:
        import unicodedata
        if code < 0x110000:
            return unicodedata.name(chr(code), "UNKNOWN")
    except Exception:
        pass
    return "UNKNOWN"



def get_unicode_block_name(code: int) -> str:
    if 0x0250 <= code <= 0x02AF:
        return "IPA拡張"
    if 0x03D0 <= code <= 0x03FF:
        return "ギリシャ記号・コプト文字"
    if 0x1E00 <= code <= 0x1EFF:
        return "拡張ラテンB"
    if 0x2000 <= code <= 0x206F:
        return "一般句読点"
    if 0x20A0 <= code <= 0x20CF:
        return "通貨記号"
    if 0x2100 <= code <= 0x214F:
        return "文字様記号"
    if 0x2190 <= code <= 0x21FF:
        return "矢印"
    if 0x2200 <= code <= 0x22FF:
        return "数学演算子"
    if 0x2300 <= code <= 0x23FF:
        return "その他技術記号"
    if 0x2400 <= code <= 0x243F:
        return "制御図記号"
    if 0x2500 <= code <= 0x257F:
        return "罫線"
    if 0x2580 <= code <= 0x259F:
        return "ブロック要素"
    if 0x3000 <= code <= 0x303F:
        return "CJKの記号と句読点"
    if 0x3040 <= code <= 0x309F:
        return "ひらがな"
    if 0x30A0 <= code <= 0x30FF:
        return "カタカナ"
    if 0x4E00 <= code <= 0x9FFF:
        return "CJK統合漢字"
    if 0xFF00 <= code <= 0xFFEF:
        return "半角・全角形"
    return "その他"



def categorize_by_ranges(results: List[Dict]) -> Dict[str, List[Dict]]:
    ranges = FontAnalyzer.get_unicode_ranges()
    out: Dict[str, List[Dict]] = {k: [] for k in ranges.keys()}
    out["その他"] = []
    for r in results:
        code = r["code"]
        placed = False
        for name, (start, end) in ranges.items():
            if start <= code <= end:
                out[name].append(r)
                placed = True
                break
        if not placed:
            out["その他"].append(r)
    return {k: v for k, v in out.items() if v}



def build_parser():
    if argparse is None:
        return None
    p = argparse.ArgumentParser(description="Utatane Font Analysis CLI")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("list-fonts", help="利用可能なフォント一覧を表示")
    s.set_defaults(func=cmd_list_fonts)

    s = sub.add_parser("info", help="フォントの基本幅統計とサンプル表示")
    s.add_argument("--font", default="mplus")
    s.add_argument("--samples", action="store_true", help="サンプル文字を表示")
    s.set_defaults(func=cmd_info)

    s = sub.add_parser("compare", help="2フォント間の幅比較")
    s.add_argument("--base", default="mplus")
    s.add_argument("--target", default="utatane")
    s.add_argument("--names", action="store_true", help="Unicode名を表示")
    s.add_argument("--max-display", type=int, default=50)
    s.set_defaults(func=cmd_compare)

    s = sub.add_parser("ranges", help="Unicode範囲別の幅分析")
    s.add_argument("--fonts", help="カンマ区切りフォント", default=None)
    s.add_argument("--ranges", help="カンマ区切り範囲名", default=None)
    s.add_argument("--no-samples", action="store_true")
    s.add_argument("--max-samples", type=int, default=10)
    s.set_defaults(func=cmd_ranges)

    s = sub.add_parser("symbols", help="記号カテゴリの幅分析")
    s.add_argument("--fonts", help="カンマ区切りフォント", default=None)
    s.add_argument("--categories", help="カンマ区切りカテゴリ名", default=None)
    s.add_argument("--brief", action="store_true", help="簡潔出力")
    s.set_defaults(func=cmd_symbols)

    s = sub.add_parser("mismatch", help="幅パターンの不一致レポート")
    s.add_argument("--base", default="mplus")
    s.add_argument("--target", default="utatane")
    s.add_argument("--pattern", nargs=2, type=int, default=[500, 1000])
    s.add_argument("--format", choices=["markdown", "text", "csv"], default="markdown")
    s.set_defaults(func=cmd_mismatch)

    s = sub.add_parser("diagnose", help="フォント診断")
    s.add_argument("--font", default="NotoSansMonoCJKjp-VF")
    s.add_argument("--no-samples", action="store_true")
    s.add_argument("--max-samples", type=int, default=20)
    s.set_defaults(func=cmd_diagnose)

    return p



def main():
    parser = build_parser()
    if parser is None:
        # minimal fallback
        print("argparseが利用できません。簡易モードで実行してください。")
        print("例: fontforge -lang=py -script analysis/font_analysis.py list-fonts")
        return 1
    args = parser.parse_args(sys.argv[1:])
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
