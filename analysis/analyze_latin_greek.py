#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge

def analyze_latin_greek_widths():
    """ラテン文字・ギリシャ文字の文字幅をM+と比較分析"""
    
    mplus_path = './sourceFonts/mplus-1m-regular.ttf'
    ubuntu_path = './sourceFonts/UbuntuMono-Regular_modify.ttf'
    
    try:
        mplus_font = fontforge.open(mplus_path)
        ubuntu_font = fontforge.open(ubuntu_path)
    except Exception as e:
        print(f"フォントを開けませんでした: {e}")
        return
    
    print("ラテン文字・ギリシャ文字の文字幅分析")
    print("=" * 60)
    
    # 分析対象の文字範囲
    ranges = {
        "基本ラテン文字": list(range(0x0080, 0x00FF+1)),  # Latin-1 Supplement
        "拡張ラテン文字A": list(range(0x0100, 0x017F+1)),  # Latin Extended-A
        "拡張ラテン文字B": list(range(0x0180, 0x024F+1)),  # Latin Extended-B
        "ギリシャ文字": list(range(0x0370, 0x03FF+1)),     # Greek and Coptic
        "キリル文字": list(range(0x0400, 0x04FF+1)),       # Cyrillic
    }
    
    print(f"M+ 1m: {mplus_path}")
    print(f"Ubuntu Mono: {ubuntu_path}")
    print()
    
    for range_name, char_codes in ranges.items():
        print(f"【{range_name}】")
        
        mplus_chars = []
        ubuntu_chars = []
        both_present = []
        
        for code in char_codes:
            mplus_present = code in mplus_font and mplus_font[code].isWorthOutputting
            ubuntu_present = code in ubuntu_font and ubuntu_font[code].isWorthOutputting
            
            if mplus_present:
                mplus_width = mplus_font[code].width
                mplus_chars.append((code, chr(code), mplus_width))
            
            if ubuntu_present:
                ubuntu_width = ubuntu_font[code].width
                ubuntu_chars.append((code, chr(code), ubuntu_width))
            
            if mplus_present and ubuntu_present:
                both_present.append({
                    'code': code,
                    'char': chr(code),
                    'mplus_width': mplus_font[code].width,
                    'ubuntu_width': ubuntu_font[code].width
                })
        
        print(f"  M+に存在: {len(mplus_chars)}文字")
        print(f"  Ubuntu Monoに存在: {len(ubuntu_chars)}文字")
        print(f"  両方に存在: {len(both_present)}文字")
        
        if mplus_chars:
            mplus_widths = [c[2] for c in mplus_chars]
            print(f"  M+の幅: {list(set(mplus_widths))}")
        
        if ubuntu_chars:
            ubuntu_widths = [c[2] for c in ubuntu_chars]
            print(f"  Ubuntu Monoの幅: {list(set(ubuntu_widths))}")
        
        # 両方に存在する文字の幅比較
        if both_present:
            width_mismatches = []
            for char_info in both_present[:10]:  # 最初の10文字をサンプル表示
                m_width = char_info['mplus_width']
                u_width = char_info['ubuntu_width']
                match = "✓" if m_width == u_width else "✗"
                
                try:
                    print(f"    U+{char_info['code']:04X} '{char_info['char']}': M+={m_width}, Ubuntu={u_width} {match}")
                except:
                    print(f"    U+{char_info['code']:04X} [表示不可]: M+={m_width}, Ubuntu={u_width} {match}")
                
                if m_width != u_width:
                    width_mismatches.append(char_info)
            
            if len(both_present) > 10:
                print(f"    ... 他{len(both_present)-10}文字")
            
            mismatch_count = sum(1 for c in both_present if c['mplus_width'] != c['ubuntu_width'])
            if mismatch_count > 0:
                print(f"  ⚠️ 幅の不整合: {mismatch_count}/{len(both_present)}文字")
        
        print()
    
    # M+のみに存在する重要な文字をチェック
    print("【M+のみに存在する可能性のある重要文字】")
    important_chars = [
        0x00A0,  # NO-BREAK SPACE
        0x00A9,  # COPYRIGHT SIGN ©
        0x00AE,  # REGISTERED SIGN ®
        0x2122,  # TRADE MARK SIGN ™
        0x00B0,  # DEGREE SIGN °
        0x00B1,  # PLUS-MINUS SIGN ±
        0x00B5,  # MICRO SIGN µ
        0x00D7,  # MULTIPLICATION SIGN ×
        0x00F7,  # DIVISION SIGN ÷
    ]
    
    for code in important_chars:
        mplus_present = code in mplus_font and mplus_font[code].isWorthOutputting
        ubuntu_present = code in ubuntu_font and ubuntu_font[code].isWorthOutputting
        
        if mplus_present and not ubuntu_present:
            mplus_width = mplus_font[code].width
            try:
                print(f"  U+{code:04X} '{chr(code)}': M+のみ (幅={mplus_width})")
            except:
                print(f"  U+{code:04X} [表示不可]: M+のみ (幅={mplus_width})")
    
    mplus_font.close()
    ubuntu_font.close()

if __name__ == '__main__':
    analyze_latin_greek_widths()