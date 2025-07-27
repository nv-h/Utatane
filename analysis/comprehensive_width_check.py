#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge
import sys

def comprehensive_width_check():
    """M+ 1mとUtataneの全グリフ幅の包括的な一致確認"""
    
    mplus_path = './sourceFonts/mplus-1m-regular.ttf'
    utatane_path = './dist/Utatane-Regular.ttf'
    
    try:
        mplus_font = fontforge.open(mplus_path)
        utatane_font = fontforge.open(utatane_path)
    except Exception as e:
        print(f"フォントを開けませんでした: {e}")
        return
    
    print("M+ 1m vs Utatane 全グリフ幅比較")
    print("=" * 80)
    print(f"M+ 1m: {mplus_path}")
    print(f"Utatane: {utatane_path}")
    print()
    
    # 両方に存在するグリフを特定
    common_glyphs = []
    mplus_glyphs = set()
    utatane_glyphs = set()
    
    # M+のグリフ一覧を取得
    for glyph in mplus_font.glyphs():
        if glyph.isWorthOutputting and glyph.encoding >= 0:
            mplus_glyphs.add(glyph.encoding)
    
    # Utataneのグリフ一覧を取得
    for glyph in utatane_font.glyphs():
        if glyph.isWorthOutputting and glyph.encoding >= 0:
            utatane_glyphs.add(glyph.encoding)
    
    # 共通のグリフを特定
    common_codes = mplus_glyphs & utatane_glyphs
    
    print(f"M+のグリフ数: {len(mplus_glyphs)}")
    print(f"Utataneのグリフ数: {len(utatane_glyphs)}")
    print(f"共通グリフ数: {len(common_codes)}")
    print()
    
    # 幅比較を実行
    matches = []
    mismatches = []
    
    for code in sorted(common_codes):
        mplus_width = mplus_font[code].width
        utatane_width = utatane_font[code].width
        
        glyph_info = {
            'code': code,
            'mplus_width': mplus_width,
            'utatane_width': utatane_width,
            'char': chr(code) if code < 0x10000 else f"[U+{code:04X}]"
        }
        
        if mplus_width == utatane_width:
            matches.append(glyph_info)
        else:
            mismatches.append(glyph_info)
    
    # 結果サマリー
    total_common = len(common_codes)
    match_count = len(matches)
    mismatch_count = len(mismatches)
    match_rate = (match_count / total_common * 100) if total_common > 0 else 0
    
    print("【結果サマリー】")
    print(f"一致: {match_count}/{total_common} ({match_rate:.1f}%)")
    print(f"不一致: {mismatch_count}/{total_common} ({100-match_rate:.1f}%)")
    print()
    
    if mismatch_count == 0:
        print("🎉 素晴らしい！全てのグリフの幅が一致しています！")
        mplus_font.close()
        utatane_font.close()
        return
    
    # 不一致グリフの詳細分析
    print("【幅不一致グリフの詳細】")
    print(f"{'文字':<8} {'コード':<12} {'M+幅':<8} {'Utatane幅':<12} {'差分':<8} {'文字名'}")
    print("-" * 80)
    
    # Unicode範囲別に分類
    range_categories = {
        "ASCII制御": (0x0000, 0x001F),
        "ASCII": (0x0020, 0x007F),
        "基本ラテン拡張": (0x0080, 0x00FF),
        "拡張ラテンA": (0x0100, 0x017F),
        "拡張ラテンB": (0x0180, 0x024F),
        "IPA": (0x0250, 0x02AF),
        "修飾文字": (0x02B0, 0x02FF),
        "結合文字": (0x0300, 0x036F),
        "ギリシャ": (0x0370, 0x03FF),
        "キリル": (0x0400, 0x04FF),
        "一般句読点": (0x2000, 0x206F),
        "上付下付": (0x2070, 0x209F),
        "通貨": (0x20A0, 0x20CF),
        "結合記号": (0x20D0, 0x20FF),
        "文字様記号": (0x2100, 0x214F),
        "数学演算子": (0x2200, 0x22FF),
        "その他技術": (0x2300, 0x23FF),
        "制御図": (0x2400, 0x243F),
        "OCR": (0x2440, 0x245F),
        "囲み英数": (0x2460, 0x24FF),
        "罫線": (0x2500, 0x257F),
        "ブロック要素": (0x2580, 0x259F),
        "幾何図形": (0x25A0, 0x25FF),
        "その他記号": (0x2600, 0x26FF),
        "装飾記号": (0x2700, 0x27BF),
        "矢印": (0x2190, 0x21FF),
        "CJK記号": (0x3000, 0x303F),
        "ひらがな": (0x3040, 0x309F),
        "カタカナ": (0x30A0, 0x30FF),
        "CJK統合漢字": (0x4E00, 0x9FFF),
        "半角カタカナ": (0xFF00, 0xFFEF),
    }
    
    # 範囲別に不一致をカウント
    range_mismatches = {}
    for category, (start, end) in range_categories.items():
        range_mismatches[category] = []
    
    for mismatch in mismatches:
        code = mismatch['code']
        char_display = mismatch['char']
        
        # 表示可能な文字かチェック
        try:
            if code < 0x10000:
                char_display = chr(code)
            else:
                char_display = f"[U+{code:04X}]"
        except:
            char_display = "[表示不可]"
        
        diff = mismatch['utatane_width'] - mismatch['mplus_width']
        
        # Unicode文字名を取得（簡易版）
        char_name = "UNKNOWN"
        try:
            import unicodedata
            if code < 0x10000:
                char_name = unicodedata.name(chr(code), "UNKNOWN")
        except:
            pass
        
        print(f"{char_display:<8} U+{code:04X}     {mismatch['mplus_width']:<8} {mismatch['utatane_width']:<12} {diff:+4d}     {char_name}")
        
        # 範囲別分類
        categorized = False
        for category, (start, end) in range_categories.items():
            if start <= code <= end:
                range_mismatches[category].append(mismatch)
                categorized = True
                break
        
        if not categorized:
            if "その他" not in range_mismatches:
                range_mismatches["その他"] = []
            range_mismatches["その他"].append(mismatch)
    
    # 範囲別サマリー
    print(f"\n{'='*80}")
    print("【Unicode範囲別の不一致サマリー】")
    for category, mismatches_in_range in range_mismatches.items():
        if mismatches_in_range:
            print(f"{category}: {len(mismatches_in_range)}件")
            
            # 各範囲の詳細（最初の5件のみ表示）
            if len(mismatches_in_range) <= 5:
                for m in mismatches_in_range:
                    diff = m['utatane_width'] - m['mplus_width']
                    print(f"  U+{m['code']:04X} {m['char']} : {m['mplus_width']} → {m['utatane_width']} ({diff:+d})")
            else:
                for m in mismatches_in_range[:3]:
                    diff = m['utatane_width'] - m['mplus_width']
                    print(f"  U+{m['code']:04X} {m['char']} : {m['mplus_width']} → {m['utatane_width']} ({diff:+d})")
                print(f"  ... 他{len(mismatches_in_range)-3}件")
            print()
    
    mplus_font.close()
    utatane_font.close()

if __name__ == '__main__':
    comprehensive_width_check()