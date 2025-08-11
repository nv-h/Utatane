#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
グリフ可視化ツール

JSONファイルから読み込んだグリフデータを用いて、
3フォント比較のPDFを生成する。
"""

import json
import sys
import argparse
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.patches as patches
    import matplotlib.font_manager as fm
    MATPLOTLIB_AVAILABLE = True
    
    # Utataneフォントを日本語表示用に設定
    def setup_japanese_font():
        try:
            utatane_font_path = Path(__file__).parent.parent / 'dist' / 'Utatane-Regular.ttf'
            if utatane_font_path.exists():
                # Utataneフォントを登録し、フォント名を取得
                font_prop = fm.FontProperties(fname=str(utatane_font_path))
                font_name = font_prop.get_name()
                
                # matplotlib フォントマネージャーに追加
                fm.fontManager.addfont(str(utatane_font_path))
                
                # フォントファミリを設定（実際のフォント名を使用）
                available_fonts = [font_name, 'DejaVu Sans', 'sans-serif']
                plt.rcParams['font.family'] = available_fonts
                plt.rcParams['font.sans-serif'] = available_fonts
                
                print(f"日本語フォントを設定: {utatane_font_path} (フォント名: {font_name})")
                return font_name
            else:
                print("警告: Utataneフォントが見つかりません。デフォルトフォントを使用します。")
                return None
        except Exception as e:
            print(f"警告: フォント設定でエラーが発生: {e}。デフォルトフォントを使用します。")
            return None
    
    # フォント設定を実行
    JAPANESE_FONT_AVAILABLE = setup_japanese_font()
    
    # フォントファミリを取得する関数
    def get_font_family():
        if JAPANESE_FONT_AVAILABLE:
            return [JAPANESE_FONT_AVAILABLE, 'DejaVu Sans', 'sans-serif']
        else:
            return ['DejaVu Sans', 'sans-serif']
    
except ImportError as e:
    MATPLOTLIB_AVAILABLE = False
    print(f"エラー: matplotlib が利用できません: {e}")
    sys.exit(1)

def draw_glyph_shape(ax, glyph_data, font_ascent, font_descent, color='black', alpha=0.7):
    """グリフ形状を描画"""
    if not glyph_data or not glyph_data.get('contours'):
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
    if bbox != [0, 0, 0, 0]:
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

def create_glyph_comparison_plot(data, output_pdf):
    """グリフ比較プロットを作成"""
    # フォント名とカラーマップ
    font_colors = {
        'mplus': 'blue',
        'yasashisa': 'green', 
        'utatane': 'red'
    }
    
    font_display_names = {
        'mplus': 'M+ 1m Regular',
        'yasashisa': 'やさしさゴシック Bold V2',
        'utatane': 'Utatane Regular'
    }
    
    glyph_list = data['metadata']['glyph_list']
    fonts_data = data['fonts']
    
    # PDF出力の準備
    with PdfPages(output_pdf) as pdf_pages:
        # グリフごとに比較ページを作成
        for i, unicode_val in enumerate(glyph_list):
            unicode_str = str(unicode_val)
            
            # 3x1のサブプロット作成
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            try:
                char_display = chr(unicode_val)
            except ValueError:
                char_display = f'[U+{unicode_val:04X}]'
            
            fig.suptitle(f'グリフ比較: U+{unicode_val:04X} ({char_display})', fontsize=16, 
                        fontfamily=get_font_family())
            
            # 各フォントのデータを取得・描画
            for j, font_key in enumerate(['mplus', 'yasashisa', 'utatane']):
                if j >= len(axes) or font_key not in fonts_data:
                    continue
                
                ax = axes[j]
                font_data = fonts_data[font_key]
                glyph_data = font_data['glyphs'].get(unicode_str)
                
                font_ascent = font_data['ascent']
                font_descent = font_data['descent']
                
                if glyph_data:
                    # グリフ形状を描画
                    draw_glyph_shape(ax, glyph_data, font_ascent, font_descent, 
                                   font_colors[font_key])
                    
                    # メトリクスボックスを描画
                    draw_metrics_boxes(ax, glyph_data, font_ascent, font_descent)
                    
                    # タイトルと情報（グリフ名を追加）
                    glyph_name = glyph_data.get('glyphname', 'Unknown')
                    ax.set_title(f'{font_display_names[font_key]}\n'
                               f'幅: {glyph_data["width"]:.0f}, LSB: {glyph_data["left_side_bearing"]:.0f}\n'
                               f'グリフ名: {glyph_name}',
                               fontfamily=get_font_family(), fontsize=10)
                    
                    # 軸設定
                    width = glyph_data['width']
                    margin = width * 0.1 if width > 0 else 50
                    ax.set_xlim(-margin, width + margin)
                    ax.set_ylim(-font_descent - 50, font_ascent + 50)
                    
                else:
                    ax.set_title(f'{font_display_names[font_key]}\n（グリフなし）',
                               fontfamily=get_font_family())
                    ax.set_xlim(-100, 600)
                    ax.set_ylim(-250, 850)
                
                ax.grid(True, alpha=0.3)
                ax.set_aspect('equal')
            
            # レイアウト調整
            plt.tight_layout()
            pdf_pages.savefig(fig, dpi=150)
            plt.close(fig)
            
            # プログレス表示
            if (i + 1) % 10 == 0:
                print(f"進捗: {i + 1}/{len(glyph_list)} グリフ処理完了")
    
    print(f"PDF出力完了: {output_pdf}")
    return True

def main():
    parser = argparse.ArgumentParser(description='グリフ可視化ツール')
    parser.add_argument('json_file', help='グリフデータJSONファイル')
    parser.add_argument('--output', '-o', help='PDF出力ファイル名')
    
    args = parser.parse_args()
    
    # JSONファイル読み込み
    if not Path(args.json_file).exists():
        print(f"エラー: JSONファイルが見つかりません: {args.json_file}")
        return 1
    
    try:
        with open(args.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"エラー: JSONファイル読み込み失敗: {e}")
        return 1
    
    # 出力ファイル名決定
    if not args.output:
        json_stem = Path(args.json_file).stem
        args.output = f"{json_stem}_comparison.pdf"
    
    # グリフ比較プロット作成
    print(f"グリフ可視化開始: {len(data['metadata']['glyph_list'])}件のグリフ")
    success = create_glyph_comparison_plot(data, args.output)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())