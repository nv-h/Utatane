#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
matplotlib を使ったフォントバージョン間比較図生成スクリプト
"""

import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np


def read_test_content(filepath):
    """テスト用テキストファイルを読み込み"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().strip().split('\n')
    except Exception as e:
        print(f"ファイル読み込みエラー: {e}")
        return []


def register_fonts():
    """フォントを登録してパスを返す"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    fonts = {
        'v1_regular': os.path.join(base_dir, "dist/v1.2.1/Utatane-Regular.ttf"),
        'v1_bold': os.path.join(base_dir, "dist/v1.2.1/Utatane-Bold.ttf"),
        'v2_regular': os.path.join(base_dir, "dist/v1.3.0/Utatane-Regular.ttf"),
        'v2_bold': os.path.join(base_dir, "dist/v1.3.0/Utatane-Bold.ttf")
    }
    
    # フォントファイル存在確認
    for name, path in fonts.items():
        if not os.path.exists(path):
            print(f"フォントファイルが見つかりません: {path}")
            return None
    
    # フォントをmatplotlibに登録
    font_props = {}
    for name, path in fonts.items():
        try:
            font_props[name] = fm.FontProperties(fname=path)
            print(f"フォント登録成功: {name}")
        except Exception as e:
            print(f"フォント登録エラー {name}: {e}")
            return None
    
    return font_props


def create_comparison_page(fig, test_lines, font_props, start_idx, lines_per_page=4):
    """比較ページを作成（縦並び表示）"""
    fig.clear()
    
    # ページ設定
    fig.suptitle('Utatane Font Version Comparison', fontsize=20, fontweight='bold', y=0.95)
    
    # 表示する行を選択
    end_idx = min(start_idx + lines_per_page, len(test_lines))
    page_lines = test_lines[start_idx:end_idx]
    
    # 各行の比較を表示
    for i, line in enumerate(page_lines):
        if not line.strip():
            continue
            
        # セクションヘッダーの処理
        if 'ローマ数字' in line:
            line = "Roman Numerals: " + line.replace('ローマ数字：', '')
        elif 'ハイフン' in line:
            line = "Hyphens and Dashes: " + line.replace('ハイフン・ダッシュ類：', '')
        elif 'ハイフン-マイナス' in line:
            continue  # 説明行はスキップ
        
        # サブプロット作成（縦並び：4行 x 1列）
        ax = fig.add_subplot(lines_per_page, 1, i + 1)
        
        # フォントサイズを大きく調整
        fontsize = 16 if len(line) < 50 else 14
        label_fontsize = 12
        
        try:
            # 縦並びで4つのバージョンを表示
            y_positions = [0.8, 0.6, 0.4, 0.2]
            
            # v1.2.1 Regular
            ax.text(0.02, y_positions[0], 'v1.2.1 Regular:', fontsize=label_fontsize, 
                   fontweight='bold', transform=ax.transAxes, color='blue')
            ax.text(0.25, y_positions[0], line, fontproperties=font_props['v1_regular'], 
                   fontsize=fontsize, transform=ax.transAxes)
            
            # v1.2.1 Bold
            ax.text(0.02, y_positions[1], 'v1.2.1 Bold:', fontsize=label_fontsize, 
                   fontweight='bold', transform=ax.transAxes, color='blue')
            ax.text(0.25, y_positions[1], line, fontproperties=font_props['v1_bold'], 
                   fontsize=fontsize, transform=ax.transAxes)
            
            # v1.3.0 Regular
            ax.text(0.02, y_positions[2], 'v1.3.0 Regular:', fontsize=label_fontsize, 
                   fontweight='bold', transform=ax.transAxes, color='red')
            ax.text(0.25, y_positions[2], line, fontproperties=font_props['v2_regular'], 
                   fontsize=fontsize, transform=ax.transAxes)
            
            # v1.3.0 Bold
            ax.text(0.02, y_positions[3], 'v1.3.0 Bold:', fontsize=label_fontsize, 
                   fontweight='bold', transform=ax.transAxes, color='red')
            ax.text(0.25, y_positions[3], line, fontproperties=font_props['v2_bold'], 
                   fontsize=fontsize, transform=ax.transAxes)
            
        except Exception as e:
            print(f"描画エラー (行 {i}): {e}")
            ax.text(0.25, 0.5, f"Error: {line[:50]}...", fontsize=12, transform=ax.transAxes)
        
        # 軸を非表示
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # 枠線を追加
        for spine in ['top', 'bottom', 'left', 'right']:
            ax.spines[spine].set_visible(True)
            ax.spines[spine].set_linewidth(1.5)
        
        # 区切り線を追加（各バージョン間）
        for y_pos in [0.75, 0.5, 0.25]:
            ax.axhline(y=y_pos, color='lightgray', linestyle='--', alpha=0.7, linewidth=0.8)
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # タイトル用のスペースを確保
    return end_idx


def create_comparison_pdf(output_path, test_lines, font_props):
    """matplotlib PDF比較文書を作成"""
    with PdfPages(output_path) as pdf:
        lines_per_page = 4  # ページあたりの行数を縦並びに合わせて減少
        
        start_idx = 0
        page_num = 1
        
        while start_idx < len(test_lines):
            print(f"ページ {page_num} を作成中... (行 {start_idx+1}-{min(start_idx+lines_per_page, len(test_lines))})")
            
            fig = plt.figure(figsize=(16, 20))  # 縦長に変更してより大きく
            
            end_idx = create_comparison_page(fig, test_lines, font_props, start_idx, lines_per_page)
            
            pdf.savefig(fig, bbox_inches='tight', dpi=200)  # DPIを上げて解像度向上
            plt.close(fig)
            
            start_idx = end_idx
            page_num += 1
    
    print(f"PDF生成完了: {output_path}")


def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    test_file = os.path.join(base_dir, "test/font_disp.txt")
    output_pdf = os.path.join(base_dir, "test/font_comparison_matplotlib.pdf")
    
    # テストファイル読み込み
    test_lines = read_test_content(test_file)
    if not test_lines:
        print("テストファイルが読み込めませんでした")
        return
    
    # 空行や不要な行をフィルタリング
    filtered_lines = []
    for line in test_lines:
        if line.strip() and not line.startswith('    '):  # インデントされた行（表ヘッダー等）をスキップ
            filtered_lines.append(line)
    
    print(f"処理対象行数: {len(filtered_lines)}")
    
    # フォント登録
    font_props = register_fonts()
    if not font_props:
        print("フォント登録に失敗しました")
        return
    
    # PDF作成
    create_comparison_pdf(output_pdf, filtered_lines, font_props)


if __name__ == "__main__":
    main()