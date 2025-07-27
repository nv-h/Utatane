#!/usr/bin/env python
# -*- coding: utf-8 -*-

def investigate_polars_box_drawing():
    """Polars等のライブラリでの罫線文字使用状況を調査"""
    
    print("DataFrame表示ライブラリでの罫線文字使用調査")
    print("=" * 60)
    
    # よく使われる罫線文字とその用途
    common_box_chars = {
        0x2500: ("─", "BOX DRAWINGS LIGHT HORIZONTAL", "水平線"),
        0x2502: ("│", "BOX DRAWINGS LIGHT VERTICAL", "垂直線"),
        0x250C: ("┌", "BOX DRAWINGS LIGHT DOWN AND RIGHT", "左上角"),
        0x2510: ("┐", "BOX DRAWINGS LIGHT DOWN AND LEFT", "右上角"),
        0x2514: ("└", "BOX DRAWINGS LIGHT UP AND RIGHT", "左下角"),
        0x2518: ("┘", "BOX DRAWINGS LIGHT UP AND LEFT", "右下角"),
        0x251C: ("├", "BOX DRAWINGS LIGHT VERTICAL AND RIGHT", "左T字"),
        0x2524: ("┤", "BOX DRAWINGS LIGHT VERTICAL AND LEFT", "右T字"),
        0x252C: ("┬", "BOX DRAWINGS LIGHT DOWN AND HORIZONTAL", "上T字"),
        0x2534: ("┴", "BOX DRAWINGS LIGHT UP AND HORIZONTAL", "下T字"),
        0x253C: ("┼", "BOX DRAWINGS LIGHT VERTICAL AND HORIZONTAL", "十字"),
    }
    
    print("【主要な罫線文字の用途】")
    for code, (char, name, usage) in common_box_chars.items():
        print(f"U+{code:04X} '{char}' {usage:<6} - {name}")
    
    print("\n【DataFrame表示での使用パターン】")
    
    # Polars風の表示例
    print("Polars DataFrameの表示例:")
    print("```")
    print("┌─────┬─────┬─────┐")
    print("│ A   │ B   │ C   │")
    print("├─────┼─────┼─────┤")
    print("│ 1   │ 2   │ 3   │")
    print("│ 4   │ 5   │ 6   │")
    print("└─────┴─────┴─────┘")
    print("```")
    
    # pandas風の表示例
    print("\npandas風の表示例:")
    print("```")
    print("     A   B   C")
    print("0    1   2   3")
    print("1    4   5   6")
    print("```")
    
    print("\n【半角vs全角の影響分析】")
    
    # 半角使用時の配置
    print("半角罫線使用時 (現在のUtatane):")
    print("文字幅500での配置:")
    print("├─────┼─────┼─────┤")
    print("│ ABC │ DEF │ GHI │  ← 各セルが半角5文字分")
    
    print("\n全角罫線使用時 (M+標準):")
    print("文字幅1000での配置:")
    print("├─────────────┼─────────────┼─────────────┤")
    print("│　ＡＢＣ　　　│　ＤＥＦ　　　│　ＧＨＩ　　　│  ← 各セルが全角幅")
    
    print("\n【実際のコンソール出力での検証が必要な項目】")
    print("1. Polarsの内部実装での罫線文字指定方法")
    print("2. ターミナルエミュレータでの文字幅認識")
    print("3. 等幅フォント前提のレイアウト計算")
    print("4. Unicode East Asian Width の影響")
    
    print("\n【Unicode East Asian Width による分類】")
    print("罫線文字のEast Asian Width:")
    
    # East Asian Width の一般的な分類
    eaw_info = {
        "─│┌┐└┘": "Ambiguous (A) - 環境により半角/全角が変わる",
        "├┤┬┴┼": "Ambiguous (A) - 環境により半角/全角が変わる", 
        "═║╔╗╚╝": "Ambiguous (A) - 環境により半角/全角が変わる",
    }
    
    for chars, classification in eaw_info.items():
        print(f"  {chars}: {classification}")
    
    print("\n【推定される問題の根本原因】")
    print("1. 罫線文字は Unicode で Ambiguous に分類されている")
    print("2. 環境によって半角/全角の扱いが異なる")
    print("3. ライブラリは特定の幅を前提としてレイアウトを計算")
    print("4. フォントの実装と環境の期待値にズレが生じる")
    
    print("\n【検証方法の提案】")
    print("A. 実際のPolarsでのDataFrame表示テスト")
    print("B. 他のTUIライブラリ (rich, textual等) での確認") 
    print("C. 様々なターミナルエミュレータでの動作確認")
    print("D. 他の等幅フォント (Nerd Fonts等) での比較")

if __name__ == '__main__':
    investigate_polars_box_drawing()