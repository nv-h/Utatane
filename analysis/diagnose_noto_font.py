#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge
import sys

def diagnose_font(font_name: str = 'NotoSansMonoCJKjp-VF', show_sample_glyphs: bool = True, max_samples: int = 20):
    """指定されたフォントの詳細診断
    
    Args:
        font_name: 診断するフォント名
        show_sample_glyphs: サンプルグリフを表示するかどうか
        max_samples: 表示する最大サンプル数
    """
    from font_analysis_utils import create_analyzer_with_error_handling
    
    # FontAnalyzer を初期化
    analyzer = create_analyzer_with_error_handling([font_name])
    if not analyzer:
        return
    
    try:
        font = analyzer.fonts[font_name]
        font_path = analyzer.font_paths[font_name]
        
        print(f"{font_name.upper()} フォント診断")
        print("=" * 80)
        print(f"フォントパス: {font_path}")
        print(f"フォント名: {font.fontname}")
        print(f"フォント家族: {font.familyname}")
        print(f"スタイル: {font.weight}")
        print()
        
        # 基本的な情報
        print("【基本情報】")
        print(f"em単位: {font.em}")
        print(f"アセント: {font.ascent}")
        print(f"ディセント: {font.descent}")
        print()
        
        # グリフ数の詳細分析
        total_glyphs = 0
        worthoutputting_glyphs = 0
        encoded_glyphs = 0
        valid_glyphs = []
        
        for glyph in font.glyphs():
            total_glyphs += 1
            if glyph.isWorthOutputting:
                worthoutputting_glyphs += 1
                if glyph.encoding >= 0:
                    encoded_glyphs += 1
                    valid_glyphs.append(glyph)
        
        print("【グリフ統計】")
        print(f"総グリフ数: {total_glyphs}")
        print(f"有効グリフ数 (isWorthOutputting): {worthoutputting_glyphs}")
        print(f"エンコード済みグリフ数 (encoding >= 0): {encoded_glyphs}")
        print()
        
        if encoded_glyphs > 0 and show_sample_glyphs:
            print("【エンコード済みグリフの詳細】")
            print("| Index | Unicode | 文字 | 幅 | 文字名 |")
            print("|-------|---------|------|----|---------| ")
            
            # エンコード順にソート
            valid_glyphs_sorted = sorted(valid_glyphs, key=lambda g: g.encoding)
            
            for i, glyph in enumerate(valid_glyphs_sorted[:max_samples]):
                char_display = "?"
                char_name = "UNKNOWN"
                
                try:
                    if glyph.encoding < 0x10000:
                        char_display = chr(glyph.encoding)
                        import unicodedata
                        char_name = unicodedata.name(chr(glyph.encoding), "UNKNOWN")[:30]
                    else:
                        char_display = f"[U+{glyph.encoding:04X}]"
                except:
                    char_display = "[表示不可]"
                
                print(f"| {i+1:3d} | U+{glyph.encoding:04X} | {char_display} | {glyph.width} | {char_name} |")
            
            if len(valid_glyphs_sorted) > max_samples:
                print(f"| ... | ... | ... | ... | ... |")
                print(f"**他{len(valid_glyphs_sorted)-max_samples}件**")
            print()
        
        # Unicode範囲の分析
        if encoded_glyphs > 0:
            print("【Unicode範囲分析】")
            unicode_ranges = _analyze_unicode_ranges(valid_glyphs)
            
            for range_name, count in sorted(unicode_ranges.items(), key=lambda x: -x[1])[:15]:
                print(f"  {range_name}: {count}件")
            print()
        
        # 幅の分析
        if encoded_glyphs > 0:
            print("【文字幅分析】")
            width_distribution = {}
            
            for glyph in valid_glyphs:
                width = glyph.width
                if width not in width_distribution:
                    width_distribution[width] = 0
                width_distribution[width] += 1
            
            print("幅分布:")
            for width, count in sorted(width_distribution.items(), key=lambda x: -x[1])[:10]:
                print(f"  幅{width}: {count}件")
            print()
        
        print("【診断結果】")
        if encoded_glyphs == 0:
            print("❌ エンコード済みグリフが見つかりません")
            print("   - フォントが破損している可能性")
            print("   - FontForgeがこのフォントフォーマットを正しく読み込めない可能性")
        elif encoded_glyphs < 1000:
            print("⚠️  グリフ数が少なすぎます")
            print("   - サブセットフォントの可能性")
            print("   - 読み込みエラーの可能性")
        else:
            print("✅ 正常なフォントです")
        
        print(f"\n【診断サマリー】")
        print(f"フォント名: {font_name}")
        print(f"有効グリフ数: {encoded_glyphs}")
        print(f"文字幅の種類: {len(set(glyph.width for glyph in valid_glyphs))}")
        
    finally:
        analyzer.close_fonts()


