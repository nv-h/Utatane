#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge
import sys

def generate_width_mismatch_report(base_font: str = 'mplus', target_font: str = 'utatane', 
                                  mismatch_pattern: tuple = (500, 1000), output_format: str = 'markdown'):
    """幅不一致パターンのグリフ詳細レポートを生成
    
    Args:
        base_font: 基準フォント名
        target_font: 比較対象フォント名
        mismatch_pattern: (基準幅, 対象幅) のタプル
        output_format: 出力形式 ('markdown', 'text', 'csv')
    """
    from font_analysis_utils import create_analyzer_with_error_handling
    
    # FontAnalyzer を初期化
    analyzer = create_analyzer_with_error_handling([base_font, target_font])
    if not analyzer:
        return
    
    try:
        # 共通グリフを取得
        base_glyphs = analyzer.get_glyph_set(base_font)
        target_glyphs = analyzer.get_glyph_set(target_font)
        common_codes = base_glyphs & target_glyphs
        
        # 指定されたパターンの幅不一致を収集
        base_width, target_width = mismatch_pattern
        mismatched_glyphs = []
        
        for code in sorted(common_codes):
            base_w = analyzer.get_glyph_width(base_font, code)
            target_w = analyzer.get_glyph_width(target_font, code)
            
            if base_w == base_width and target_w == target_width:
                char_display = analyzer._format_char(code)
                char_name = _get_unicode_character_name(code)
                unicode_block = get_unicode_block_name(code)
                
                mismatched_glyphs.append({
                    'code': code,
                    'char': char_display,
                    'name': char_name,
                    'unicode_block': unicode_block
                })
        
        # Unicode範囲別に分類
        blocks = {}
        for glyph in mismatched_glyphs:
            block = glyph['unicode_block']
            if block not in blocks:
                blocks[block] = []
            blocks[block].append(glyph)
        
        # 結果出力
        if output_format == 'markdown':
            _output_markdown_report(base_font, target_font, mismatch_pattern, blocks, mismatched_glyphs)
        elif output_format == 'text':
            _output_text_report(base_font, target_font, mismatch_pattern, blocks, mismatched_glyphs)
        elif output_format == 'csv':
            _output_csv_report(base_font, target_font, mismatch_pattern, mismatched_glyphs)
        else:
            print(f"不明な出力形式: {output_format}")
    
    finally:
        analyzer.close_fonts()


def _get_unicode_character_name(code):
    """Unicode文字名を取得"""
    try:
        import unicodedata
        if code < 0x10000:
            return unicodedata.name(chr(code), "UNKNOWN")
    except:
        pass
    return "UNKNOWN"


def _output_markdown_report(base_font, target_font, pattern, blocks, all_glyphs):
    """Markdown形式でレポート出力"""
    base_width, target_width = pattern
    
    print(f"## 幅不一致グリフ一覧（{len(all_glyphs)}件）")
    print()
    print(f"**問題**: {base_font.upper()}フォントで幅{base_width}のグリフが、{target_font.upper()}で幅{target_width}に変更されている")
    print()
    
    total_count = 0
    for block_name in sorted(blocks.keys()):
        glyphs = blocks[block_name]
        total_count += len(glyphs)
        
        print(f"### {block_name}（{len(glyphs)}件）")
        print()
        print("| Unicode | 文字 | 文字名 |")
        print("|---------|------|--------|")
        
        for glyph in sorted(glyphs, key=lambda x: x['code']):
            unicode_str = f"U+{glyph['code']:04X}"
            char_str = glyph['char']
            name_str = glyph['name']
            print(f"| {unicode_str} | {char_str} | {name_str} |")
        
        print()
    
    print(f"**総計**: {total_count}件")


