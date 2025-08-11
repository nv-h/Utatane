#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge
import sys

def analyze_judgment_logic_side_effects():
    """判定ロジック副作用（184件）の詳細分析"""
    
    mplus_path = './sourceFonts/mplus-1m-regular.ttf'
    utatane_path = './dist/Utatane-Regular.ttf'
    
    try:
        mplus_font = fontforge.open(mplus_path)
        utatane_font = fontforge.open(utatane_path)
    except Exception as e:
        print(f"フォントを開けませんでした: {e}")
        return
    
    print("判定ロジック副作用（184件）の詳細分析")
    print("=" * 80)
    print("判定基準: g.width > WIDTH * 0.7 (700) による誤判定の分析")
    print()
    
    # 判定ロジックの副作用に該当するグリフを特定
    # 1. 制御図記号の全角化（37件）: U+2400-U+243F
    # 2. その他の記号類（147件）
    
    # 影響を受けるUnicode範囲を定義
    affected_ranges = {
        "制御図記号": (0x2400, 0x243F),  # 37件
        "IPA音標文字": (0x0250, 0x02AF),  # 14件
        "ギリシャ記号": (0x03D0, 0x03FF),  # 8件  
        "通貨記号": (0x20A0, 0x20CF),     # 7件
        "数学演算子": (0x2200, 0x22FF),   # 一部
        "一般句読点": (0x2000, 0x206F),   # 一部
        "文字様記号": (0x2100, 0x214F),   # 一部
        "その他技術": (0x2300, 0x23FF),   # 一部
        "拡張ラテン文字": (0x1E00, 0x1EFF), # 118件（複数範囲）
        "合字": (0xFB00, 0xFB4F),        # 一部
    }
    
    # 判定ロジック副作用のパターン
    # パターン1: M+で500（半角）→ Utataneで1000（全角） [誤って全角化]
    # パターン2: M+で1000（全角）→ Utataneで500（半角） [意図的半角化：罫線等]
    
    side_effect_glyphs = {
        "誤全角化": [],  # M+ 500 → Utatane 1000 の誤判定
        "意図半角化": []  # M+ 1000 → Utatane 500 の意図的変更
    }
    
    # 共通グリフを取得
    common_codes = set()
    for glyph in mplus_font.glyphs():
        if glyph.isWorthOutputting and glyph.encoding >= 0:
            if glyph.encoding in utatane_font:
                if utatane_font[glyph.encoding].isWorthOutputting:
                    common_codes.add(glyph.encoding)
    
    for code in sorted(common_codes):
        mplus_width = mplus_font[code].width
        utatane_width = utatane_font[code].width
        
        if mplus_width != utatane_width:
            char_display = "?"
            char_name = "UNKNOWN"
            try:
                if code < 0x10000:
                    char_display = chr(code)
                    import unicodedata
                    char_name = unicodedata.name(chr(code), "UNKNOWN")
                else:
                    char_display = f"[U+{code:04X}]"
            except:
                char_display = "[表示不可]"
            
            glyph_info = {
                'code': code,
                'char': char_display,
                'name': char_name,
                'mplus_width': mplus_width,
                'utatane_width': utatane_width,
                'diff': utatane_width - mplus_width
            }
            
            # パターン分類
            if mplus_width == 500 and utatane_width == 1000:
                # 誤って全角化されたケース
                side_effect_glyphs["誤全角化"].append(glyph_info)
            elif mplus_width == 1000 and utatane_width == 500:
                # 意図的に半角化されたケース（罫線等）
                side_effect_glyphs["意図半角化"].append(glyph_info)
    
    # 結果出力
    print(f"【判定ロジック副作用の分類】")
    print()
    
    # 誤全角化されたグリフの分析
    false_fullwidth = side_effect_glyphs["誤全角化"]
    print(f"■ 誤全角化パターン（M+ 500 → Utatane 1000）: {len(false_fullwidth)}件")
    print("原因: `g.width > WIDTH * 0.7` の判定で500を半角と判定できず全角化")
    print()
    
    # Unicode範囲別に分類
    range_count = {}
    for range_name, (start, end) in affected_ranges.items():
        if isinstance((start, end), tuple):
            count = sum(1 for g in false_fullwidth if start <= g['code'] <= end)
            if count > 0:
                range_count[range_name] = count
    
    print("Unicode範囲別の誤全角化件数:")
    for range_name, count in sorted(range_count.items(), key=lambda x: -x[1]):
        print(f"  {range_name}: {count}件")
    print()
    
    # 詳細リスト（制御図記号とIPA音標文字）
    print("■ 制御図記号の誤全角化（詳細）:")
    control_symbols = [g for g in false_fullwidth if 0x2400 <= g['code'] <= 0x243F]
    for g in control_symbols[:10]:  # 最初の10件
        print(f"  U+{g['code']:04X} {g['char']} : {g['name']}")
    if len(control_symbols) > 10:
        print(f"  ... 他{len(control_symbols)-10}件")
    print()
    
    print("■ IPA音標文字の誤全角化（詳細）:")
    ipa_symbols = [g for g in false_fullwidth if 0x0250 <= g['code'] <= 0x02AF]
    for g in ipa_symbols:  # 全件表示
        print(f"  U+{g['code']:04X} {g['char']} : {g['name']}")
    print()
    
    # 意図的半角化（罫線等）
    intentional_halfwidth = side_effect_glyphs["意図半角化"]
    print(f"■ 意図的半角化パターン（M+ 1000 → Utatane 500）: {len(intentional_halfwidth)}件")
    print("理由: DataFrame表示最適化のための罫線・句読点の半角化")
    print()
    
    # 罫線の詳細
    box_drawing = [g for g in intentional_halfwidth if 0x2500 <= g['code'] <= 0x257F]
    print(f"  罫線文字（U+2500-U+257F）: {len(box_drawing)}件")
    
    # その他の意図的半角化
    other_intentional = [g for g in intentional_halfwidth if not (0x2500 <= g['code'] <= 0x257F)]
    print(f"  その他（三点リーダー等）: {len(other_intentional)}件")
    for g in other_intentional:
        print(f"    U+{g['code']:04X} {g['char']} : {g['name']}")
    print()
    
    # 総計確認
    total_side_effects = len(false_fullwidth) + len(intentional_halfwidth)
    print(f"【総計】")
    print(f"誤全角化: {len(false_fullwidth)}件")
    print(f"意図半角化: {len(intentional_halfwidth)}件") 
    print(f"合計: {total_side_effects}件")
    print()
    
    # 判定ロジックの問題の確認
    print(f"【判定ロジックの検証】")
    print("現在の判定: g.width > 700 の場合に全角（1000）、そうでなければ半角（500）")
    print()
    print("問題のあるケース（M+で500なのにUtataneで1000になったもの）:")
    
    # M+での幅が500のグリフがUtataneで1000になっているケースを確認
    problematic_cases = []
    for code in sorted(common_codes):
        mplus_glyph = mplus_font[code]
        utatane_glyph = utatane_font[code]
        
        # M+で500、Utataneで1000のケース
        if mplus_glyph.width == 500 and utatane_glyph.width == 1000:
            problematic_cases.append({
                'code': code,
                'char': chr(code) if code < 0x10000 else f"[U+{code:04X}]",
                'mplus_width': mplus_glyph.width,
                'original_width': mplus_glyph.width  # M+での元の幅
            })
    
    print(f"判定ロジック副作用による誤全角化: {len(problematic_cases)}件")
    print()
    
    # 実際の判定ロジックの問題を確認
    print("問題の原因:")
    print("1. M+で500のグリフが、合成処理後に700を超える幅になる")
    print("2. その結果、`g.width > 700`の条件でTrueとなり全角化される")
    print("3. 本来は半角（500）のままであるべきグリフが全角（1000）になる")
    print()
    
    mplus_font.close()
    utatane_font.close()

if __name__ == '__main__':
    analyze_judgment_logic_side_effects()