#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge

def check_current_symbol_handling():
    """現在のUtataneでの記号類の処理状況を確認"""
    
    try:
        utatane_path = './dist/Utatane-Regular.ttf'
        mplus_path = './sourceFonts/mplus-1m-regular.ttf'
        
        utatane_font = fontforge.open(utatane_path)
        mplus_font = fontforge.open(mplus_path)
    except Exception as e:
        print(f"フォントを開けませんでした: {e}")
        return
    
    print("現在のUtataneでの記号類処理確認")
    print("=" * 60)
    
    # 問題が発見された記号をチェック
    problem_symbols = [
        (0x00D7, "×", "MULTIPLICATION SIGN"),
        (0x00F7, "÷", "DIVISION SIGN"), 
        (0x00B1, "±", "PLUS-MINUS SIGN"),
        (0x2212, "−", "MINUS SIGN"),
        (0x2191, "↑", "UPWARDS ARROW"),
        (0x2193, "↓", "DOWNWARDS ARROW"),
        (0x2026, "…", "HORIZONTAL ELLIPSIS"),
    ]
    
    # 参考として正常な記号もチェック
    good_symbols = [
        (0x25CB, "○", "WHITE CIRCLE"),
        (0x2461, "②", "CIRCLED DIGIT TWO"),
        (0x2715, "✕", "MULTIPLICATION X"),
        (0x2713, "✓", "CHECK MARK"),
        (0x2192, "→", "RIGHTWARDS ARROW"),
    ]
    
    print("【問題が発見された記号の現在の状況】")
    print(f"{'記号':<6} {'コード':<10} {'Utatane':<10} {'M+基準':<10} {'状況':<15}")
    print("-" * 60)
    
    mismatches = []
    
    for code, char, name in problem_symbols:
        utatane_width = None
        mplus_width = None
        
        if code in utatane_font and utatane_font[code].isWorthOutputting:
            utatane_width = utatane_font[code].width
        
        if code in mplus_font and mplus_font[code].isWorthOutputting:
            mplus_width = mplus_font[code].width
        
        if utatane_width and mplus_width:
            match = "✓" if utatane_width == mplus_width else "✗ 不整合"
            if utatane_width != mplus_width:
                mismatches.append({
                    'code': code,
                    'char': char,
                    'name': name,
                    'utatane': utatane_width,
                    'mplus': mplus_width
                })
        elif utatane_width and not mplus_width:
            match = "Utataneのみ"
        elif not utatane_width and mplus_width:
            match = "M+のみ"
        else:
            match = "どちらにもなし"
        
        u_str = str(utatane_width) if utatane_width else "なし"
        m_str = str(mplus_width) if mplus_width else "なし"
        
        print(f"{char:<6} U+{code:04X}   {u_str:<10} {m_str:<10} {match}")
    
    print(f"\n【参考：正常に処理されている記号】")
    print(f"{'記号':<6} {'コード':<10} {'Utatane':<10} {'M+基準':<10} {'状況':<15}")
    print("-" * 60)
    
    for code, char, name in good_symbols:
        utatane_width = None
        mplus_width = None
        
        if code in utatane_font and utatane_font[code].isWorthOutputting:
            utatane_width = utatane_font[code].width
        
        if code in mplus_font and mplus_font[code].isWorthOutputting:
            mplus_width = mplus_font[code].width
        
        if utatane_width and mplus_width:
            match = "✓" if utatane_width == mplus_width else "✗"
        else:
            match = "一部なし"
        
        u_str = str(utatane_width) if utatane_width else "なし"
        m_str = str(mplus_width) if mplus_width else "なし"
        
        print(f"{char:<6} U+{code:04X}   {u_str:<10} {m_str:<10} {match}")
    
    print(f"\n=" * 60)
    print("【記号類の描画ずれ原因分析】")
    
    if mismatches:
        print(f"\n⚠️ {len(mismatches)}個の記号でM+との幅不整合を確認:")
        for m in mismatches:
            print(f"  {m['char']} (U+{m['code']:04X}): {m['utatane']} → {m['mplus']} に修正必要")
        
        print(f"\n【推定される原因】")
        print("1. やさしさゴシックフォントの文字幅がM+と異なる")
        print("2. Ubuntu Monoの文字幅がM+と異なる場合がある")
        print("3. 現在のUtataneの幅調整ロジックで適切に処理されていない")
        
        print(f"\n【アプリケーションでの描画ずれへの影響】")
        print("- 文字幅が異なると、文字の配置がずれる")
        print("- 特に等幅フォントでは、文字間隔の不整合が目立つ")
        print("- ターミナルやエディタでの表示崩れの原因となる")
        
    else:
        print("記号類の幅は適切に処理されています。")
    
    utatane_font.close()
    mplus_font.close()

if __name__ == '__main__':
    check_current_symbol_handling()