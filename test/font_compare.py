#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
フォント比較統一スクリプト
FontForgeベースの比較とmatplotlibベースの比較を統合
"""

import os
import sys
import argparse
import subprocess
import glob
from pathlib import Path


def find_available_fonts():
    """利用可能なフォントファイルを検索"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    patterns = [
        "dist/*.ttf",
        "dist/*/*.ttf", 
        "sourceFonts/*.ttf"
    ]
    
    fonts = {}
    for pattern in patterns:
        for font_path in glob.glob(os.path.join(base_dir, pattern)):
            rel_path = os.path.relpath(font_path, base_dir)
            font_name = os.path.splitext(os.path.basename(font_path))[0]
            
            # バージョン情報を含む場合
            dir_name = os.path.dirname(rel_path)
            if dir_name and dir_name != 'dist' and dir_name != 'sourceFonts':
                key = f"{os.path.basename(dir_name)}_{font_name}"
            else:
                key = font_name
                
            fonts[key] = rel_path
    
    return fonts


def get_fontforge_command():
    """FontForgeコマンドのパスを取得"""
    candidates = [
        "../fontforge/build/bin/fontforge",
        "fontforge",
        "C:\\Program Files (x86)\\FontForgeBuilds\\bin\\fontforge.exe"
    ]
    
    for cmd in candidates:
        try:
            if os.path.exists(cmd):
                return cmd
            # システムPATH上を確認
            result = subprocess.run(['which', cmd], capture_output=True, text=True)
            if result.returncode == 0:
                return cmd.strip()
        except:
            continue
    
    return None


def run_fontforge_comparison(args, fontforge_cmd):
    """FontForgeベースの比較を実行"""
    cmd = [
        fontforge_cmd, '-lang=py', '-script', 
        './test/compare_fonts_fontforge.py',
        '-f1', args.font1,
        '-f2', args.font2,
        '-t', args.test_file
    ]
    
    if args.visual:
        cmd.append('--visual')
    
    if args.output:
        cmd.extend(['-o', args.output])
    
    return subprocess.run(cmd)


def run_matplotlib_comparison(args):
    """matplotlib (uv) ベースの比較を実行"""
    current_dir = os.getcwd()
    pdf_dir = os.path.join(current_dir, 'pdf-comparison')
    
    if not os.path.exists(pdf_dir):
        print("pdf-comparisonディレクトリが見つかりません")
        return 1
    
    try:
        os.chdir(pdf_dir)
        cmd = ['uv', 'run', 'compare_fonts_matplotlib.py']
        result = subprocess.run(cmd)
        return result.returncode
    finally:
        os.chdir(current_dir)


def main():
    parser = argparse.ArgumentParser(description='フォント比較統一ツール')
    parser.add_argument('--list-fonts', action='store_true',
                        help='利用可能なフォントを一覧表示')
    parser.add_argument('--method', choices=['fontforge', 'matplotlib', 'both'], 
                        default='fontforge', help='比較方法')
    parser.add_argument('--font1', '-f1', help='比較元フォント')
    parser.add_argument('--font2', '-f2', help='比較先フォント')
    parser.add_argument('--test-file', '-t', default='test/font_disp.txt',
                        help='テスト文字列ファイル')
    parser.add_argument('--output', '-o', help='結果をファイルに出力')
    parser.add_argument('--visual', '-v', action='store_true',
                        help='文字幅を視覚的なバーで表示')
    
    args = parser.parse_args()
    
    # フォント一覧表示
    if args.list_fonts:
        fonts = find_available_fonts()
        print("利用可能なフォント:")
        for key, path in sorted(fonts.items()):
            print(f"  {key:<30} : {path}")
        return 0
    
    # FontForgeコマンド確認
    fontforge_cmd = get_fontforge_command()
    if not fontforge_cmd and args.method in ['fontforge', 'both']:
        print("FontForgeが見つかりません。以下をインストール/設定してください:")
        print("- 標準パッケージ: sudo apt install fontforge")
        print("- カスタムビルド: ../fontforge/build/bin/fontforge")
        if args.method == 'fontforge':
            return 1
    
    # フォント選択のデフォルト設定と名前解決
    fonts = find_available_fonts()
    
    # フォント名が指定されている場合、パスに変換
    if args.font1 and args.font1 in fonts:
        args.font1 = fonts[args.font1]
    if args.font2 and args.font2 in fonts:
        args.font2 = fonts[args.font2]
    
    # デフォルト設定
    if not args.font1:
        # 現在のフォントを優先
        if 'Utatane-Regular' in fonts:
            args.font1 = fonts['Utatane-Regular']
        else:
            args.font1 = list(fonts.values())[0] if fonts else 'dist/Utatane-Regular.ttf'
    
    if not args.font2:
        # v1.3.0を優先
        candidates = ['v1.3.0_Utatane-Regular', 'v1.2.1_Utatane-Regular']
        for candidate in candidates:
            if candidate in fonts:
                args.font2 = fonts[candidate]
                break
        else:
            # フォールバック
            args.font2 = list(fonts.values())[1] if len(fonts) > 1 else 'dist/v1.3.0/Utatane-Regular.ttf'
    
    print(f"比較方法: {args.method}")
    print(f"フォント1: {args.font1}")
    print(f"フォント2: {args.font2}")
    
    # 比較実行
    if args.method == 'fontforge':
        result = run_fontforge_comparison(args, fontforge_cmd)
        return result.returncode
    
    elif args.method == 'matplotlib':
        return run_matplotlib_comparison(args)
    
    elif args.method == 'both':
        print("\n=== FontForge比較 ===")
        fontforge_result = run_fontforge_comparison(args, fontforge_cmd)
        
        print("\n=== matplotlib比較 (PDF生成) ===")
        matplotlib_result = run_matplotlib_comparison(args)
        
        return max(fontforge_result.returncode, matplotlib_result)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())