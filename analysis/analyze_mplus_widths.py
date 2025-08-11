#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge
import sys

def analyze_font_widths(font_name: str = 'mplus', show_samples: bool = True):
    """指定されたフォントの文字幅を詳細に分析する
    
    Args:
        font_name: 分析対象フォント名 ('mplus', 'ubuntu', 'yasashisa', 'utatane')
        show_samples: サンプル文字を表示するかどうか
    """
    from font_analysis_utils import create_analyzer_with_error_handling, ReportGenerator
    
    # フォント名の正規化とバリデーション
    available_fonts = {
        'mplus': 'M+ 1m Regular',
        'ubuntu': 'Ubuntu Mono Regular',
        'yasashisa': 'やさしさゴシックボールド V2',
        'utatane': 'Utatane Regular'
    }
    
    if font_name not in available_fonts:
        print(f"エラー: 不明なフォント名 '{font_name}'")
        print(f"使用可能なフォント: {', '.join(available_fonts.keys())}")
        return
    
    # FontAnalyzer を初期化
    analyzer = create_analyzer_with_error_handling([font_name])
    if not analyzer:
        return
    
    try:
        print(f"{available_fonts[font_name]}フォント詳細分析")
        print("=" * 60)
        
        # フォント基本情報を表示
        ReportGenerator.print_font_info(analyzer, font_name)
        print("=" * 60)
        
        # 分析対象の文字範囲を取得
        analysis_ranges = _get_analysis_ranges()
        
        width_stats = {}
        
        for range_name, char_codes in analysis_ranges.items():
            widths = []
            present_chars = []
            
            for code in char_codes:
                width = analyzer.get_glyph_width(font_name, code)
                if width is not None:
                    widths.append(width)
                    present_chars.append((code, analyzer._format_char(code), width))
            
            if widths:
                width_stats[range_name] = {
                    'count': len(widths),
                    'min_width': min(widths),
                    'max_width': max(widths),
                    'avg_width': sum(widths) / len(widths),
                    'unique_widths': sorted(list(set(widths))),
                    'sample_chars': present_chars[:10]  # 最初の10文字
                }
        
        # 結果出力
        for range_name, stats in width_stats.items():
            print(f"\n【{range_name}】")
            print(f"  文字数: {stats['count']}")
            print(f"  幅の範囲: {stats['min_width']} - {stats['max_width']}")
            print(f"  平均幅: {stats['avg_width']:.1f}")
            print(f"  固有の幅: {stats['unique_widths']}")
            
            if show_samples:
                print(f"  サンプル文字:")
                for code, char, width in stats['sample_chars']:
                    try:
                        print(f"    U+{code:04X} '{char}' width={width}")
                    except:
                        print(f"    U+{code:04X} [表示不可] width={width}")
        
        # 全角/半角の基準を特定
        print("\n" + "=" * 60)
        print("【全角/半角基準の推定】")
        
        if 'ASCII' in width_stats and 'ひらがな' in width_stats:
            ascii_widths = width_stats['ASCII']['unique_widths']
            hiragana_widths = width_stats['ひらがな']['unique_widths']
            
            ascii_width = ascii_widths[0] if len(ascii_widths) == 1 else None
            hiragana_width = hiragana_widths[0] if len(hiragana_widths) == 1 else None
            
            print(f"ASCII文字幅: {ascii_width}")
            print(f"ひらがな文字幅: {hiragana_width}")
            
            if ascii_width and hiragana_width:
                ratio = hiragana_width / ascii_width
                print(f"全角/半角比率: {ratio:.3f}")
                print(f"推定半角幅: {ascii_width}")
                print(f"推定全角幅: {hiragana_width}")
            else:
                print("⚠️ 幅が統一されていないため、正確な比率を算出できません")
                if len(ascii_widths) > 1:
                    print(f"  ASCII幅のばらつき: {ascii_widths}")
                if len(hiragana_widths) > 1:
                    print(f"  ひらがな幅のばらつき: {hiragana_widths}")
    
    finally:
        analyzer.close_fonts()


def _get_analysis_ranges():
    """分析対象の文字範囲を定義"""
    return {
        "ASCII": list(range(0x0020, 0x007F+1)),
        "ひらがな": list(range(0x3040, 0x309F+1)),
        "カタカナ": list(range(0x30A0, 0x30FF+1)),
        "漢字CJK": list(range(0x4E00, 0x4E00+100)),  # 最初の100文字のみ
        "半角カタカナ": list(range(0xFF61, 0xFF9F+1)),
        "罫線素片": list(range(0x2500, 0x257F+1)),
        "ブロック要素": list(range(0x2580, 0x259F+1)),
        "記号": [0x00A0, 0x00A6, 0x00B1, 0x00B6, 0x00D7, 0x00F7, 0x2010, 0x2011, 
                0x2012, 0x2013, 0x2014, 0x2015, 0x2016, 0x2017, 0x2018, 0x2019],
    }

if __name__ == '__main__':
    import sys
    
    # コマンドライン引数の処理
    font_name = 'mplus'
    show_samples = True
    
    if len(sys.argv) > 1:
        font_name = sys.argv[1]
    if len(sys.argv) > 2:
        show_samples = sys.argv[2].lower() in ['true', '1', 'yes']
    
    analyze_font_widths(font_name, show_samples)