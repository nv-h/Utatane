#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge
import sys

def trace_processing_path():
    """問題グリフがどの処理パスを通るかを詳細分析"""
    
    # utatane.pyで定義されている定数を再現
    HALFWIDTH_CJK_KANA = set(range(0xFF61, 0xFF9F + 1))
    ROMAN_NUMERALS = {0x2160, 0x2161, 0x2162, 0x2163, 0x2164, 0x2165, 0x2166, 0x2167, 0x2168, 0x2169, 0x216A, 0x216B}
    SPECIAL_PUNCTUATION = {0x2010, 0x2015}  # 簡略版
    FULLWIDTH_CODES = set(range(0x3000, 0x9FFF + 1)) | set(range(0xFF01, 0xFF60 + 1))  # 簡略版
    RULED_LINES = set(range(0x2500, 0x257F + 1))
    BLOCK_ELEMENTS = set(range(0x2580, 0x259F + 1))
    
    yasashisa_path = './sourceFonts/YasashisaGothicBold-V2.ttf'
    
    try:
        yasashisa_font = fontforge.open(yasashisa_path)
    except Exception as e:
        print(f"やさしさゴシックフォントを開けませんでした: {e}")
        return
    
    print("問題グリフの処理パス詳細分析")
    print("=" * 80)
    print("各グリフがutatane.pyのどの処理パスを通るかを特定")
    print()
    
    # 問題グリフのサンプル
    problem_glyphs = [
        # IPA音標文字
        (0x025D, "ɝ", "IPA"),
        (0x026F, "ɯ", "IPA"), 
        (0x0271, "ɱ", "IPA"),
        # ギリシャ記号
        (0x03D2, "ϒ", "ギリシャ"),
        (0x03D6, "ϖ", "ギリシャ"),
        # 制御図記号
        (0x2400, "␀", "制御図"),
        (0x240A, "␊", "制御図"),
        (0x240D, "␍", "制御図"),
        # 通貨記号
        (0x20A8, "₨", "通貨"),
        (0x20A9, "₩", "通貨"),
        # 数学演算子
        (0x2225, "∥", "数学"),
        (0x223C, "∼", "数学"),
        # 拡張ラテン
        (0x1E3E, "Ḿ", "拡張ラテン"),
        (0x1ECC, "Ọ", "拡張ラテン"),
    ]
    
    print("| Unicode | 文字 | 分類 | やさしさ幅 | 処理パス | 理由 |")
    print("|---------|------|------|------------|----------|------|")
    
    for code, char, category in problem_glyphs:
        # やさしさゴシックでの幅をチェック
        yasashisa_width = None
        if code in yasashisa_font and yasashisa_font[code].isWorthOutputting:
            yasashisa_width = yasashisa_font[code].width
        
        # どの処理パスを通るかを判定
        processing_path = "UNKNOWN"
        reason = ""
        
        if code in HALFWIDTH_CJK_KANA:
            processing_path = "半角カナ処理"
            reason = "HALFWIDTH_CJK_KANA"
        elif code in ROMAN_NUMERALS:
            processing_path = "ローマ数字処理"  
            reason = "ROMAN_NUMERALS"
        elif code in SPECIAL_PUNCTUATION:
            processing_path = "特定句読点処理"
            reason = "SPECIAL_PUNCTUATION" 
        elif code in FULLWIDTH_CODES:
            processing_path = "全角文字処理"
            reason = "FULLWIDTH_CODES"
        elif code in RULED_LINES:
            processing_path = "罫線処理"
            reason = "RULED_LINES"
        elif code in BLOCK_ELEMENTS:
            processing_path = "ブロック要素処理"
            reason = "BLOCK_ELEMENTS"
        else:
            processing_path = "**else句（問題箇所）**"
            reason = "どの分類にも該当せず"
        
        print(f"| U+{code:04X} | {char} | {category} | {yasashisa_width} | {processing_path} | {reason} |")
    
    print()
    print("【重要な発見】")
    print()
    print("✓ **全ての問題グリフが`else`句を通っている**")
    print("✓ `else`句では以下の処理が実行される:")
    print("  1. `g.transform(JP_REDUCTION_MAT)` - やさしさゴシック用の縮小処理")
    print("  2. `g.transform(JP_REDUCTION_FIX_MAT_NOHEIGHT)` - 位置補正")
    print("  3. `if g.width > WIDTH * 0.7:` - 変換後の幅で判定")
    print()
    
    print("【問題の根本原因】")
    print()
    print("1. **処理対象の誤り**: M+フォント由来のグリフなのに日本語処理を受ける")
    print("2. **やさしさゴシックの影響**: やさしさゴシックの幅情報で縮小処理が実行される")
    print("3. **判定ロジックの後付け**: 縮小処理後に幅判定するため、元の意図と異なる結果")
    print()
    
    # やさしさゴシックの典型的幅パターンを分析
    print("【やさしさゴシックの幅パターン】")
    print()
    
    yasashisa_widths = []
    for code, char, category in problem_glyphs:
        if code in yasashisa_font and yasashisa_font[code].isWorthOutputting:
            yasashisa_widths.append(yasashisa_font[code].width)
    
    if yasashisa_widths:
        print(f"やさしさゴシックの幅範囲: {min(yasashisa_widths)} - {max(yasashisa_widths)}")
        print(f"平均幅: {sum(yasashisa_widths) // len(yasashisa_widths)}")
        print()
        
        # JP_REDUCTION_MATによる縮小後の推定幅
        # 通常、JP_A_RATで縮小される（0.75程度と推定）
        JP_A_RAT = 0.75  # 推定値
        
        print("推定縮小後幅（JP_REDUCTION_MAT適用後）:")
        for code, char, category in problem_glyphs[:5]:  # 最初の5件
            if code in yasashisa_font and yasashisa_font[code].isWorthOutputting:
                original_width = yasashisa_font[code].width
                estimated_width = original_width * JP_A_RAT
                exceeds_threshold = estimated_width > 700
                print(f"  {char}: {original_width} → {estimated_width:.0f} {'(>700 ✓)' if exceeds_threshold else '(≤700)'}")
        print()
    
    print("【解決策の方向性】")
    print()
    print("1. **M+専用グリフの除外**: 問題グリフをelse句から除外")
    print("2. **判定基準の変更**: やさしさゴシック由来かM+由来かで判定を分離") 
    print("3. **処理順序の見直し**: 幅判定を縮小処理前に実行")
    print()
    
    yasashisa_font.close()

if __name__ == '__main__':
    trace_processing_path()