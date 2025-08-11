#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge
import sys

def accurate_width_transformation_analysis():
    """正確なJP_REDUCTION_MAT変換による幅変化の分析"""
    
    # utatane.pyの実際の値を使用
    LATIN_ASCENT = 800
    JP_ASCENT = 880
    JP_A_RAT = LATIN_ASCENT / JP_ASCENT  # 800/880 = 0.9090909...
    WIDTH = 1000
    
    yasashisa_path = './sourceFonts/YasashisaGothicBold-V2.ttf'
    mplus_path = './sourceFonts/mplus-1m-regular.ttf'
    
    try:
        yasashisa_font = fontforge.open(yasashisa_path)
        mplus_font = fontforge.open(mplus_path)
    except Exception as e:
        print(f"フォントを開けませんでした: {e}")
        return
    
    print("正確な幅変換分析")
    print("=" * 80)
    print(f"JP_A_RAT = {LATIN_ASCENT}/{JP_ASCENT} = {JP_A_RAT:.6f}")
    print(f"閾値 = WIDTH * 0.7 = {WIDTH * 0.7}")
    print()
    
    # 問題グリフのサンプル
    problem_glyphs = [
        (0x025D, "ɝ", "IPA"),
        (0x026F, "ɯ", "IPA"), 
        (0x0271, "ɱ", "IPA"),
        (0x03D2, "ϒ", "ギリシャ"),
        (0x03D6, "ϖ", "ギリシャ"),
        (0x2400, "␀", "制御図"),
        (0x240A, "␊", "制御図"),
        (0x20A8, "₨", "通貨"),
        (0x20A9, "₩", "通貨"),
        (0x2225, "∥", "数学"),
        (0x1E3E, "Ḿ", "拡張ラテン"),
    ]
    
    print("| Unicode | 文字 | 分類 | M+幅 | やさしさ幅 | 縮小後推定幅 | >700? | 最終判定 |")
    print("|---------|------|------|------|------------|-------------|-------|----------|")
    
    for code, char, category in problem_glyphs:
        mplus_width = None
        yasashisa_width = None
        
        if code in mplus_font and mplus_font[code].isWorthOutputting:
            mplus_width = mplus_font[code].width
        
        if code in yasashisa_font and yasashisa_font[code].isWorthOutputting:
            yasashisa_width = yasashisa_font[code].width
        
        # JP_REDUCTION_MATによる変換
        # transform(scale)は幅も同じ比率で縮小される
        if yasashisa_width:
            estimated_width_after_reduction = yasashisa_width * JP_A_RAT
            exceeds_threshold = estimated_width_after_reduction > 700
            final_width = WIDTH if exceeds_threshold else WIDTH // 2
        else:
            estimated_width_after_reduction = "N/A"
            exceeds_threshold = "N/A"
            final_width = "N/A"
        
        estimated_str = f"{estimated_width_after_reduction:.0f}" if isinstance(estimated_width_after_reduction, float) else str(estimated_width_after_reduction)
        threshold_str = "Yes" if exceeds_threshold else "No" if isinstance(exceeds_threshold, bool) else str(exceeds_threshold)
        print(f"| U+{code:04X} | {char} | {category} | {mplus_width} | {yasashisa_width} | {estimated_str} | {threshold_str} | {final_width} |")
    
    print()
    print("【重要な発見】")
    print()
    print("✓ **やさしさゴシックの幅がJP_REDUCTION_MATで縮小される**")
    print(f"✓ **縮小比率: {JP_A_RAT:.3f} (約90.9%)**")
    print("✓ **縮小後でも多くのグリフが700を超えている**")
    print()
    
    # 具体的な計算例
    print("【具体例】")
    example_glyphs = [
        (0x025D, "ɝ", 804),
        (0x2400, "␀", 1000),
        (0x20A9, "₩", 1051)
    ]
    
    for code, char, original_width in example_glyphs:
        reduced_width = original_width * JP_A_RAT
        print(f"{char} (U+{code:04X}):")
        print(f"  やさしさゴシック幅: {original_width}")
        print(f"  縮小後幅: {original_width} × {JP_A_RAT:.3f} = {reduced_width:.1f}")
        print(f"  判定: {reduced_width:.1f} > 700? {'Yes' if reduced_width > 700 else 'No'}")
        print(f"  結果: {'全角(1000)' if reduced_width > 700 else '半角(500)'}")
        print()
    
    print("【なぜM+で500なのにUtataneで1000になるのか？】")
    print()
    print("1. **フォント合成の順序**:")
    print("   - やさしさゴシックを先に読み込み")
    print("   - M+フォントの罫線・ブロック要素を後から上書き")
    print("   - IPA・ギリシャ・制御図記号等は上書きされない")
    print()
    print("2. **処理パスの問題**:")
    print("   - これらのグリフは特別な分類に該当しない")
    print("   - `else`句でやさしさゴシック由来として処理される")
    print("   - M+では500幅だがやさしさゴシックでは800-1000幅")
    print()
    print("3. **判定ロジックの結果**:")
    print("   - やさしさゴシック幅を90.9%縮小")
    print("   - それでも700を超えるため全角判定")
    print("   - 本来のM+幅(500)とは無関係に判定される")
    print()
    
    print("【解決策】")
    print()
    print("これらのグリフは**M+フォントの幅を基準にすべき**:")
    print("- M+で500 → Utataneで500 (半角維持)")
    print("- やさしさゴシックの幅情報を使わない")
    print("- または、M+専用グリフとして特別扱い")
    
    yasashisa_font.close()
    mplus_font.close()

if __name__ == '__main__':
    accurate_width_transformation_analysis()