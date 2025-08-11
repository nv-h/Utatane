#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge
import sys

def compare_with_noto_sans_mono():
    """Noto Sans Mono CJK JPとUtataneの文字幅比較"""
    
    noto_path = './dist/NotoSansMonoCJKjp-Regular.otf'
    utatane_path = './dist/Utatane-Regular.ttf'
    mplus_path = './sourceFonts/mplus-1m-regular.ttf'
    
    try:
        noto_font = fontforge.open(noto_path)
        utatane_font = fontforge.open(utatane_path)
        mplus_font = fontforge.open(mplus_path)
    except Exception as e:
        print(f"フォントを開けませんでした: {e}")
        return
    
    print("Noto Sans Mono CJK JP vs Utatane 文字幅比較")
    print("=" * 80)
    print(f"Noto Sans Mono: {noto_path}")
    print(f"Utatane: {utatane_path}")
    print(f"M+ 1m (参考): {mplus_path}")
    print()
    
    # 共通グリフの特定
    common_codes = set()
    noto_glyphs = set()
    utatane_glyphs = set()
    mplus_glyphs = set()
    
    for glyph in noto_font.glyphs():
        if glyph.isWorthOutputting and glyph.encoding >= 0:
            noto_glyphs.add(glyph.encoding)
    
    for glyph in utatane_font.glyphs():
        if glyph.isWorthOutputting and glyph.encoding >= 0:
            utatane_glyphs.add(glyph.encoding)
    
    for glyph in mplus_font.glyphs():
        if glyph.isWorthOutputting and glyph.encoding >= 0:
            mplus_glyphs.add(glyph.encoding)
    
    # 3つのフォント全てに共通するグリフ
    common_codes = noto_glyphs & utatane_glyphs & mplus_glyphs
    
    print(f"Noto Sans Monoのグリフ数: {len(noto_glyphs)}")
    print(f"Utataneのグリフ数: {len(utatane_glyphs)}")
    print(f"M+ 1mのグリフ数: {len(mplus_glyphs)}")
    print(f"3フォント共通グリフ数: {len(common_codes)}")
    print()
    
    # 幅比較を実行
    comparison_results = []
    
    for code in sorted(common_codes):
        noto_width = noto_font[code].width
        utatane_width = utatane_font[code].width
        mplus_width = mplus_font[code].width
        
        char_display = "?"
        char_name = "UNKNOWN"
        try:
            if code < 0x10000:
                char_display = chr(code)
                import unicodedata
                char_name = unicodedata.name(chr(code), "UNKNOWN")[:50]
            else:
                char_display = f"[U+{code:04X}]"
        except:
            char_display = "[表示不可]"
        
        comparison_results.append({
            'code': code,
            'char': char_display,
            'name': char_name,
            'noto_width': noto_width,
            'utatane_width': utatane_width,
            'mplus_width': mplus_width,
            'noto_utatane_match': noto_width == utatane_width,
            'noto_mplus_match': noto_width == mplus_width,
            'utatane_mplus_match': utatane_width == mplus_width
        })
    
    # 統計情報
    total_glyphs = len(comparison_results)
    noto_utatane_matches = sum(1 for r in comparison_results if r['noto_utatane_match'])
    noto_mplus_matches = sum(1 for r in comparison_results if r['noto_mplus_match'])
    utatane_mplus_matches = sum(1 for r in comparison_results if r['utatane_mplus_match'])
    
    print("【幅一致統計】")
    print(f"Noto ⇔ Utatane一致: {noto_utatane_matches}/{total_glyphs} ({noto_utatane_matches/total_glyphs*100:.1f}%)")
    print(f"Noto ⇔ M+一致: {noto_mplus_matches}/{total_glyphs} ({noto_mplus_matches/total_glyphs*100:.1f}%)")
    print(f"Utatane ⇔ M+一致: {utatane_mplus_matches}/{total_glyphs} ({utatane_mplus_matches/total_glyphs*100:.1f}%)")
    print()
    
    # 不一致パターンの分析
    mismatches = [r for r in comparison_results if not r['noto_utatane_match']]
    print(f"【Noto vs Utatane不一致グリフ】: {len(mismatches)}件")
    print()
    
    # 問題グリフ（前回調査した106件）の比較
    problem_glyphs_codes = [
        # IPA音標文字
        0x025D, 0x026F, 0x0270, 0x0271, 0x0276, 0x0277, 0x028D, 0x0298,
        0x02A3, 0x02A4, 0x02A5, 0x02A6, 0x02A8, 0x02A9,
        # ギリシャ記号  
        0x03D2, 0x03D3, 0x03D4, 0x03D6, 0x03D8, 0x03DA, 0x03E0, 0x03E1,
        # 制御図記号（抜粋）
        0x2400, 0x2401, 0x2402, 0x2403, 0x240A, 0x240D, 0x2420, 0x2421,
        # 通貨記号
        0x20A8, 0x20A9, 0x20AA, 0x20AF, 0x20B0, 0x20B2, 0x20B3,
        # 数学演算子
        0x2225, 0x2226, 0x223C,
    ]
    
    problem_comparisons = [r for r in comparison_results if r['code'] in problem_glyphs_codes]
    
    if problem_comparisons:
        print("■ 問題グリフでのNoto vs Utatane比較")
        print("| Unicode | 文字 | Noto幅 | Utatane幅 | M+幅 | Noto判定 | 文字名 |")
        print("|---------|------|--------|-----------|------|----------|--------|")
        
        for r in problem_comparisons[:20]:  # 最初の20件
            noto_judgment = "適正" if r['noto_width'] == r['mplus_width'] else "異なる"
            print(f"| U+{r['code']:04X} | {r['char']} | {r['noto_width']} | {r['utatane_width']} | {r['mplus_width']} | {noto_judgment} | {r['name'][:30]} |")
        
        if len(problem_comparisons) > 20:
            print(f"| ... | ... | ... | ... | ... | ... | ... |")
            print(f"**計{len(problem_comparisons)}件中{noto_utatane_matches}件がNotoと一致**")
        print()
    
    # Notoが正解とした場合のパターン分析
    print("【Noto Sans Monoを正解とした場合の分析】")
    print()
    
    # Notoの幅パターン
    noto_width_patterns = {}
    for r in comparison_results:
        width = r['noto_width']
        if width not in noto_width_patterns:
            noto_width_patterns[width] = 0
        noto_width_patterns[width] += 1
    
    print("Noto Sans Monoの幅分布:")
    for width, count in sorted(noto_width_patterns.items(), key=lambda x: -x[1])[:10]:
        print(f"  幅{width}: {count}件")
    print()
    
    # 問題グリフでNotoが採用している幅
    if problem_comparisons:
        print("問題グリフでのNoto判定:")
        noto_500_count = sum(1 for r in problem_comparisons if r['noto_width'] == 500)
        noto_1000_count = sum(1 for r in problem_comparisons if r['noto_width'] == 1000)
        noto_other_count = len(problem_comparisons) - noto_500_count - noto_1000_count
        
        print(f"  半角(500): {noto_500_count}件")
        print(f"  全角(1000): {noto_1000_count}件") 
        print(f"  その他: {noto_other_count}件")
        print()
    
    # UtataneがNotoと異なる判定をしているケースの詳細
    incorrect_utatane = [r for r in problem_comparisons if not r['noto_utatane_match']]
    if incorrect_utatane:
        print(f"■ UtataneがNotoと異なる判定をしている問題グリフ: {len(incorrect_utatane)}件")
        print("| Unicode | 文字 | Noto幅 | Utatane幅 | 差分 | 問題度 |")
        print("|---------|------|--------|-----------|------|--------|") 
        
        for r in incorrect_utatane[:15]:
            diff = r['utatane_width'] - r['noto_width']
            severity = "高" if abs(diff) >= 500 else "中" if abs(diff) >= 200 else "低"
            print(f"| U+{r['code']:04X} | {r['char']} | {r['noto_width']} | {r['utatane_width']} | {diff:+d} | {severity} |")
        
        if len(incorrect_utatane) > 15:
            print(f"**他{len(incorrect_utatane)-15}件**")
        print()
    
    # 結論
    print("【結論】")
    print()
    
    if noto_utatane_matches / total_glyphs >= 0.95:
        print("✓ NotoとUtataneは高い互換性を持っている")
    elif noto_utatane_matches / total_glyphs >= 0.9:
        print("△ NotoとUtataneは概ね互換性があるが改善の余地あり")
    else:
        print("✗ NotoとUtataneの互換性に大きな問題がある")
    
    problem_noto_agrees_mplus = sum(1 for r in problem_comparisons if r['noto_width'] == r['mplus_width'])
    if problem_comparisons:
        print(f"✓ 問題グリフの{problem_noto_agrees_mplus}/{len(problem_comparisons)}件でNotoがM+と同じ判定")
        print(f"✓ これはNoto Sans MonoもM+の幅設計を採用していることを示唆")
        
        if problem_noto_agrees_mplus / len(problem_comparisons) >= 0.8:
            print("→ UtataneもM+基準に合わせるべき（Noto互換のため）")
    
    noto_font.close()
    utatane_font.close()
    mplus_font.close()

if __name__ == '__main__':
    compare_with_noto_sans_mono()