def _analyze_unicode_ranges(valid_glyphs):
    """Unicode範囲の分析"""
    unicode_ranges = {}
    
    for glyph in valid_glyphs:
        code = glyph.encoding
        range_name = _get_unicode_range_name(code)
        
        if range_name not in unicode_ranges:
            unicode_ranges[range_name] = 0
        unicode_ranges[range_name] += 1
    
    return unicode_ranges


def _get_unicode_range_name(code):
    """Unicode範囲名を取得"""
    if code < 0x80:
        return "ASCII"
    elif code < 0x100:
        return "Latin-1 Supplement"
    elif code < 0x180:
        return "Latin Extended-A"
    elif code < 0x250:
        return "Latin Extended-B"
    elif code < 0x2B0:
        return "IPA Extensions"
    elif code < 0x300:
        return "Spacing Modifier Letters"
    elif code < 0x370:
        return "Combining Diacritical Marks"
    elif code < 0x400:
        return "Greek and Coptic"
    elif code < 0x500:
        return "Cyrillic"
    elif code < 0x2000:
        return "Other Latin Scripts"
    elif code < 0x2070:
        return "General Punctuation"
    elif code < 0x20D0:
        return "Superscripts and Subscripts / Currency"
    elif code < 0x2100:
        return "Combining Marks for Symbols"
    elif code < 0x2190:
        return "Letterlike Symbols"
    elif code < 0x2200:
        return "Arrows"
    elif code < 0x2300:
        return "Mathematical Operators"
    elif code < 0x2400:
        return "Miscellaneous Technical"
    elif code < 0x2440:
        return "Control Pictures"
    elif code < 0x2500:
        return "Optical Character Recognition"
    elif code < 0x2580:
        return "Box Drawing"
    elif code < 0x25A0:
        return "Block Elements"
    elif code < 0x3000:
        return "Geometric Shapes and Misc"
    elif code < 0x3040:
        return "CJK Symbols and Punctuation"
    elif code < 0x30A0:
        return "Hiragana"
    elif code < 0x3100:
        return "Katakana"
    elif code < 0x4E00:
        return "CJK Misc"
    elif code < 0xA000:
        return "CJK Ideographs"
    elif code < 0xFF00:
        return "Other CJK"
    elif code < 0xFFF0:
        return "Halfwidth and Fullwidth Forms"
    else:
        return "Other"

if __name__ == '__main__':
    import sys
    
    # コマンドライン引数の処理
    font_name = 'NotoSansMonoCJKjp-VF'
    show_samples = True
    max_samples = 20
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--font' and i + 1 < len(args):
            font_name = args[i + 1]
            i += 2
        elif args[i] == '--no-samples':
            show_samples = False
            i += 1
        elif args[i] == '--max-samples' and i + 1 < len(args):
            max_samples = int(args[i + 1])
            i += 2
        elif args[i] == '--help':
            print("使用法: python diagnose_noto_font.py [オプション]")
            print("オプション:")
            print("  --font FONT           診断するフォント名")
            print("  --no-samples          サンプルグリフを表示しない")
            print("  --max-samples N       表示する最大サンプル数")
            print("  --help                このヘルプを表示")
            sys.exit(0)
        else:
            print(f"不明な引数: {args[i]}")
            print("--help で使用法を確認してください")
            sys.exit(1)
    
    diagnose_font(font_name, show_samples, max_samples)