#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge
import sys

def analyze_mplus_widths():
    """M+ 1m regular フォントの文字幅を詳細に分析する"""
    
    font_path = './sourceFonts/mplus-1m-regular.ttf'
    try:
        font = fontforge.open(font_path)
    except Exception as e:
        print(f"フォントを開けませんでした: {e}")
        return
    
    print(f"M+ 1m Regular フォント分析: {font_path}")
    print(f"Em square: {font.em}")
    print(f"Ascent: {font.ascent}, Descent: {font.descent}")
    print("=" * 60)
    
    # 分析対象の文字範囲を定義
    ranges = {
        "ASCII": list(range(0x0020, 0x007F+1)),
        "ひらがな": list(range(0x3040, 0x309F+1)),
        "カタカナ": list(range(0x30A0, 0x30FF+1)),
        "漢字CJK": list(range(0x4E00, 0x4E00+100)),  # 最初の100文字のみ
        "半角カタカナ": list(range(0xFF61, 0xFF9F+1)),
        "罫線素片": list(range(0x2500, 0x257F+1)),
        "ブロック要素": list(range(0x2580, 0x259F+1)),
        "記号": [0x00A0, 0x00A6, 0x00B1, 0x00B6, 0x00D7, 0x00F7, 0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2016, 0x2017, 0x2018, 0x2019],
    }
    
    width_stats = {}
    
    for range_name, char_codes in ranges.items():
        widths = []
        present_chars = []
        
        for code in char_codes:
            if code in font:
                glyph = font[code]
                if glyph.isWorthOutputting:
                    widths.append(glyph.width)
                    present_chars.append((code, chr(code), glyph.width))
        
        if widths:
            width_stats[range_name] = {
                'count': len(widths),
                'min_width': min(widths),
                'max_width': max(widths),
                'avg_width': sum(widths) / len(widths),
                'unique_widths': list(set(widths)),
                'sample_chars': present_chars[:10]  # 最初の10文字
            }
    
    # 結果出力
    for range_name, stats in width_stats.items():
        print(f"\n【{range_name}】")
        print(f"  文字数: {stats['count']}")
        print(f"  幅の範囲: {stats['min_width']} - {stats['max_width']}")
        print(f"  平均幅: {stats['avg_width']:.1f}")
        print(f"  固有の幅: {stats['unique_widths']}")
        print(f"  サンプル文字:")
        for code, char, width in stats['sample_chars']:
            try:
                print(f"    U+{code:04X} '{char}' width={width}")
            except:
                print(f"    U+{code:04X} [表示不可] width={width}")
    
    # 全角/半角の基準を特定
    print("\n" + "=" * 60)
    print("【全角/半角基準の推定】")
    
    if 'ASCII' in width_stats and 'ひらがな' in width_stats:
        ascii_width = width_stats['ASCII']['unique_widths'][0] if len(width_stats['ASCII']['unique_widths']) == 1 else None
        hiragana_width = width_stats['ひらがな']['unique_widths'][0] if len(width_stats['ひらがな']['unique_widths']) == 1 else None
        
        print(f"ASCII文字幅: {ascii_width}")
        print(f"ひらがな文字幅: {hiragana_width}")
        
        if ascii_width and hiragana_width:
            ratio = hiragana_width / ascii_width
            print(f"全角/半角比率: {ratio:.3f}")
            print(f"推定半角幅: {ascii_width}")
            print(f"推定全角幅: {hiragana_width}")
    
    font.close()

if __name__ == '__main__':
    analyze_mplus_widths()