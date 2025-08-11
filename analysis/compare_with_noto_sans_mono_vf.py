#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge
import sys

def compare_with_noto_sans_mono_vf():
    """Noto Sans Mono CJK JP VF(可変フォント)とUtataneの文字幅比較"""
    
    noto_path = './dist/NotoSansMonoCJKjp-VF.ttf'
    utatane_path = './dist/Utatane-Regular.ttf'
    mplus_path = './sourceFonts/mplus-1m-regular.ttf'
    
    try:
        noto_font = fontforge.open(noto_path)
        utatane_font = fontforge.open(utatane_path)
        mplus_font = fontforge.open(mplus_path)
    except Exception as e:
        print(f"フォントを開けませんでした: {e}")
        return
    
    print("Noto Sans Mono CJK JP VF vs Utatane 文字幅比較")
    print("=" * 80)
    print(f"Noto Sans Mono VF: {noto_path}")
    print(f"Utatane: {utatane_path}")
    print(f"M+ 1m (参考): {mplus_path}")
    print()
    
    # フォント基本情報
    print("【フォント基本情報】")
    print(f"Noto: {noto_font.fontname} / EM={noto_font.em}")
    print(f"Utatane: {utatane_font.fontname} / EM={utatane_font.em}")
    print(f"M+: {mplus_font.fontname} / EM={mplus_font.em}")
    print()
    
    # 共通グリフの特定
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
    
    # 共通グリフ
    noto_utatane_common = noto_glyphs & utatane_glyphs
    all_common = noto_glyphs & utatane_glyphs & mplus_glyphs
    
    print(f"【グリフ統計】")
    print(f"Noto VFのグリフ数: {len(noto_glyphs)}")
    print(f"Utataneのグリフ数: {len(utatane_glyphs)}")
    print(f"M+ 1mのグリフ数: {len(mplus_glyphs)}")
    print(f"Noto-Utatane共通: {len(noto_utatane_common)}")
    print(f"3フォント共通: {len(all_common)}")
    print()
    
    if len(noto_utatane_common) == 0:
        print("❌ 共通グリフが見つかりません。フォントの読み込みに問題があります。")
        
        # デバッグ情報
        print("\n【デバッグ情報】")
        print("Noto VFの最初の20グリフ:")
        noto_sample = list(noto_glyphs)[:20]
        for code in sorted(noto_sample):
            char = chr(code) if code < 0x10000 else f"[U+{code:04X}]"
            print(f"  U+{code:04X} {char}")
        
        noto_font.close()
        utatane_font.close()
        mplus_font.close()
        return
    
    # 幅比較を実行
    comparison_results = []
    
    for code in sorted(noto_utatane_common):
        noto_width = noto_font[code].width
        utatane_width = utatane_font[code].width
        mplus_width = mplus_font[code].width if code in mplus_glyphs else None
        
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
            'noto_mplus_match': noto_width == mplus_width if mplus_width else None,
            'utatane_mplus_match': utatane_width == mplus_width if mplus_width else None
        })
    
    # 統計情報
    total_glyphs = len(comparison_results)
    noto_utatane_matches = sum(1 for r in comparison_results if r['noto_utatane_match'])
    
    with_mplus = [r for r in comparison_results if r['mplus_width'] is not None]
    noto_mplus_matches = sum(1 for r in with_mplus if r['noto_mplus_match'])
    utatane_mplus_matches = sum(1 for r in with_mplus if r['utatane_mplus_match'])
    
    print("【幅一致統計】")
    print(f"比較対象グリフ数: {total_glyphs}")
    print(f"Noto ⇔ Utatane一致: {noto_utatane_matches}/{total_glyphs} ({noto_utatane_matches/total_glyphs*100:.1f}%)")
    if with_mplus:
        print(f"M+含む比較グリフ数: {len(with_mplus)}")
        print(f"Noto ⇔ M+一致: {noto_mplus_matches}/{len(with_mplus)} ({noto_mplus_matches/len(with_mplus)*100:.1f}%)")
        print(f"Utatane ⇔ M+一致: {utatane_mplus_matches}/{len(with_mplus)} ({utatane_mplus_matches/len(with_mplus)*100:.1f}%)")
    print()
    
    # 不一致の詳細分析
    mismatches = [r for r in comparison_results if not r['noto_utatane_match']]
    print(f"【Noto vs Utatane不一致グリフ】: {len(mismatches)}件")
    
    if mismatches:
        # 不一致のパターン分析
        print("\n不一致パターン分析:")
        patterns = {}
        for r in mismatches:
            pattern = f"{r['noto_width']}→{r['utatane_width']}"
            if pattern not in patterns:
                patterns[pattern] = 0
            patterns[pattern] += 1
        
        for pattern, count in sorted(patterns.items(), key=lambda x: -x[1])[:10]:
            print(f"  {pattern}: {count}件")
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
        # 拡張ラテン文字（抜粋）
        0x1E3E, 0x1E3F, 0x1E40, 0x1E41, 0x1ECC, 0x1ECE,
    ]
    
    problem_comparisons = [r for r in comparison_results if r['code'] in problem_glyphs_codes]
    
    if problem_comparisons:
        print(f"■ 問題グリフでの比較結果: {len(problem_comparisons)}件中{len([r for r in problem_comparisons if r['noto_utatane_match']])}件一致")
        print("| Unicode | 文字 | Noto幅 | Utatane幅 | M+幅 | Noto判定 | 問題度 | 文字名 |")
        print("|---------|------|--------|-----------|------|----------|--------|--------|")
        
        for r in sorted(problem_comparisons, key=lambda x: x['code'])[:25]:  # 最初の25件
            noto_judgment = "適正" if r['mplus_width'] and r['noto_width'] == r['mplus_width'] else "M+と差異" if r['mplus_width'] else "M+なし"
            diff = r['utatane_width'] - r['noto_width'] if r['noto_width'] else 0
            severity = "高" if abs(diff) >= 500 else "中" if abs(diff) >= 100 else "低"
            match_mark = "✓" if r['noto_utatane_match'] else "✗"
            
            print(f"| U+{r['code']:04X} | {r['char']} | {r['noto_width']} | {r['utatane_width']} | {r['mplus_width'] or 'N/A'} | {noto_judgment} | {severity} {match_mark} | {r['name'][:25]} |")
        
        if len(problem_comparisons) > 25:
            remaining = len(problem_comparisons) - 25
            print(f"| ... | ... | ... | ... | ... | ... | ... | 他{remaining}件 |")
        print()
    
    # Noto VFの幅パターン分析
    print("【Noto VFの幅パターン分析】")
    noto_width_patterns = {}
    for r in comparison_results:
        width = r['noto_width']
        if width not in noto_width_patterns:
            noto_width_patterns[width] = 0
        noto_width_patterns[width] += 1
    
    print("Noto VFの幅分布（上位10パターン）:")
    for width, count in sorted(noto_width_patterns.items(), key=lambda x: -x[1])[:10]:
        percentage = count / total_glyphs * 100
        print(f"  幅{width}: {count}件 ({percentage:.1f}%)")
    print()
    
    # 問題グリフでのNoto判定
    if problem_comparisons:
        print("【問題グリフでのNoto VF判定】")
        noto_500_count = sum(1 for r in problem_comparisons if r['noto_width'] == 500)
        noto_1000_count = sum(1 for r in problem_comparisons if r['noto_width'] == 1000)
        noto_other_count = len(problem_comparisons) - noto_500_count - noto_1000_count
        
        print(f"半角(500): {noto_500_count}件")
        print(f"全角(1000): {noto_1000_count}件") 
        print(f"その他: {noto_other_count}件")
        
        # M+との一致率
        if with_mplus:
            problem_with_mplus = [r for r in problem_comparisons if r['mplus_width'] is not None]
            if problem_with_mplus:
                noto_mplus_agree = sum(1 for r in problem_with_mplus if r['noto_width'] == r['mplus_width'])
                print(f"M+と一致: {noto_mplus_agree}/{len(problem_with_mplus)}件 ({noto_mplus_agree/len(problem_with_mplus)*100:.1f}%)")
        print()
    
    # 結論
    print("【結論・推奨事項】")
    print()
    
    match_rate = noto_utatane_matches / total_glyphs
    if match_rate >= 0.95:
        print("✅ NotoとUtataneは非常に高い互換性を持っています")
    elif match_rate >= 0.9:
        print("✅ NotoとUtataneは高い互換性を持っています") 
    elif match_rate >= 0.8:
        print("⚠️  NotoとUtataneは概ね互換性がありますが改善の余地があります")
    else:
        print("❌ NotoとUtataneの互換性に大きな問題があります")
    
    print(f"互換性スコア: {match_rate*100:.1f}%")
    
    if problem_comparisons:
        problem_mismatch = len([r for r in problem_comparisons if not r['noto_utatane_match']])
        print(f"問題グリフ不一致: {problem_mismatch}/{len(problem_comparisons)}件")
        
        if problem_mismatch > 0:
            print("→ これらのグリフをM+/Noto基準に修正することを推奨")
            print("→ 特にIPA・ギリシャ・通貨記号は学術・国際文書で重要")
    
    noto_font.close()
    utatane_font.close()
    mplus_font.close()

if __name__ == '__main__':
    compare_with_noto_sans_mono_vf()