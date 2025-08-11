#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge
import sys

def investigate_yasashisa_gothic_influence():
    """やさしさゴシックの文字幅がM+との判定差異に与える影響を調査"""
    
    mplus_path = './sourceFonts/mplus-1m-regular.ttf'
    yasashisa_path = './sourceFonts/YasashisaGothicBold-V2.ttf'
    utatane_path = './dist/Utatane-Regular.ttf'
    
    try:
        mplus_font = fontforge.open(mplus_path)
        yasashisa_font = fontforge.open(yasashisa_path)
        utatane_font = fontforge.open(utatane_path)
    except Exception as e:
        print(f"フォントを開けませんでした: {e}")
        return
    
    print("やさしさゴシックの文字幅影響調査")
    print("=" * 80)
    print("問題グリフがどのフォントに存在し、どのような幅を持っているかを調査")
    print()
    
    # 誤全角化されたグリフのリスト（主要なもの）
    problem_glyphs = [
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
        # 一般句読点
        0x203F, 0x2040, 0x2053,
        # 文字様記号
        0x211E, 0x2127,
        # 技術記号
        0x23CE,
        # 合字
        0xFB00, 0xFB03, 0xFB04
    ]
    
    print(f"調査対象グリフ: {len(problem_glyphs)}件")
    print()
    
    # 各フォントでのグリフ存在・幅情報を収集
    font_analysis = []
    
    for code in problem_glyphs:
        char_display = "?"
        char_name = "UNKNOWN"
        
        try:
            if code < 0x10000:
                char_display = chr(code)
                import unicodedata
                char_name = unicodedata.name(chr(code), "UNKNOWN")[:50]  # 長すぎる名前を短縮
            else:
                char_display = f"[U+{code:04X}]"
        except:
            char_display = "[表示不可]"
        
        # 各フォントでの存在・幅チェック
        mplus_exists = code in mplus_font and mplus_font[code].isWorthOutputting
        yasashisa_exists = code in yasashisa_font and yasashisa_font[code].isWorthOutputting
        utatane_exists = code in utatane_font and utatane_font[code].isWorthOutputting
        
        mplus_width = mplus_font[code].width if mplus_exists else None
        yasashisa_width = yasashisa_font[code].width if yasashisa_exists else None
        utatane_width = utatane_font[code].width if utatane_exists else None
        
        analysis = {
            'code': code,
            'char': char_display,
            'name': char_name,
            'mplus_exists': mplus_exists,
            'yasashisa_exists': yasashisa_exists,
            'utatane_exists': utatane_exists,
            'mplus_width': mplus_width,
            'yasashisa_width': yasashisa_width,
            'utatane_width': utatane_width
        }
        
        font_analysis.append(analysis)
    
    # 結果の分類と分析
    print("【フォント別存在状況】")
    print()
    
    # パターン分類
    patterns = {
        'mplus_only': [],      # M+のみに存在
        'yasashisa_only': [],  # やさしさゴシックのみに存在
        'both_fonts': [],      # 両方に存在
        'neither': []          # どちらにも存在しない（Utatane独自？）
    }
    
    for analysis in font_analysis:
        if analysis['mplus_exists'] and not analysis['yasashisa_exists']:
            patterns['mplus_only'].append(analysis)
        elif not analysis['mplus_exists'] and analysis['yasashisa_exists']:
            patterns['yasashisa_only'].append(analysis)
        elif analysis['mplus_exists'] and analysis['yasashisa_exists']:
            patterns['both_fonts'].append(analysis)
        else:
            patterns['neither'].append(analysis)
    
    print(f"M+のみに存在: {len(patterns['mplus_only'])}件")
    print(f"やさしさゴシックのみに存在: {len(patterns['yasashisa_only'])}件")
    print(f"両方のフォントに存在: {len(patterns['both_fonts'])}件")
    print(f"どちらにも存在しない: {len(patterns['neither'])}件")
    print()
    
    # M+のみに存在するグリフの詳細
    if patterns['mplus_only']:
        print("■ M+のみに存在するグリフ（やさしさゴシックの影響なし）")
        print("| Unicode | 文字 | 文字名 | M+幅 | Utatane幅 |")
        print("|---------|------|--------|------|-----------|")
        for g in patterns['mplus_only'][:10]:  # 最初の10件
            print(f"| U+{g['code']:04X} | {g['char']} | {g['name']} | {g['mplus_width']} | {g['utatane_width']} |")
        if len(patterns['mplus_only']) > 10:
            print(f"| ... | ... | ... | ... | ... |")
            print(f"**計{len(patterns['mplus_only'])}件**")
        print()
    
    # やさしさゴシックのみに存在するグリフの詳細
    if patterns['yasashisa_only']:
        print("■ やさしさゴシックのみに存在するグリフ")
        print("| Unicode | 文字 | 文字名 | やさしさ幅 | Utatane幅 |")
        print("|---------|------|--------|------------|-----------|")
        for g in patterns['yasashisa_only'][:10]:
            print(f"| U+{g['code']:04X} | {g['char']} | {g['name']} | {g['yasashisa_width']} | {g['utatane_width']} |")
        if len(patterns['yasashisa_only']) > 10:
            print(f"**計{len(patterns['yasashisa_only'])}件**")
        print()
    
    # 両方に存在するグリフの詳細
    if patterns['both_fonts']:
        print("■ 両方のフォントに存在するグリフ（幅比較）")
        print("| Unicode | 文字 | M+幅 | やさしさ幅 | Utatane幅 | 判定元 |")
        print("|---------|------|------|------------|-----------|--------|")
        for g in patterns['both_fonts'][:15]:
            # どちらの幅により近いかを判定
            mplus_diff = abs(g['utatane_width'] - g['mplus_width']) if g['mplus_width'] else float('inf')
            yasashisa_diff = abs(g['utatane_width'] - g['yasashisa_width']) if g['yasashisa_width'] else float('inf')
            
            if mplus_diff < yasashisa_diff:
                source = "M+"
            elif yasashisa_diff < mplus_diff:
                source = "やさしさ"
            else:
                source = "同等"
                
            print(f"| U+{g['code']:04X} | {g['char']} | {g['mplus_width']} | {g['yasashisa_width']} | {g['utatane_width']} | {source} |")
        if len(patterns['both_fonts']) > 15:
            print(f"**計{len(patterns['both_fonts'])}件**")
        print()
    
    # 幅の影響分析
    print("【やさしさゴシックの幅影響分析】")
    print()
    
    # やさしさゴシックが関与しているケース
    yasashisa_involved = len(patterns['yasashisa_only']) + len(patterns['both_fonts'])
    mplus_only_cases = len(patterns['mplus_only'])
    
    print(f"やさしさゴシックが関与: {yasashisa_involved}件")
    print(f"M+のみから生成: {mplus_only_cases}件")
    print()
    
    if yasashisa_involved > 0:
        print("■ やさしさゴシック関与ケースの幅分析")
        
        # やさしさゴシックの典型的な幅を調査
        yasashisa_widths = []
        for g in patterns['yasashisa_only'] + patterns['both_fonts']:
            if g['yasashisa_width']:
                yasashisa_widths.append(g['yasashisa_width'])
        
        if yasashisa_widths:
            unique_widths = sorted(set(yasashisa_widths))
            width_counts = {w: yasashisa_widths.count(w) for w in unique_widths}
            
            print("やさしさゴシックの文字幅分布:")
            for width, count in sorted(width_counts.items(), key=lambda x: -x[1]):
                print(f"  幅{width}: {count}件")
            print()
    
    # 結論
    print("【結論】")
    print()
    
    if mplus_only_cases > yasashisa_involved:
        print("✓ 問題グリフの多くはM+フォントのみに存在")
        print("✓ やさしさゴシックの影響ではなく、M+グリフの縮小処理が原因")
        print("✓ 日本語フォント処理パス（JP_REDUCTION_MAT等）を通ることで幅が変化")
    else:
        print("✓ やさしさゴシックの影響が大きい可能性")
        print("✓ やさしさゴシックの文字幅が判定に影響している")
    
    print()
    print("問題の根本原因:")
    print("1. M+フォントから取得したグリフが日本語処理パスを通る")
    print("2. JP_REDUCTION_MAT, JP_REDUCTION_FIX_MAT_NOHEIGHTによる変換")
    print("3. 変換後の幅が700を超えて誤判定される")
    print()
    
    mplus_font.close()
    yasashisa_font.close()
    utatane_font.close()

if __name__ == '__main__':
    investigate_yasashisa_gothic_influence()