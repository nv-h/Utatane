#!/usr/bin/env python3
"""
Unicode Range Analysis Tool for Utatane Font Project

指定したUnicode範囲の文字を複数フォント間で分析

使用方法:
fontforge -lang=py -script analyze_ranges.py [オプション]
"""

from typing import List, Optional
import sys

try:
    import fontforge
except ImportError:
    print("このスクリプトはFontForge環境で実行してください")
    print("使用方法: fontforge -lang=py -script analyze_ranges.py")
    sys.exit(1)


def analyze_unicode_ranges(font_selection: List[str] = None, 
                          range_names: List[str] = None,
                          show_samples: bool = True,
                          max_samples: int = 10):
    """指定したUnicode範囲の文字を複数フォント間で分析
    
    Args:
        font_selection: 分析するフォント名のリスト
        range_names: 分析するUnicode範囲名のリスト
        show_samples: サンプル文字を表示するかどうか
        max_samples: 表示する最大サンプル数
    """
    from font_analysis_utils import (
        create_analyzer_with_error_handling,
        ReportGenerator,
        FontAnalyzer
    )
    
    if font_selection is None:
        font_selection = ['mplus', 'ubuntu']
    
    # FontAnalyzer を初期化
    analyzer = create_analyzer_with_error_handling(font_selection)
    if not analyzer:
        return
    
    try:
        print("Unicode範囲別文字分析")
        print("=" * 70)
        
        # フォント情報表示
        for font_name in font_selection:
            ReportGenerator.print_font_info(analyzer, font_name)
        print("=" * 70)
        
        # Unicode範囲を取得
        unicode_ranges = FontAnalyzer.get_unicode_ranges()
        
        if range_names:
            # 指定された範囲のみに絞り込み
            filtered_ranges = {}
            for range_name in range_names:
                if range_name in unicode_ranges:
                    filtered_ranges[range_name] = unicode_ranges[range_name]
                else:
                    print(f"警告: 不明な範囲名 '{range_name}'")
            unicode_ranges = filtered_ranges
        
        total_analyzed = 0
        total_mismatches = 0
        
        for range_name, (start, end) in unicode_ranges.items():
            char_codes = list(range(start, end + 1))
            
            print(f"\n【{range_name}】(U+{start:04X} - U+{end:04X})")
            
            # 各フォントでの存在確認
            font_presence = {}
            common_chars = []
            
            for font_name in font_selection:
                present_chars = []
                for code in char_codes:
                    width = analyzer.get_glyph_width(font_name, code)
                    if width is not None:
                        present_chars.append(code)
                font_presence[font_name] = set(present_chars)
                print(f"  {font_name}: {len(present_chars)}文字")
            
            # 共通文字を特定
            if font_selection:
                common_chars = list(set.intersection(*font_presence.values()))
                print(f"  共通文字: {len(common_chars)}文字")
            
            if not common_chars:
                print("  → 共通する文字がありません")
                continue
            
            # 幅比較
            comparison_results = analyzer.compare_widths(common_chars, font_selection)
            inconsistencies = [r for r in comparison_results if r['has_inconsistency']]
            
            match_count = len(common_chars) - len(inconsistencies)
            mismatch_count = len(inconsistencies)
            
            if mismatch_count > 0:
                print(f"  ⚠️ 幅不整合: {mismatch_count}/{len(common_chars)}文字")
                total_mismatches += mismatch_count
            else:
                print(f"  ✓ 全て一致: {len(common_chars)}文字")
            
            total_analyzed += len(common_chars)
            
            # サンプル表示
            if show_samples and inconsistencies:
                print(f"  不整合サンプル（最大{max_samples}件）:")
                for i, result in enumerate(inconsistencies[:max_samples]):
                    char_display = result['char']
                    code = result['code']
                    widths = []
                    for font_name in font_selection:
                        width = result['widths'].get(font_name)
                        if width is not None:
                            widths.append(f"{font_name}={width}")
                    width_str = ", ".join(widths)
                    print(f"    U+{code:04X} '{char_display}': {width_str}")
                
                if len(inconsistencies) > max_samples:
                    print(f"    ... 他{len(inconsistencies) - max_samples}件")
            
            elif show_samples and common_chars:
                # 一致例のサンプル表示
                sample_chars = common_chars[:min(3, len(common_chars))]
                print("  サンプル文字:")
                for code in sample_chars:
                    char_display = analyzer._format_char(code)
                    widths = []
                    for font_name in font_selection:
                        width = analyzer.get_glyph_width(font_name, code)
                        if width is not None:
                            widths.append(f"{font_name}={width}")
                    width_str = ", ".join(widths)
                    print(f"    U+{code:04X} '{char_display}': {width_str}")
        
        # 総合結果
        print("\n" + "=" * 70)
        print("【総合結果】")
        print(f"分析文字数: {total_analyzed}文字")
        print(f"幅不整合: {total_mismatches}文字 ({total_mismatches/total_analyzed*100:.1f}%)" if total_analyzed > 0 else "分析対象なし")
        
        if total_mismatches == 0 and total_analyzed > 0:
            print("🎉 全ての文字幅が一致しています！")
    
    finally:
        analyzer.close_fonts()


def get_available_ranges():
    """利用可能なUnicode範囲名を表示"""
    from font_analysis_utils import FontAnalyzer
    
    ranges = FontAnalyzer.get_unicode_ranges()
    print("利用可能なUnicode範囲:")
    for name, (start, end) in ranges.items():
        print(f"  {name:<20} (U+{start:04X} - U+{end:04X})")


if __name__ == '__main__':
    font_selection = None
    range_names = None
    show_samples = True
    max_samples = 10
    
    # コマンドライン引数解析
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--fonts' and i + 1 < len(args):
            font_selection = args[i + 1].split(',')
            i += 2
        elif args[i] == '--ranges' and i + 1 < len(args):
            range_names = args[i + 1].split(',')
            i += 2
        elif args[i] == '--no-samples':
            show_samples = False
            i += 1
        elif args[i] == '--max-samples' and i + 1 < len(args):
            max_samples = int(args[i + 1])
            i += 2
        elif args[i] == '--list-ranges':
            get_available_ranges()
            sys.exit(0)
        elif args[i] == '--help':
            print("使用法: python analyze_ranges.py [オプション]")
            print("オプション:")
            print("  --fonts FONTS         比較するフォント名（カンマ区切り）")
            print("  --ranges RANGES       分析するUnicode範囲名（カンマ区切り）")
            print("  --no-samples          サンプル文字を表示しない")
            print("  --max-samples N       表示する最大サンプル数")
            print("  --list-ranges         利用可能なUnicode範囲一覧を表示")
            print("  --help                このヘルプを表示")
            print()
            print("例:")
            print("  # 基本的な使用法")
            print("  fontforge -lang=py -script analyze_ranges.py")
            print("  # ラテン・ギリシャ文字のみ分析")
            print("  fontforge -lang=py -script analyze_ranges.py --ranges 'ギリシャ,基本ラテン拡張'")
            print("  # 特定フォント間の比較")
            print("  fontforge -lang=py -script analyze_ranges.py --fonts 'mplus,utatane'")
            sys.exit(0)
        else:
            print(f"不明な引数: {args[i]}")
            print("--help で使用法を確認してください")
            sys.exit(1)
    
    analyze_unicode_ranges(font_selection, range_names, show_samples, max_samples)