#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge

def check_current_utatane_widths():
    """現在のUtataneフォントの文字幅をM+と比較チェック"""
    
    # 既存のUtataneフォントがあるかチェック
    utatane_path = './dist/Utatane-Regular.ttf'
    mplus_path = './sourceFonts/mplus-1m-regular.ttf'
    
    try:
        utatane_font = fontforge.open(utatane_path)
        mplus_font = fontforge.open(mplus_path)
    except Exception as e:
        print(f"フォントを開けませんでした: {e}")
        print("先にUtataneフォントを生成してください")
        return
    
    print("Utatane vs M+ 1m 文字幅比較")
    print("=" * 50)
    
    # 問題のありそうな文字範囲をチェック
    check_ranges = {
        "罫線素片": list(range(0x2500, 0x2510)),  # 最初の16文字
        "ブロック要素": list(range(0x2580, 0x2590)),  # 最初の16文字
        "記号": [0x00A6, 0x00B1, 0x2010, 0x2013, 0x2014, 0x2015],
    }
    
    mismatches = []
    
    for range_name, char_codes in check_ranges.items():
        print(f"\n【{range_name}】")
        
        for code in char_codes:
            utatane_width = None
            mplus_width = None
            
            if code in utatane_font:
                utatane_glyph = utatane_font[code]
                if utatane_glyph.isWorthOutputting:
                    utatane_width = utatane_glyph.width
            
            if code in mplus_font:
                mplus_glyph = mplus_font[code]
                if mplus_glyph.isWorthOutputting:
                    mplus_width = mplus_glyph.width
            
            if utatane_width is not None and mplus_width is not None:
                match = "✓" if utatane_width == mplus_width else "✗"
                print(f"  U+{code:04X} '{chr(code)}': Utatane={utatane_width}, M+={mplus_width} {match}")
                
                if utatane_width != mplus_width:
                    mismatches.append({
                        'code': code,
                        'char': chr(code),
                        'utatane': utatane_width,
                        'mplus': mplus_width
                    })
    
    print("\n" + "=" * 50)
    print(f"不整合発見: {len(mismatches)}件")
    
    if mismatches:
        print("\n【修正が必要な文字】")
        for m in mismatches:
            print(f"  U+{m['code']:04X} '{m['char']}': {m['utatane']} → {m['mplus']} に修正")
    
    utatane_font.close()
    mplus_font.close()

if __name__ == '__main__':
    check_current_utatane_widths()