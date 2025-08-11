#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
グリフデータ抽出ツール (FontForge専用)

3つのフォント（M+、やさしさゴシック、Utatane）からグリフデータを抽出し、
JSONファイルに出力する。後で別のスクリプトで可視化する。
"""

import fontforge
import sys
import os
import argparse
import json
from pathlib import Path

# 判定ロジック副作用の184件グリフリスト
PROBLEMATIC_GLYPHS = {
    'ipa': [0x025D, 0x026F, 0x0270, 0x0271, 0x0276, 0x0277, 0x028D, 0x0298,
            0x02A3, 0x02A4, 0x02A5, 0x02A6, 0x02A8, 0x02A9],
    'greek': [0x03D2, 0x03D3, 0x03D4, 0x03D6, 0x03D8, 0x03DA, 0x03E0, 0x03E1],
    'control': [0x2400, 0x2401, 0x2402, 0x2403, 0x2404, 0x2405, 0x2406, 0x2407,
                0x2408, 0x2409, 0x240A, 0x240B, 0x240C, 0x240D, 0x240E, 0x240F,
                0x2410, 0x2411, 0x2412, 0x2413, 0x2414, 0x2415, 0x2416, 0x2417,
                0x2418, 0x2419, 0x241A, 0x241B, 0x241C, 0x241D, 0x241E, 0x241F,
                0x2420, 0x2421, 0x2423, 0x2424, 0x2425],
    'currency': [0x20A8, 0x20A9, 0x20AA, 0x20AF, 0x20B0, 0x20B2, 0x20B3],
    'math': [0x2225, 0x2226, 0x223C],
    'latin_ext_b': [0x1E3E, 0x1E3F, 0x1E40, 0x1E41, 0x1E42, 0x1E43, 0x1E88, 0x1E89,
                    0x1ECC, 0x1ECE, 0x1ED0, 0x1ED2, 0x1ED4, 0x1ED6, 0x1ED8, 0x1EDA,
                    0x1EDC, 0x1EDE, 0x1EE0, 0x1EE2, 0x1EE8, 0x1EEA, 0x1EEC, 0x1EEE,
                    0x1EF0, 0x1EFA],
    'misc': [0x203F, 0x2040, 0x2053, 0x211E, 0x2127, 0xFB00, 0xFB03, 0xFB04,
             0x23CE, 0x110150, 0x110151]
}

HIGH_IMPACT_GLYPHS = (
    PROBLEMATIC_GLYPHS['ipa'] + PROBLEMATIC_GLYPHS['greek'] + 
    PROBLEMATIC_GLYPHS['currency'] + PROBLEMATIC_GLYPHS['math']
)

def get_default_fonts():
    """デフォルトフォントパスを取得"""
    base_dir = Path(__file__).parent.parent
    return {
        'mplus': base_dir / 'sourceFonts' / 'mplus-1m-regular.ttf',
        'yasashisa': base_dir / 'sourceFonts' / 'YasashisaGothicBold-V2.ttf', 
        'utatane': base_dir / 'dist' / 'Utatane-Regular.ttf'
    }

def load_font_safely(font_path):
    """フォントを安全に読み込み"""
    try:
        if not os.path.exists(font_path):
            return None, f"フォントファイルが見つかりません: {font_path}"
        font = fontforge.open(str(font_path))
        return font, None
    except Exception as e:
        return None, f"フォント読み込みエラー: {e}"

def get_glyph_data(font, unicode_val):
    """グリフのデータを取得"""
    if unicode_val not in font:
        return None
    
    glyph = font[unicode_val]
    
    try:
        bbox = glyph.boundingBox()
    except:
        bbox = [0, 0, 0, 0]
    
    # 輪郭データを取得
    contours = []
    try:
        layer = glyph.layers[glyph.activeLayer]
        for contour in layer:
            points = [[float(point.x), float(point.y)] for point in contour]
            if points:
                contours.append(points)
    except:
        contours = []
    
    return {
        'unicode': unicode_val,
        'glyphname': glyph.glyphname,
        'width': float(glyph.width),
        'left_side_bearing': float(glyph.left_side_bearing),
        'right_side_bearing': float(glyph.right_side_bearing),
        'bbox': bbox,
        'contours': contours,
        'exists': True
    }

def extract_font_data(font, glyph_list):
    """フォントからグリフデータを抽出"""
    font_data = {
        'fontname': font.fontname,
        'ascent': float(font.ascent),
        'descent': float(font.descent),
        'glyphs': {}
    }
    
    for unicode_val in glyph_list:
        glyph_data = get_glyph_data(font, unicode_val)
        if glyph_data:
            font_data['glyphs'][str(unicode_val)] = glyph_data
    
    return font_data

def read_test_file_chars(test_file_path, section=None):
    """テストファイルから文字を読み込み"""
    if not os.path.exists(test_file_path):
        return []
    
    chars = set()
    current_section = None
    
    try:
        with open(test_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    if line.startswith('#'):
                        current_section = line[1:].strip()
                    continue
                
                # セクション指定がある場合はそのセクションのみ
                if section and current_section != section:
                    continue
                
                # 文字を抽出
                for char in line:
                    if char.isprintable() and ord(char) > 32:  # 制御文字除外
                        chars.add(ord(char))
    except Exception as e:
        print(f"テストファイル読み込みエラー: {e}")
        return []
    
    return sorted(chars)

def get_glyph_selection(args):
    """引数に基づいてグリフ選択を行う"""
    selected_glyphs = set()
    
    if args.category:
        for cat in args.category:
            if cat in PROBLEMATIC_GLYPHS:
                selected_glyphs.update(PROBLEMATIC_GLYPHS[cat])
    
    if args.priority == 'high':
        selected_glyphs.update(HIGH_IMPACT_GLYPHS)
    elif args.priority == 'all':
        for cat_glyphs in PROBLEMATIC_GLYPHS.values():
            selected_glyphs.update(cat_glyphs)
    
    # テストファイル選択
    if args.from_testfile:
        test_chars = read_test_file_chars(args.test_file, args.section)
        selected_glyphs.update(test_chars)
    
    if args.unicode:
        for unicode_str in args.unicode:
            try:
                if unicode_str.startswith('U+'):
                    unicode_val = int(unicode_str[2:], 16)
                else:
                    unicode_val = int(unicode_str, 16)
                selected_glyphs.add(unicode_val)
            except ValueError:
                print(f"警告: 不正なUnicode指定 '{unicode_str}' をスキップ")
    
    if args.chars:
        for char in args.chars:
            selected_glyphs.add(ord(char))
    
    # デフォルト：高影響グリフ
    if not selected_glyphs:
        selected_glyphs.update(HIGH_IMPACT_GLYPHS)
    
    return sorted(selected_glyphs)

def main():
    parser = argparse.ArgumentParser(description='グリフデータ抽出ツール')
    
    # フォント指定
    parser.add_argument('--mplus', help='M+フォントパス')
    parser.add_argument('--yasashisa', help='やさしさゴシックフォントパス')
    parser.add_argument('--utatane', help='Utataneフォントパス')
    
    # グリフ選択
    parser.add_argument('--category', action='append', 
                       choices=['ipa', 'greek', 'control', 'currency', 'math', 'latin_ext_b', 'misc'],
                       help='カテゴリ選択（複数指定可能）')
    parser.add_argument('--priority', choices=['high', 'all'],
                       help='優先度による選択（high: 32件, all: 184件）')
    parser.add_argument('--from-testfile', action='store_true',
                       help='テストファイルから文字選択')
    parser.add_argument('--test-file', default='test/font_disp.txt',
                       help='テストファイルパス')
    parser.add_argument('--section', help='テストファイルの特定セクション')
    parser.add_argument('--unicode', action='append', metavar='U+XXXX',
                       help='Unicode指定（U+2400形式、複数指定可能）')
    parser.add_argument('--chars', help='文字直接指定')
    
    # 出力設定
    parser.add_argument('--output', '-o', default='glyph_data.json',
                       help='JSON出力ファイル名')
    parser.add_argument('--list-categories', action='store_true',
                       help='利用可能なカテゴリ一覧表示')
    
    args = parser.parse_args()
    
    # カテゴリ一覧表示
    if args.list_categories:
        print("利用可能なカテゴリ:")
        for cat, glyphs in PROBLEMATIC_GLYPHS.items():
            print(f"  {cat:12} : {len(glyphs):2}件")
        return 0
    
    # フォント読み込み
    default_fonts = get_default_fonts()
    font_paths = {
        'mplus': args.mplus or default_fonts['mplus'],
        'yasashisa': args.yasashisa or default_fonts['yasashisa'], 
        'utatane': args.utatane or default_fonts['utatane']
    }
    
    fonts_data = {}
    for key, path in font_paths.items():
        font, error = load_font_safely(path)
        if error:
            print(f"エラー ({key}): {error}")
            return 1
        fonts_data[key] = font
    
    print("フォント読み込み完了:")
    for key, font in fonts_data.items():
        if font:
            print(f"  {key}: {font.fontname}")
    
    # グリフ選択
    selected_glyphs = get_glyph_selection(args)
    if not selected_glyphs:
        print("エラー: 抽出するグリフが選択されていません")
        return 1
    
    print(f"\n抽出対象グリフ: {len(selected_glyphs)}件")
    
    # グリフデータ抽出
    result_data = {
        'metadata': {
            'total_glyphs': len(selected_glyphs),
            'glyph_list': selected_glyphs
        },
        'fonts': {}
    }
    
    for font_key, font in fonts_data.items():
        if font:
            print(f"{font_key} からデータ抽出中...")
            result_data['fonts'][font_key] = extract_font_data(font, selected_glyphs)
    
    # JSON出力
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nグリフデータ抽出完了: {args.output}")
    print(f"次のコマンドでPDF生成: uv run python test/glyph_visualizer.py {args.output}")
    
    # フォントクローズ
    for font in fonts_data.values():
        if font:
            font.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())