def _output_text_report(base_font, target_font, pattern, blocks, all_glyphs):
    """テキスト形式でレポート出力"""
    base_width, target_width = pattern
    
    print(f"{base_font.upper()} vs {target_font.upper()} 幅不一致レポート")
    print("=" * 60)
    print(f"パターン: {base_width} → {target_width}")
    print(f"総件数: {len(all_glyphs)}件")
    print()
    
    for block_name in sorted(blocks.keys()):
        glyphs = blocks[block_name]
        print(f"【{block_name}】（{len(glyphs)}件）")
        
        for glyph in sorted(glyphs, key=lambda x: x['code']):
            print(f"  U+{glyph['code']:04X} '{glyph['char']}' {glyph['name']}")
        print()


def _output_csv_report(base_font, target_font, pattern, all_glyphs):
    """CSV形式でレポート出力"""
    print("Unicode,Character,Name,Block,BaseWidth,TargetWidth")
    base_width, target_width = pattern
    
    for glyph in sorted(all_glyphs, key=lambda x: x['code']):
        unicode_str = f"U+{glyph['code']:04X}"
        char_str = glyph['char'].replace(',', '\\,')  # CSVエスケープ
        name_str = glyph['name'].replace(',', '\\,')
        block_str = glyph['unicode_block'].replace(',', '\\,')
        
        print(f"{unicode_str},{char_str},{name_str},{block_str},{base_width},{target_width}")

def get_unicode_block_name(code):
    """Unicode文字のブロック名を取得"""
    if 0x0250 <= code <= 0x02AF:
        return "IPA拡張"
    elif 0x03D0 <= code <= 0x03FF:
        return "ギリシャ記号・コプト文字"
    elif 0x1E00 <= code <= 0x1EFF:
        return "拡張ラテンB"
    elif 0x2000 <= code <= 0x206F:
        return "一般句読点"
    elif 0x20A0 <= code <= 0x20CF:
        return "通貨記号"
    elif 0x2100 <= code <= 0x214F:
        return "文字様記号"
    elif 0x2200 <= code <= 0x22FF:
        return "数学演算子"
    elif 0x2300 <= code <= 0x23FF:
        return "その他技術記号"
    elif 0x2400 <= code <= 0x243F:
        return "制御図記号"
    elif 0xFB00 <= code <= 0xFB4F:
        return "アルファベット表示形"
    else:
        return "その他"

if __name__ == '__main__':
    import sys
    
    # コマンドライン引数の処理
    base_font = 'mplus'
    target_font = 'utatane'
    base_width = 500
    target_width = 1000
    output_format = 'markdown'
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--base' and i + 1 < len(args):
            base_font = args[i + 1]
            i += 2
        elif args[i] == '--target' and i + 1 < len(args):
            target_font = args[i + 1]
            i += 2
        elif args[i] == '--pattern' and i + 2 < len(args):
            base_width = int(args[i + 1])
            target_width = int(args[i + 2])
            i += 3
        elif args[i] == '--format' and i + 1 < len(args):
            output_format = args[i + 1]
            i += 2
        elif args[i] == '--help':
            print("使用法: python generate_misclassified_glyph_list.py [オプション]")
            print("オプション:")
            print("  --base FONT           基準フォント名")
            print("  --target FONT         対象フォント名")
            print("  --pattern W1 W2       不一致パターン (基準幅 対象幅)")
            print("  --format FORMAT       出力形式 (markdown, text, csv)")
            print("  --help                このヘルプを表示")
            print()
            print("例:")
            print("  # デフォルト（M+ 500 → Utatane 1000）")
            print("  python generate_misclassified_glyph_list.py")
            print("  # Ubuntu 500 → Yasashisa 1000")
            print("  python generate_misclassified_glyph_list.py --base ubuntu --target yasashisa")
            print("  # CSV形式で出力")
            print("  python generate_misclassified_glyph_list.py --format csv")
            sys.exit(0)
        else:
            print(f"不明な引数: {args[i]}")
            print("--help で使用法を確認してください")
            sys.exit(1)
    
    generate_width_mismatch_report(base_font, target_font, (base_width, target_width), output_format)