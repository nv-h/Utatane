#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge
import sys

from typing import Dict, List

def comprehensive_width_check(base_font: str = 'mplus', target_font: str = 'utatane', 
                             show_unicode_names: bool = False, max_mismatches_display: int = 50):
    """2つのフォント間で全グリフ幅の包括的な一致確認
    
    Args:
        base_font: 基準となるフォント名
        target_font: 比較対象のフォント名
        show_unicode_names: Unicode文字名を表示するかどうか
        max_mismatches_display: 表示する不一致の最大件数
    """
    from font_analysis_utils import create_analyzer_with_error_handling, ReportGenerator
    
    # FontAnalyzer を初期化
    analyzer = create_analyzer_with_error_handling([base_font, target_font])
    if not analyzer:
        return
    
    try:
        print(f"{base_font.upper()} vs {target_font.upper()} 全グリフ幅比較")
        print("=" * 80)
        
        # フォント情報表示
        for font_name in [base_font, target_font]:
            ReportGenerator.print_font_info(analyzer, font_name)
        print()
        
        # 共通のグリフを特定
        base_glyphs = analyzer.get_glyph_set(base_font)
        target_glyphs = analyzer.get_glyph_set(target_font)
        common_codes = base_glyphs & target_glyphs
        
        print(f"{base_font.upper()}のグリフ数: {len(base_glyphs)}")
        print(f"{target_font.upper()}のグリフ数: {len(target_glyphs)}")
        print(f"共通グリフ数: {len(common_codes)}")
        print()
        
        # 幅比較を実行
        comparison_results = analyzer.compare_widths(list(common_codes), [base_font, target_font])
        
        # 結果サマリー
        inconsistencies = ReportGenerator.print_width_comparison_summary(
            comparison_results, 
            f"{base_font.upper()} vs {target_font.upper()} 幅比較結果"
        )
        
        if not inconsistencies:
            print("🎉 素晴らしい！全てのグリフの幅が一致しています！")
            return
        
        # 不一致グリフの詳細分析
        print("\n【幅不一致グリフの詳細】")
        print(f"{'文字':<8} {'コード':<12} {base_font.upper()+'幅':<8} {target_font.upper()+'幅':<12} {'差分':<8}", end="")
        
        if show_unicode_names:
            print(" 文字名")
        else:
            print()
        
        print("-" * (80 + (50 if show_unicode_names else 0)))
        
        displayed_count = 0
        for result in inconsistencies:
            if displayed_count >= max_mismatches_display:
                break
                
            char_display = result['char']
            code = result['code']
            base_width = result['widths'][base_font]
            target_width = result['widths'][target_font]
            
            if base_width is None or target_width is None:
                continue  # どちらかが存在しない場合はスキップ
                
            diff = target_width - base_width
            
            row = f"{char_display:<8} U+{code:04X}     {base_width:<8} {target_width:<12} {diff:+4d}"
            
            if show_unicode_names:
                char_name = _get_unicode_name(code)
                row += f"     {char_name}"
            
            print(row)
            displayed_count += 1
        
        if len(inconsistencies) > max_mismatches_display:
            print(f"\n... 他{len(inconsistencies) - max_mismatches_display}件")
        
        # Unicode範囲別分析
        print(f"\n{'='*80}")
        print("【Unicode範囲別の不一致サマリー】")
        
        range_analysis = _categorize_by_unicode_ranges(inconsistencies)
        
        for range_name, mismatches_in_range in range_analysis.items():
            if mismatches_in_range:
                print(f"{range_name}: {len(mismatches_in_range)}件")
                
                # 各範囲の詳細（最初の3件のみ表示）
                sample_count = min(3, len(mismatches_in_range))
                for i, m in enumerate(mismatches_in_range[:sample_count]):
                    base_width = m['widths'][base_font]
                    target_width = m['widths'][target_font] 
                    diff = target_width - base_width if base_width and target_width else 0
                    print(f"  U+{m['code']:04X} {m['char']} : {base_width} → {target_width} ({diff:+d})")
                
                if len(mismatches_in_range) > sample_count:
                    print(f"  ... 他{len(mismatches_in_range)-sample_count}件")
                print()
    
    finally:
        analyzer.close_fonts()


def _get_unicode_name(char_code: int) -> str:
    """Unicode文字名を取得"""
    try:
        import unicodedata
        if char_code < 0x10000:
            return unicodedata.name(chr(char_code), "UNKNOWN")
    except:
        pass
    return "UNKNOWN"


def _categorize_by_unicode_ranges(inconsistencies: List[Dict]) -> Dict[str, List[Dict]]:
    """不一致グリフをUnicode範囲別に分類"""
    from font_analysis_utils import FontAnalyzer
    
    unicode_ranges = FontAnalyzer.get_unicode_ranges()
    range_mismatches = {}
    
    # 初期化
    for category in unicode_ranges.keys():
        range_mismatches[category] = []
    range_mismatches["その他"] = []
    
    for mismatch in inconsistencies:
        code = mismatch['code']
        categorized = False
        
        for category, (start, end) in unicode_ranges.items():
            if start <= code <= end:
                range_mismatches[category].append(mismatch)
                categorized = True
                break
        
        if not categorized:
            range_mismatches["その他"].append(mismatch)
    
    # 空のカテゴリを除去
    return {k: v for k, v in range_mismatches.items() if v}

if __name__ == '__main__':
    import sys
    
    # コマンドライン引数の処理
    base_font = 'mplus'
    target_font = 'utatane'
    show_unicode_names = False
    max_display = 50
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--base' and i + 1 < len(args):
            base_font = args[i + 1]
            i += 2
        elif args[i] == '--target' and i + 1 < len(args):
            target_font = args[i + 1]
            i += 2
        elif args[i] == '--names':
            show_unicode_names = True
            i += 1
        elif args[i] == '--max-display' and i + 1 < len(args):
            max_display = int(args[i + 1])
            i += 2
        elif args[i] == '--help':
            print("使用法: python comprehensive_width_check.py [オプション]")
            print("オプション:")
            print("  --base FONT       基準フォント名 (default: mplus)")
            print("  --target FONT     対象フォント名 (default: utatane)")
            print("  --names           Unicode文字名を表示")
            print("  --max-display N   表示する不一致の最大件数 (default: 50)")
            sys.exit(0)
        else:
            print(f"不明な引数: {args[i]}")
            print("--help で使用法を確認してください")
            sys.exit(1)
    
    comprehensive_width_check(base_font, target_font, show_unicode_names, max_display)