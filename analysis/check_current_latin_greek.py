#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge

def check_current_latin_greek():
    """現在のUtataneでのラテン文字・ギリシャ文字の処理状況を確認"""
    
    try:
        utatane_path = './dist/Utatane-Regular.ttf'
        mplus_path = './sourceFonts/mplus-1m-regular.ttf'
        
        utatane_font = fontforge.open(utatane_path)
        mplus_font = fontforge.open(mplus_path)
    except Exception as e:
        print(f"フォントを開けませんでした: {e}")
        return
    
    print("現在のUtataneでのラテン文字・ギリシャ文字処理確認")
    print("=" * 60)
    
    # テスト対象文字
    test_ranges = {
        "基本ラテン文字": [0x00C0, 0x00C1, 0x00C7, 0x00C9, 0x00D1, 0x00F1, 0x00FC],  # À Á Ç É Ñ ñ ü
        "拡張ラテン文字A": [0x0100, 0x0101, 0x0106, 0x0107, 0x010C, 0x010D],        # Ā ā Ć ć Č č
        "ギリシャ文字": [0x0391, 0x0392, 0x0393, 0x03B1, 0x03B2, 0x03B3],          # Α Β Γ α β γ
        "キリル文字": [0x0410, 0x0411, 0x0430, 0x0431],                            # А Б а б
    }
    
    total_mplus_only = 0
    
    for range_name, char_codes in test_ranges.items():
        print(f"\n【{range_name}】")
        
        for code in char_codes:
            utatane_present = code in utatane_font and utatane_font[code].isWorthOutputting
            mplus_present = code in mplus_font and mplus_font[code].isWorthOutputting
            
            status = ""
            if utatane_present and mplus_present:
                u_width = utatane_font[code].width
                m_width = mplus_font[code].width
                status = f"両方あり (Utatane:{u_width}, M+:{m_width})"
            elif utatane_present and not mplus_present:
                u_width = utatane_font[code].width
                status = f"Utataneのみ (幅:{u_width})"
            elif not utatane_present and mplus_present:
                m_width = mplus_font[code].width
                status = f"M+のみ (幅:{m_width}) ⚠️"
                total_mplus_only += 1
            else:
                status = "どちらにもなし"
            
            try:
                print(f"  U+{code:04X} '{chr(code)}': {status}")
            except:
                print(f"  U+{code:04X} [表示不可]: {status}")
    
    # M+にあってUtataneにない文字の範囲を調査
    print(f"\n=" * 60)
    print("【M+にあってUtataneにない文字の詳細調査】")
    
    important_ranges = [
        (0x0080, 0x00FF, "基本ラテン文字"),
        (0x0100, 0x017F, "拡張ラテン文字A"),
        (0x0180, 0x024F, "拡張ラテン文字B"),
        (0x0370, 0x03FF, "ギリシャ文字"),
        (0x0400, 0x04FF, "キリル文字"),
    ]
    
    for start, end, name in important_ranges:
        mplus_only_count = 0
        sample_chars = []
        
        for code in range(start, end + 1):
            utatane_present = code in utatane_font and utatane_font[code].isWorthOutputting
            mplus_present = code in mplus_font and mplus_font[code].isWorthOutputting
            
            if mplus_present and not utatane_present:
                mplus_only_count += 1
                if len(sample_chars) < 5:  # 最初の5文字をサンプルとして保存
                    sample_chars.append((code, mplus_font[code].width))
        
        if mplus_only_count > 0:
            print(f"\n{name}: M+のみに{mplus_only_count}文字存在")
            print("  サンプル:")
            for code, width in sample_chars:
                try:
                    print(f"    U+{code:04X} '{chr(code)}' (幅:{width})")
                except:
                    print(f"    U+{code:04X} [表示不可] (幅:{width})")
    
    utatane_font.close()
    mplus_font.close()

if __name__ == '__main__':
    check_current_latin_greek()