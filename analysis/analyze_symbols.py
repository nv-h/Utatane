#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge

def analyze_symbol_widths():
    """記号類（○△②×✕等）の文字幅をM+と比較分析"""
    
    mplus_path = './sourceFonts/mplus-1m-regular.ttf'
    ubuntu_path = './sourceFonts/UbuntuMono-Regular_modify.ttf'
    yasashisa_path = './sourceFonts/YasashisaGothicBold-V2_-30.ttf'
    
    try:
        mplus_font = fontforge.open(mplus_path)
        ubuntu_font = fontforge.open(ubuntu_path)
        yasashisa_font = fontforge.open(yasashisa_path)
    except Exception as e:
        print(f"フォントを開けませんでした: {e}")
        return
    
    print("記号類の文字幅分析（描画ずれ調査）")
    print("=" * 70)
    
    # 問題となりやすい記号類を定義
    symbol_categories = {
        "幾何図形": [
            0x25CB,  # ○ WHITE CIRCLE
            0x25CF,  # ● BLACK CIRCLE
            0x25B3,  # △ WHITE UP-POINTING TRIANGLE
            0x25B2,  # ▲ BLACK UP-POINTING TRIANGLE
            0x25A1,  # □ WHITE SQUARE
            0x25A0,  # ■ BLACK SQUARE
            0x25C7,  # ◇ WHITE DIAMOND
            0x25C6,  # ◆ BLACK DIAMOND
        ],
        "囲み数字": [
            0x2460,  # ① CIRCLED DIGIT ONE
            0x2461,  # ② CIRCLED DIGIT TWO
            0x2462,  # ③ CIRCLED DIGIT THREE
            0x2463,  # ④ CIRCLED DIGIT FOUR
            0x2464,  # ⑤ CIRCLED DIGIT FIVE
            0x2468,  # ⑨ CIRCLED DIGIT NINE
            0x2469,  # ⑩ CIRCLED DIGIT TEN
        ],
        "演算記号・×類": [
            0x00D7,  # × MULTIPLICATION SIGN
            0x2715,  # ✕ MULTIPLICATION X
            0x00F7,  # ÷ DIVISION SIGN
            0x00B1,  # ± PLUS-MINUS SIGN
            0x2212,  # − MINUS SIGN
            0x2213,  # ∓ MINUS-OR-PLUS SIGN
        ],
        "チェック・星印": [
            0x2713,  # ✓ CHECK MARK
            0x2714,  # ✔ HEAVY CHECK MARK
            0x2717,  # ✗ BALLOT X
            0x2718,  # ✘ HEAVY BALLOT X
            0x2605,  # ★ BLACK STAR
            0x2606,  # ☆ WHITE STAR
        ],
        "矢印": [
            0x2190,  # ← LEFTWARDS ARROW
            0x2191,  # ↑ UPWARDS ARROW
            0x2192,  # → RIGHTWARDS ARROW
            0x2193,  # ↓ DOWNWARDS ARROW
            0x21D0,  # ⇐ LEFTWARDS DOUBLE ARROW
            0x21D2,  # ⇒ RIGHTWARDS DOUBLE ARROW
        ],
        "その他記号": [
            0x203B,  # ※ REFERENCE MARK
            0x3012,  # 〒 POSTAL MARK
            0x3013,  # 〓 GETA MARK
            0x301C,  # 〜 WAVE DASH
            0xFF5E,  # ～ FULLWIDTH TILDE
            0x2026,  # … HORIZONTAL ELLIPSIS
            0x22EF,  # ⋯ MIDLINE HORIZONTAL ELLIPSIS
        ]
    }
    
    all_mismatches = []
    
    for category, char_codes in symbol_categories.items():
        print(f"\n【{category}】")
        print(f"{'文字':<8} {'コード':<10} {'M+':<8} {'Ubuntu':<8} {'やさしさ':<10} {'状況':<15}")
        print("-" * 70)
        
        category_mismatches = []
        
        for code in char_codes:
            # 各フォントでの存在確認と幅取得
            mplus_info = None
            ubuntu_info = None
            yasashisa_info = None
            
            if code in mplus_font and mplus_font[code].isWorthOutputting:
                mplus_info = mplus_font[code].width
            
            if code in ubuntu_font and ubuntu_font[code].isWorthOutputting:
                ubuntu_info = ubuntu_font[code].width
            
            if code in yasashisa_font and yasashisa_font[code].isWorthOutputting:
                yasashisa_info = yasashisa_font[code].width
            
            # 結果整理
            mplus_str = str(mplus_info) if mplus_info else "なし"
            ubuntu_str = str(ubuntu_info) if ubuntu_info else "なし"
            yasashisa_str = str(yasashisa_info) if yasashisa_info else "なし"
            
            # 状況判定
            status = ""
            fonts_with_char = []
            widths = []
            
            if mplus_info:
                fonts_with_char.append("M+")
                widths.append(mplus_info)
            if ubuntu_info:
                fonts_with_char.append("Ubuntu")
                widths.append(ubuntu_info)
            if yasashisa_info:
                fonts_with_char.append("やさしさ")
                widths.append(yasashisa_info)
            
            if len(set(widths)) > 1:
                status = "⚠️ 幅不統一"
                category_mismatches.append({
                    'code': code,
                    'char': chr(code),
                    'mplus': mplus_info,
                    'ubuntu': ubuntu_info,
                    'yasashisa': yasashisa_info,
                    'fonts': fonts_with_char
                })
            elif len(fonts_with_char) == 1:
                status = f"{fonts_with_char[0]}のみ"
            elif len(fonts_with_char) == 0:
                status = "全フォントになし"
            else:
                status = "統一済み"
            
            try:
                char_display = chr(code)
            except:
                char_display = "[表示不可]"
            
            print(f"{char_display:<8} U+{code:04X}   {mplus_str:<8} {ubuntu_str:<8} {yasashisa_str:<10} {status}")
        
        if category_mismatches:
            all_mismatches.extend(category_mismatches)
            print(f"\n  ➤ {category}で{len(category_mismatches)}件の幅不統一を発見")
    
    # 総合結果
    print("\n" + "=" * 70)
    print("【総合結果：幅不統一の記号】")
    
    if all_mismatches:
        print(f"\n合計 {len(all_mismatches)} 件の幅不統一を発見:")
        
        for mismatch in all_mismatches:
            print(f"\nU+{mismatch['code']:04X} '{mismatch['char']}':")
            if mismatch['mplus']:
                print(f"  M+ 1m: {mismatch['mplus']}")
            if mismatch['ubuntu']:
                print(f"  Ubuntu Mono: {mismatch['ubuntu']}")
            if mismatch['yasashisa']:
                print(f"  やさしさゴシック: {mismatch['yasashisa']}")
            print(f"  存在フォント: {', '.join(mismatch['fonts'])}")
    else:
        print("幅不統一の記号は見つかりませんでした。")
    
    mplus_font.close()
    ubuntu_font.close()
    yasashisa_font.close()

if __name__ == '__main__':
    analyze_symbol_widths()