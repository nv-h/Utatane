#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
グリフ形状可視化ツール

M+、やさしさゴシック、Utataneの3フォントでグリフ形状を比較し、
境界ボックスやメトリクス情報を重ね合わせてPDF出力する。

使用方法:
    fontforge -lang=py -script glyph_shape_viewer.py [options]
"""

import fontforge
import sys
import os
import argparse
from pathlib import Path
import math

# matplotlibとPDF出力用ライブラリ
try:
    import sys
    import os
    
    # uv環境のパッケージを追加（numpy競合対策）
    venv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.venv', 'lib')
    if os.path.exists(venv_path):
        for item in os.listdir(venv_path):
            if item.startswith('python'):
                site_packages = os.path.join(venv_path, item, 'site-packages')
                if os.path.exists(site_packages):
                    # numpy系のパッケージを先に追加
                    for pkg in ['numpy', 'matplotlib', 'contourpy', 'kiwisolver', 'pillow']:
                        pkg_path = os.path.join(site_packages, pkg)
                        if os.path.exists(pkg_path) and pkg_path not in sys.path:
                            sys.path.insert(0, pkg_path)
                    
                    if site_packages not in sys.path:
                        sys.path.insert(0, site_packages)
                    break
    
    import matplotlib
    matplotlib.use('Agg')  # バックエンドをAggに設定（GUI不要）
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.patches as patches
    MATPLOTLIB_AVAILABLE = True
except ImportError as e:
    MATPLOTLIB_AVAILABLE = False
    print(f"警告: matplotlib が利用できません。エラー: {e}")
    print("以下を試してください:")
    print("  uv add matplotlib")
    print("  または pip install matplotlib")

# 判定ロジック副作用の184件グリフリスト
PROBLEMATIC_GLYPHS = {
    # IPA音標文字（14件）
    'ipa': [
        0x025D, 0x026F, 0x0270, 0x0271, 0x0276, 0x0277, 0x028D, 0x0298,
        0x02A3, 0x02A4, 0x02A5, 0x02A6, 0x02A8, 0x02A9
    ],
    
    # ギリシア記号・コプト文字（8件）
    'greek': [
        0x03D2, 0x03D3, 0x03D4, 0x03D6, 0x03D8, 0x03DA, 0x03E0, 0x03E1
    ],
    
    # 制御図記号（37件）
    'control': [
        0x2400, 0x2401, 0x2402, 0x2403, 0x2404, 0x2405, 0x2406, 0x2407,
        0x2408, 0x2409, 0x240A, 0x240B, 0x240C, 0x240D, 0x240E, 0x240F,
        0x2410, 0x2411, 0x2412, 0x2413, 0x2414, 0x2415, 0x2416, 0x2417,
        0x2418, 0x2419, 0x241A, 0x241B, 0x241C, 0x241D, 0x241E, 0x241F,
        0x2420, 0x2421, 0x2423, 0x2424, 0x2425
    ],
    
    # 通貨記号（7件）
    'currency': [
        0x20A8, 0x20A9, 0x20AA, 0x20AF, 0x20B0, 0x20B2, 0x20B3
    ],
    
    # 数学演算子（3件）
    'math': [
        0x2225, 0x2226, 0x223C
    ],
    
    # 拡張ラテンB（26件）
    'latin_ext_b': [
        0x1E3E, 0x1E3F, 0x1E40, 0x1E41, 0x1E42, 0x1E43, 0x1E88, 0x1E89,
        0x1ECC, 0x1ECE, 0x1ED0, 0x1ED2, 0x1ED4, 0x1ED6, 0x1ED8, 0x1EDA,
        0x1EDC, 0x1EDE, 0x1EE0, 0x1EE2, 0x1EE8, 0x1EEA, 0x1EEC, 0x1EEE,
        0x1EF0, 0x1EFA
    ],
    
    # その他の記号（11件）
    'misc': [
        0x203F, 0x2040, 0x2053, 0x211E, 0x2127, 0xFB00, 0xFB03, 0xFB04,
        0x23CE, 0x110150, 0x110151
    ]
}

# 高影響グリフ（32件）
HIGH_IMPACT_GLYPHS = (
    PROBLEMATIC_GLYPHS['ipa'] + 
    PROBLEMATIC_GLYPHS['greek'] + 
    PROBLEMATIC_GLYPHS['currency'] + 
    PROBLEMATIC_GLYPHS['math']
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
        bbox = (0, 0, 0, 0)
    
    # 輪郭データを取得
    contours = []
    try:
        layer = glyph.layers[glyph.activeLayer]
        for contour in layer:
            points = [(point.x, point.y) for point in contour]
            if points:
                contours.append(points)
    except:
        contours = []
    
    return {
        'unicode': unicode_val,
        'glyphname': glyph.glyphname,
        'width': glyph.width,
        'left_side_bearing': glyph.left_side_bearing,
        'right_side_bearing': glyph.right_side_bearing,
        'bbox': bbox,
        'contours': contours,
        'exists': True
    }

def draw_glyph_shape(ax, glyph_data, font_ascent, font_descent, color='black', alpha=0.7):
    """グリフ形状を描画"""
    if not glyph_data or not glyph_data['contours']:
        return
    
    # 輪郭を描画
    for contour in glyph_data['contours']:
        if len(contour) < 2:
            continue
        
        # 閉じた輪郭として描画
        xs = [p[0] for p in contour] + [contour[0][0]]
        ys = [p[1] for p in contour] + [contour[0][1]]
        
        ax.plot(xs, ys, color=color, alpha=alpha, linewidth=1.5)
        ax.fill(xs, ys, color=color, alpha=alpha*0.3)

def draw_metrics_boxes(ax, glyph_data, font_ascent, font_descent):
    """メトリクス情報のボックスを描画"""
    if not glyph_data:
        return
    
    width = glyph_data['width']
    bbox = glyph_data['bbox']
    
    # グリフ幅の矩形（薄い灰色）
    width_rect = patches.Rectangle(
        (0, -font_descent), width, font_ascent + font_descent,
        linewidth=1, edgecolor='gray', facecolor='lightgray', alpha=0.2
    )
    ax.add_patch(width_rect)
    
    # バウンディングボックス（赤い枠線）
    if bbox != (0, 0, 0, 0):
        bbox_rect = patches.Rectangle(
            (bbox[0], bbox[1]), bbox[2] - bbox[0], bbox[3] - bbox[1],
            linewidth=2, edgecolor='red', facecolor='none', alpha=0.8
        )
        ax.add_patch(bbox_rect)
    
    # ベースライン（黒い線）
    ax.axhline(y=0, color='black', linewidth=1, alpha=0.5)
    
    # アセントライン（点線）
    ax.axhline(y=font_ascent, color='blue', linewidth=1, linestyle='--', alpha=0.5)
    
    # ディセントライン（点線）
    ax.axhline(y=-font_descent, color='blue', linewidth=1, linestyle='--', alpha=0.5)

def create_glyph_comparison_plot(fonts_data, glyph_list, output_pdf=None):
    """グリフ比較プロットを作成"""
    if not MATPLOTLIB_AVAILABLE:
        print("matplotlib が利用できないため、PDF出力をスキップします。")
        return False
    
    # フォント名とカラーマップ
    font_colors = {
        'mplus': 'blue',
        'yasashisa': 'green', 
        'utatane': 'red'
    }
    
    font_names = {
        'mplus': 'M+ 1m Regular',
        'yasashisa': 'やさしさゴシック Bold V2',
        'utatane': 'Utatane Regular'
    }
    
    # PDF出力の準備
    if output_pdf:
        pdf_pages = PdfPages(output_pdf)
    
    # グリフごとに比較ページを作成
    for i, unicode_val in enumerate(glyph_list):
        if unicode_val is None:
            continue
            
        # 3x1のサブプロット作成
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle(f'グリフ比較: U+{unicode_val:04X} ({chr(unicode_val)})', fontsize=16)
        
        # 各フォントのデータを取得・描画
        all_glyph_data = {}
        font_metrics = {}
        
        for j, (font_key, font) in enumerate(fonts_data.items()):
            if font is None:
                continue
                
            ax = axes[j]
            glyph_data = get_glyph_data(font, unicode_val)
            all_glyph_data[font_key] = glyph_data
            
            # フォントメトリクス
            font_metrics[font_key] = {
                'ascent': font.ascent,
                'descent': font.descent
            }
            
            if glyph_data:
                # グリフ形状を描画
                draw_glyph_shape(ax, glyph_data, font.ascent, font.descent, 
                               font_colors[font_key])
                
                # メトリクスボックスを描画
                draw_metrics_boxes(ax, glyph_data, font.ascent, font.descent)
                
                # タイトルと情報
                ax.set_title(f'{font_names[font_key]}\n'
                           f'幅: {glyph_data["width"]}, LSB: {glyph_data["left_side_bearing"]:.0f}')
                
                # 軸設定
                width = glyph_data['width']
                margin = width * 0.1
                ax.set_xlim(-margin, width + margin)
                ax.set_ylim(-font.descent - 50, font.ascent + 50)
                
            else:
                ax.set_title(f'{font_names[font_key]}\n（グリフなし）')
                ax.set_xlim(-100, 600)
                ax.set_ylim(-250, 850)
            
            ax.grid(True, alpha=0.3)
            ax.set_aspect('equal')
        
        # レイアウト調整
        plt.tight_layout()
        
        if output_pdf:
            pdf_pages.savefig(fig, dpi=150)
        else:
            plt.show()
        
        plt.close(fig)
        
        # プログレス表示
        if (i + 1) % 10 == 0:
            print(f"進捗: {i + 1}/{len(glyph_list)} グリフ処理完了")
    
    if output_pdf:
        pdf_pages.close()
        print(f"PDF出力完了: {output_pdf}")
    
    return True

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
    
    # カテゴリ選択
    if args.category:
        for cat in args.category:
            if cat in PROBLEMATIC_GLYPHS:
                selected_glyphs.update(PROBLEMATIC_GLYPHS[cat])
            else:
                print(f"警告: 不明なカテゴリ '{cat}' をスキップ")
    
    # 優先度選択
    if args.priority == 'high':
        selected_glyphs.update(HIGH_IMPACT_GLYPHS)
    elif args.priority == 'all':
        for cat_glyphs in PROBLEMATIC_GLYPHS.values():
            selected_glyphs.update(cat_glyphs)
    
    # テストファイル選択
    if args.from_testfile:
        test_chars = read_test_file_chars(args.test_file, args.section)
        selected_glyphs.update(test_chars)
    
    # 個別Unicode指定
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
    
    # 文字直接指定
    if args.chars:
        for char in args.chars:
            selected_glyphs.add(ord(char))
    
    # デフォルト：高影響グリフ
    if not selected_glyphs:
        selected_glyphs.update(HIGH_IMPACT_GLYPHS)
    
    return sorted(selected_glyphs)

def main():
    parser = argparse.ArgumentParser(
        description='グリフ形状可視化ツール - M+、やさしさゴシック、Utataneの3フォント比較',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 高影響グリフ（デフォルト）
  fontforge -lang=py -script glyph_shape_viewer.py

  # 制御図記号のみ
  fontforge -lang=py -script glyph_shape_viewer.py --category control

  # 特定のUnicode文字
  fontforge -lang=py -script glyph_shape_viewer.py --unicode U+2400 U+20A9

  # テストファイルの罫線セクション
  fontforge -lang=py -script glyph_shape_viewer.py --from-testfile --section 罫線

  # カスタムフォント指定
  fontforge -lang=py -script glyph_shape_viewer.py --mplus custom.ttf
        """
    )
    
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
    parser.add_argument('--output', '-o', help='PDF出力ファイル名')
    parser.add_argument('--list-categories', action='store_true',
                       help='利用可能なカテゴリ一覧表示')
    
    args = parser.parse_args()
    
    # カテゴリ一覧表示
    if args.list_categories:
        print("利用可能なカテゴリ:")
        for cat, glyphs in PROBLEMATIC_GLYPHS.items():
            print(f"  {cat:12} : {len(glyphs):2}件 - {', '.join([f'U+{g:04X}' for g in glyphs[:5]])}{'...' if len(glyphs) > 5 else ''}")
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
        print("エラー: 比較するグリフが選択されていません")
        return 1
    
    print(f"\n比較対象グリフ: {len(selected_glyphs)}件")
    print(f"最初の10件: {', '.join([f'U+{g:04X}' for g in selected_glyphs[:10]])}")
    
    # 出力ファイル名決定
    if not args.output:
        args.output = f"glyph_comparison_{len(selected_glyphs)}glyphs.pdf"
    
    # 比較プロット作成
    success = create_glyph_comparison_plot(fonts_data, selected_glyphs, args.output)
    
    # フォントクローズ
    for font in fonts_data.values():
        if font:
            font.close()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())