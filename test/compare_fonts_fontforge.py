#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FontForgeを使用したフォント比較ツール
文字幅、メトリクス、グリフの詳細な比較を行います
"""

import fontforge
import os
import sys
import argparse
from collections import OrderedDict


def load_font_safely(font_path):
    """フォントを安全に読み込む"""
    if not os.path.exists(font_path):
        return None, f"フォントファイルが見つかりません: {font_path}"
    
    try:
        font = fontforge.open(font_path)
        return font, None
    except Exception as e:
        return None, f"フォント読み込みエラー: {e}"


def get_font_metrics(font):
    """フォントの基本メトリクス情報を取得"""
    return {
        'em': font.em,
        'ascent': font.ascent,
        'descent': font.descent,
        'fontname': font.fontname,
        'familyname': font.familyname,
        'weight': font.weight,
        'glyph_count': len(font)
    }


def get_glyph_metrics(font, unicode_point):
    """指定されたUnicodeポイントのグリフメトリクスを取得"""
    if unicode_point not in font:
        return None
    
    glyph = font[unicode_point]
    return {
        'width': glyph.width,
        'left_side_bearing': glyph.left_side_bearing,
        'right_side_bearing': glyph.right_side_bearing,
        'unicode': glyph.unicode,
        'glyphname': glyph.glyphname,
        'exists': True
    }


def read_test_strings(filepath):
    """テスト用文字列ファイルを読み込み、セクション別に分類"""
    if not os.path.exists(filepath):
        return {}
    
    sections = OrderedDict()
    current_section = "基本文字"
    sections[current_section] = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip()
                if not line:
                    continue
                
                # セクション判定
                if 'ローマ数字' in line:
                    current_section = "ローマ数字"
                    sections[current_section] = []
                    continue
                elif 'ハイフン' in line:
                    current_section = "ハイフン・ダッシュ"
                    sections[current_section] = []
                    continue
                elif line.startswith('    ') or line.startswith('U+25') or line.startswith('U+26'):
                    # 表の行はスキップ
                    continue
                elif '▀▁▂▃▄▅▆▇█' in line or '┌──────────┬' in line:
                    current_section = "罫線・ブロック"
                    if current_section not in sections:
                        sections[current_section] = []
                
                sections[current_section].append(line)
    
    except Exception as e:
        print(f"テストファイル読み込みエラー: {e}")
        return {"エラー": []}
    
    return sections


def analyze_string_widths(font, test_string):
    """文字列の各文字の幅を解析"""
    results = []
    total_width = 0
    
    for char in test_string:
        unicode_point = ord(char)
        metrics = get_glyph_metrics(font, unicode_point)
        
        if metrics:
            total_width += metrics['width']
            results.append({
                'char': char,
                'unicode': f"U+{unicode_point:04X}",
                'width': metrics['width'],
                'lsb': metrics['left_side_bearing'],
                'rsb': metrics['right_side_bearing'],
                'exists': True
            })
        else:
            results.append({
                'char': char,
                'unicode': f"U+{unicode_point:04X}",
                'width': 0,
                'lsb': 0,
                'rsb': 0,
                'exists': False
            })
    
    return results, total_width


def compare_fonts_detailed(font1_path, font2_path, test_sections):
    """2つのフォントの詳細比較を行う"""
    # フォント読み込み
    font1, error1 = load_font_safely(font1_path)
    if error1:
        return None, error1
    
    font2, error2 = load_font_safely(font2_path)
    if error2:
        font1.close()
        return None, error2
    
    try:
        comparison_result = {
            'font1_metrics': get_font_metrics(font1),
            'font2_metrics': get_font_metrics(font2),
            'font1_path': font1_path,
            'font2_path': font2_path,
            'sections': {}
        }
        
        for section_name, strings in test_sections.items():
            section_results = []
            
            for test_string in strings:
                if not test_string.strip():
                    continue
                
                # 各フォントで文字列を解析
                font1_analysis, font1_total = analyze_string_widths(font1, test_string)
                font2_analysis, font2_total = analyze_string_widths(font2, test_string)
                
                section_results.append({
                    'text': test_string,
                    'font1_analysis': font1_analysis,
                    'font2_analysis': font2_analysis,
                    'font1_total_width': font1_total,
                    'font2_total_width': font2_total,
                    'width_diff': font2_total - font1_total
                })
            
            comparison_result['sections'][section_name] = section_results
        
        return comparison_result, None
    
    finally:
        font1.close()
        font2.close()


def format_width_bar(width, max_width=1000):
    """幅を視覚的なバーで表示"""
    bar_length = 20
    if max_width == 0:
        return "□" * bar_length
    
    filled = int((width / max_width) * bar_length)
    return "█" * filled + "□" * (bar_length - filled)


def format_comparison_report(comparison_data, show_visual=True):
    """比較結果を整形して出力"""
    if not comparison_data:
        return
    
    print("=" * 80)
    print("FontForge フォント比較レポート")
    print("=" * 80)
    
    # フォント基本情報
    f1_metrics = comparison_data['font1_metrics']
    f2_metrics = comparison_data['font2_metrics']
    
    print(f"\nフォント1: {os.path.basename(comparison_data['font1_path'])}")
    print(f"  ファミリ名: {f1_metrics['familyname']}")
    print(f"  フォント名: {f1_metrics['fontname']}")
    print(f"  EM: {f1_metrics['em']}, Ascent: {f1_metrics['ascent']}, Descent: {f1_metrics['descent']}")
    print(f"  グリフ数: {f1_metrics['glyph_count']}")
    
    print(f"\nフォント2: {os.path.basename(comparison_data['font2_path'])}")
    print(f"  ファミリ名: {f2_metrics['familyname']}")
    print(f"  フォント名: {f2_metrics['fontname']}")
    print(f"  EM: {f2_metrics['em']}, Ascent: {f2_metrics['ascent']}, Descent: {f2_metrics['descent']}")
    print(f"  グリフ数: {f2_metrics['glyph_count']}")
    
    print("\n" + "=" * 80)
    print("文字列比較結果")
    print("=" * 80)
    
    # セクション別に結果を表示
    for section_name, section_data in comparison_data['sections'].items():
        if not section_data:
            continue
            
        print(f"\n【{section_name}】")
        print("-" * 60)
        
        for item in section_data:
            text = item['text']
            f1_total = item['font1_total_width']
            f2_total = item['font2_total_width']
            diff = item['width_diff']
            
            print(f"\nテキスト: {text}")
            print(f"総幅: {f1_total:>4} → {f2_total:>4} (差分: {diff:+4})")
            
            # 文字ごとの詳細（幅に差がある場合のみ）
            if abs(diff) > 0:
                print("  文字別詳細:")
                for i, char in enumerate(text):
                    if i < len(item['font1_analysis']) and i < len(item['font2_analysis']):
                        f1_char = item['font1_analysis'][i]
                        f2_char = item['font2_analysis'][i]
                        
                        if f1_char['width'] != f2_char['width']:
                            if show_visual:
                                # 視覚的なバー表示
                                bar1 = format_width_bar(f1_char['width'])
                                bar2 = format_width_bar(f2_char['width'])
                                print(f"    {char} ({f1_char['unicode']}):")
                                print(f"      {f1_char['width']:>4} {bar1}")
                                print(f"      {f2_char['width']:>4} {bar2}")
                                print(f"      差分: {f2_char['width'] - f1_char['width']:+4}")
                            else:
                                print(f"    {char} ({f1_char['unicode']}): "
                                      f"{f1_char['width']:>4} → {f2_char['width']:>4} "
                                      f"(LSB: {f1_char['lsb']:>3}→{f2_char['lsb']:>3}, "
                                      f"RSB: {f1_char['rsb']:>3}→{f2_char['rsb']:>3})")


def main():
    parser = argparse.ArgumentParser(description='FontForgeを使用したフォント比較')
    parser.add_argument('--font1', '-f1', default='dist/Utatane-Regular.ttf', 
                        help='比較元フォント（デフォルト: 現在のRegular）')
    parser.add_argument('--font2', '-f2', default='dist/v1.3.0/Utatane-Regular.ttf',
                        help='比較先フォント（デフォルト: v1.3.0 Regular）')
    parser.add_argument('--test-file', '-t', default='test/font_disp.txt',
                        help='テスト文字列ファイル')
    parser.add_argument('--output', '-o', help='結果をファイルに出力')
    parser.add_argument('--visual', '-v', action='store_true', 
                        help='文字幅を視覚的なバーで表示')
    
    args = parser.parse_args()
    
    # パスを絶対パスに変換（testディレクトリから親ディレクトリへ）
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    font1_path = os.path.join(base_dir, args.font1) if not os.path.isabs(args.font1) else args.font1
    font2_path = os.path.join(base_dir, args.font2) if not os.path.isabs(args.font2) else args.font2
    test_file_path = os.path.join(base_dir, args.test_file) if not os.path.isabs(args.test_file) else args.test_file
    
    print("比較対象:")
    print(f"  フォント1: {font1_path}")
    print(f"  フォント2: {font2_path}")
    print(f"  テストファイル: {test_file_path}")
    
    # テスト文字列を読み込み
    test_sections = read_test_strings(test_file_path)
    if not test_sections:
        print("テスト文字列の読み込みに失敗しました")
        return 1
    
    # フォント比較実行
    comparison_result, error = compare_fonts_detailed(font1_path, font2_path, test_sections)
    if error:
        print(f"比較エラー: {error}")
        return 1
    
    # 結果出力
    if args.output:
        # ファイル出力
        with open(args.output, 'w', encoding='utf-8') as f:
            original_stdout = sys.stdout
            sys.stdout = f
            format_comparison_report(comparison_result, show_visual=args.visual)
            sys.stdout = original_stdout
        print(f"比較結果を {args.output} に保存しました")
    else:
        # 標準出力
        format_comparison_report(comparison_result, show_visual=args.visual)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())