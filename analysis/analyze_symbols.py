#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge

from typing import List, Optional

def analyze_symbol_widths(font_selection: List[str] = None, categories: List[str] = None, 
                        show_detailed_output: bool = True):
    """記号類（○△②×✕等）の文字幅を複数フォント間で比較分析
    
    Args:
        font_selection: 比較するフォント名のリスト。Noneの場合は ['mplus', 'ubuntu', 'yasashisa']
        categories: 分析する記号カテゴリ。Noneの場合は全カテゴリ
        show_detailed_output: 詳細な出力を表示するかどうか
    """
    from font_analysis_utils import (
        create_analyzer_with_error_handling, 
        ReportGenerator, 
        FontAnalyzer
    )
    
    if font_selection is None:
        font_selection = ['mplus', 'ubuntu', 'yasashisa']
    
    # FontAnalyzer を初期化
    analyzer = create_analyzer_with_error_handling(font_selection)
    if not analyzer:
        return
    
    try:
        print("記号類の文字幅分析（描画ずれ調査）")
        print("=" * 70)
        
        # 各フォントの基本情報を表示
        for font_name in font_selection:
            ReportGenerator.print_font_info(analyzer, font_name)
        
        print("=" * 70)
        
        # 記号カテゴリを取得
        symbol_categories = FontAnalyzer.get_symbol_categories()
        
        if categories:
            # 指定されたカテゴリのみに絞り込み
            symbol_categories = {k: v for k, v in symbol_categories.items() if k in categories}
        
        all_mismatches = []
        
        for category, char_codes in symbol_categories.items():
            print(f"\n【{category}】")
            
            if show_detailed_output:
                # ヘッダー行を動的に生成
                header = f"{'文字':<8} {'コード':<10}"
                for font_name in font_selection:
                    header += f" {font_name:<8}"
                header += f" {'状況':<15}"
                print(header)
                print("-" * len(header))
            
            category_mismatches = []
            
            for code in char_codes:
                # 各フォントでの幅を取得
                width_info = {}
                widths = []
                fonts_with_char = []
                
                for font_name in font_selection:
                    width = analyzer.get_glyph_width(font_name, code)
                    width_info[font_name] = width
                    if width is not None:
                        widths.append(width)
                        fonts_with_char.append(font_name)
                
                # 状況判定
                status = ""
                if len(set(widths)) > 1:
                    status = "⚠️ 幅不統一"
                    category_mismatches.append({
                        'code': code,
                        'char': analyzer._format_char(code),
                        'width_info': width_info,
                        'fonts': fonts_with_char
                    })
                elif len(fonts_with_char) == 1:
                    status = f"{fonts_with_char[0]}のみ"
                elif len(fonts_with_char) == 0:
                    status = "全フォントになし"
                else:
                    status = "統一済み"
                
                if show_detailed_output:
                    char_display = analyzer._format_char(code)
                    row = f"{char_display:<8} U+{code:04X}"
                    
                    for font_name in font_selection:
                        width = width_info.get(font_name)
                        width_str = str(width) if width else "なし"
                        row += f"   {width_str:<8}"
                    
                    row += f" {status}"
                    print(row)
            
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
                for font_name, width in mismatch['width_info'].items():
                    if width is not None:
                        print(f"  {font_name}: {width}")
                print(f"  存在フォント: {', '.join(mismatch['fonts'])}")
        else:
            print("幅不統一の記号は見つかりませんでした。")
    
    finally:
        analyzer.close_fonts()

if __name__ == '__main__':
    import sys
    
    # コマンドライン引数の処理
    font_selection = None
    categories = None
    show_detailed = True
    
    # 簡単な引数解析
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--fonts' and i + 1 < len(args):
            font_selection = args[i + 1].split(',')
            i += 2
        elif args[i] == '--categories' and i + 1 < len(args):
            categories = args[i + 1].split(',')
            i += 2
        elif args[i] == '--brief':
            show_detailed = False
            i += 1
        else:
            print(f"不明な引数: {args[i]}")
            print("使用法: python analyze_symbols.py [--fonts font1,font2] [--categories cat1,cat2] [--brief]")
            sys.exit(1)
    
    analyze_symbol_widths(font_selection, categories, show_detailed)