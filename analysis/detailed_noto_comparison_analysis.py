#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge
import sys

def detailed_noto_comparison_analysis():
    """Noto Sans Mono CJK VFとの詳細比較分析（特に問題グリフに焦点）"""
    
    noto_path = './dist/NotoSansMonoCJKjp-VF.ttf'
    utatane_path = './dist/Utatane-Regular.ttf'
    mplus_path = './sourceFonts/mplus-1m-regular.ttf'
    
    try:
        noto_font = fontforge.open(noto_path)
        utatane_font = fontforge.open(utatane_path)
        mplus_font = fontforge.open(mplus_path)
    except Exception as e:
        print(f"フォントを開けませんでした: {e}")
        return
    
    print("Noto Sans Mono CJK VF との詳細比較分析")
    print("=" * 80)
    print("問題グリフ（106件）に焦点を当てた分析")
    print()
    
    # 問題グリフの完全リスト（前回調査の106件）
    problem_glyphs_codes = [
        # IPA音標文字（14件）
        0x025D, 0x026F, 0x0270, 0x0271, 0x0276, 0x0277, 0x028D, 0x0298,
        0x02A3, 0x02A4, 0x02A5, 0x02A6, 0x02A8, 0x02A9,
        # ギリシャ記号（8件） 
        0x03D2, 0x03D3, 0x03D4, 0x03D6, 0x03D8, 0x03DA, 0x03E0, 0x03E1,
        # 制御図記号（37件）
        0x2400, 0x2401, 0x2402, 0x2403, 0x2404, 0x2405, 0x2406, 0x2407, 0x2408, 0x2409,
        0x240A, 0x240B, 0x240C, 0x240D, 0x240E, 0x240F, 0x2410, 0x2411, 0x2412, 0x2413,
        0x2414, 0x2415, 0x2416, 0x2417, 0x2418, 0x2419, 0x241A, 0x241B, 0x241C, 0x241D,
        0x241E, 0x241F, 0x2420, 0x2421, 0x2423, 0x2424, 0x2425,
        # 通貨記号（7件）
        0x20A8, 0x20A9, 0x20AA, 0x20AF, 0x20B0, 0x20B2, 0x20B3,
        # 数学演算子（3件）
        0x2225, 0x2226, 0x223C,
        # 拡張ラテン文字（26件）
        0x1E3E, 0x1E3F, 0x1E40, 0x1E41, 0x1E42, 0x1E43, 0x1E88, 0x1E89,
        0x1ECC, 0x1ECE, 0x1ED0, 0x1ED2, 0x1ED4, 0x1ED6, 0x1ED8, 0x1EDA,
        0x1EDC, 0x1EDE, 0x1EE0, 0x1EE2, 0x1EE8, 0x1EEA, 0x1EEC, 0x1EEE,
        0x1EF0, 0x1EFA,
        # 一般句読点（3件）
        0x203F, 0x2040, 0x2053,
        # 文字様記号（2件）
        0x211E, 0x2127,
        # その他技術記号（1件）
        0x23CE,
        # 合字（3件）
        0xFB00, 0xFB03, 0xFB04
    ]
    
    # 各フォントでの比較データを収集
    comparison_data = []
    
    for code in problem_glyphs_codes:
        # 各フォントでの存在・幅チェック
        noto_exists = code in noto_font and noto_font[code].isWorthOutputting
        utatane_exists = code in utatane_font and utatane_font[code].isWorthOutputting
        mplus_exists = code in mplus_font and mplus_font[code].isWorthOutputting
        
        noto_width = noto_font[code].width if noto_exists else None
        utatane_width = utatane_font[code].width if utatane_exists else None
        mplus_width = mplus_font[code].width if mplus_exists else None
        
        # 文字表示名
        char_display = "?"
        char_name = "UNKNOWN"
        try:
            if code < 0x10000:
                char_display = chr(code)
                import unicodedata
                char_name = unicodedata.name(chr(code), "UNKNOWN")[:40]
            else:
                char_display = f"[U+{code:04X}]"
        except:
            char_display = "[表示不可]"
        
        # Unicode範囲分類
        if 0x0250 <= code <= 0x02AF:
            category = "IPA"
        elif 0x03D0 <= code <= 0x03FF:
            category = "ギリシャ"
        elif 0x1E00 <= code <= 0x1EFF:
            category = "拡張ラテン"
        elif 0x2000 <= code <= 0x206F:
            category = "一般句読点"
        elif 0x20A0 <= code <= 0x20CF:
            category = "通貨"
        elif 0x2100 <= code <= 0x214F:
            category = "文字様"
        elif 0x2200 <= code <= 0x22FF:
            category = "数学"
        elif 0x2300 <= code <= 0x23FF:
            category = "技術"
        elif 0x2400 <= code <= 0x243F:
            category = "制御図"
        elif 0xFB00 <= code <= 0xFB4F:
            category = "合字"
        else:
            category = "その他"
        
        comparison_data.append({
            'code': code,
            'char': char_display,
            'name': char_name,
            'category': category,
            'noto_exists': noto_exists,
            'utatane_exists': utatane_exists,
            'mplus_exists': mplus_exists,
            'noto_width': noto_width,
            'utatane_width': utatane_width,
            'mplus_width': mplus_width
        })
    
    # フィルタリング：3つのフォント全てに存在するもの
    valid_comparisons = [d for d in comparison_data if d['noto_exists'] and d['utatane_exists'] and d['mplus_exists']]
    
    print(f"【比較対象】")
    print(f"問題グリフ総数: {len(problem_glyphs_codes)}件")
    print(f"3フォント共通: {len(valid_comparisons)}件")
    print()
    
    # カテゴリ別分析
    print("【カテゴリ別詳細比較】")
    print()
    
    categories = {}
    for data in valid_comparisons:
        cat = data['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(data)
    
    for category, items in sorted(categories.items()):
        print(f"■ {category}（{len(items)}件）")
        print()
        print("| Unicode | 文字 | M+幅 | Noto幅 | Utatane幅 | M+=Noto? | M+=Utatane? | Noto=Utatane? | 推奨 |")
        print("|---------|------|------|--------|-----------|----------|-------------|---------------|------|")
        
        for item in sorted(items, key=lambda x: x['code']):
            m_width = item['mplus_width']
            n_width = item['noto_width'] 
            u_width = item['utatane_width']
            
            mplus_noto_match = "✓" if m_width == n_width else "✗"
            mplus_utatane_match = "✓" if m_width == u_width else "✗"
            noto_utatane_match = "✓" if n_width == u_width else "✗"
            
            # 推奨判定
            if m_width == n_width == u_width:
                recommendation = "OK"
            elif m_width == n_width:
                recommendation = "M+/Noto準拠" if u_width != m_width else "OK"
            elif m_width == u_width:
                recommendation = "現状維持"
            elif n_width == u_width:
                recommendation = "要検討"
            else:
                recommendation = "M+準拠推奨"
            
            print(f"| U+{item['code']:04X} | {item['char']} | {m_width} | {n_width} | {u_width} | {mplus_noto_match} | {mplus_utatane_match} | {noto_utatane_match} | {recommendation} |")
        
        # カテゴリ統計
        mplus_noto_agree = sum(1 for item in items if item['mplus_width'] == item['noto_width'])
        mplus_utatane_agree = sum(1 for item in items if item['mplus_width'] == item['utatane_width'])
        noto_utatane_agree = sum(1 for item in items if item['noto_width'] == item['utatane_width'])
        
        print()
        print(f"**統計**: M+=Noto: {mplus_noto_agree}/{len(items)}件, M+=Utatane: {mplus_utatane_agree}/{len(items)}件, Noto=Utatane: {noto_utatane_agree}/{len(items)}件")
        print()
    
    # 全体統計
    print("【全体統計・業界標準との比較】")
    print()
    
    total_valid = len(valid_comparisons)
    total_mplus_noto_agree = sum(1 for item in valid_comparisons if item['mplus_width'] == item['noto_width'])
    total_mplus_utatane_agree = sum(1 for item in valid_comparisons if item['mplus_width'] == item['utatane_width'])
    total_noto_utatane_agree = sum(1 for item in valid_comparisons if item['noto_width'] == item['utatane_width'])
    
    print(f"M+ ⇔ Noto一致率: {total_mplus_noto_agree}/{total_valid} ({total_mplus_noto_agree/total_valid*100:.1f}%)")
    print(f"M+ ⇔ Utatane一致率: {total_mplus_utatane_agree}/{total_valid} ({total_mplus_utatane_agree/total_valid*100:.1f}%)")
    print(f"Noto ⇔ Utatane一致率: {total_noto_utatane_agree}/{total_valid} ({total_noto_utatane_agree/total_valid*100:.1f}%)")
    print()
    
    # 問題の重要度評価
    print("【問題の重要度評価】")
    print()
    
    # Utataneが両方と異なる（独自判定）ケース
    unique_utatane = [item for item in valid_comparisons 
                     if item['utatane_width'] != item['mplus_width'] and item['utatane_width'] != item['noto_width']]
    
    # M+とNotoが一致しているのにUtataneが異なるケース（最も問題）
    consensus_violation = [item for item in valid_comparisons 
                          if item['mplus_width'] == item['noto_width'] and item['utatane_width'] != item['mplus_width']]
    
    print(f"Utatane独自判定: {len(unique_utatane)}件")
    print(f"業界コンセンサス違反: {len(consensus_violation)}件 ←最優先修正対象")
    print()
    
    if consensus_violation:
        print("■ 業界コンセンサス違反グリフ（M+=Noto≠Utatane）")
        print("| Unicode | 文字 | カテゴリ | 標準幅 | Utatane幅 | 差分 | 影響度 |")
        print("|---------|------|----------|--------|-----------|------|--------|")
        
        for item in consensus_violation:
            diff = item['utatane_width'] - item['mplus_width']
            impact = "高" if item['category'] in ["IPA", "ギリシャ", "通貨", "数学"] else "中" if item['category'] == "制御図" else "低"
            print(f"| U+{item['code']:04X} | {item['char']} | {item['category']} | {item['mplus_width']} | {item['utatane_width']} | {diff:+d} | {impact} |")
        print()
    
    # 推奨事項
    print("【推奨事項】")
    print()
    
    if total_mplus_noto_agree / total_valid > 0.8:
        print("✓ M+とNotoの幅設計は高い一致率を示しており、業界標準と考えられる")
    
    if len(consensus_violation) > 0:
        print(f"❗ {len(consensus_violation)}件の業界コンセンサス違反を修正することを強く推奨")
        print("  特に以下の優先順位で修正:")
        high_priority = [item for item in consensus_violation if item['category'] in ["IPA", "ギリシャ", "通貨", "数学"]]
        med_priority = [item for item in consensus_violation if item['category'] == "制御図"]
        low_priority = [item for item in consensus_violation if item not in high_priority + med_priority]
        
        if high_priority:
            print(f"  1. 高優先度（学術・国際文書用）: {len(high_priority)}件")
        if med_priority:
            print(f"  2. 中優先度（システム・デバッグ用）: {len(med_priority)}件")
        if low_priority:
            print(f"  3. 低優先度（特殊用途）: {len(low_priority)}件")
    
    compatibility_score = total_noto_utatane_agree / total_valid * 100
    print(f"\n現在のNoto互換性スコア: {compatibility_score:.1f}%")
    
    if len(consensus_violation) == 0:
        print("🎉 業界標準との完全互換達成！")
    elif compatibility_score >= 90:
        print("✅ 高い互換性（軽微な調整で完璧に）")
    elif compatibility_score >= 80:
        print("⚠️  中程度の互換性（要改善）") 
    else:
        print("❌ 互換性に大きな問題あり（大幅修正必要）")
    
    noto_font.close()
    utatane_font.close()
    mplus_font.close()

if __name__ == '__main__':
    detailed_noto_comparison_analysis()