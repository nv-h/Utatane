#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指定のコードポイント群について、各フォント（M+, やさしさ, Utatane v1.3.1, Noto Sans Mono CJK jp VF）の文字幅を収集し、
Markdownテーブルとして出力する補助スクリプト。

実行方法（プロジェクトルートで）:
  ./fontforge/build/bin/fontforge -lang=py -script analysis/collect_widths_for_doc.py
"""

import sys
import os

try:
    import fontforge
except ImportError:
    print("このスクリプトはFontForge環境で実行してください")
    sys.exit(1)


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FONTS = {
    "M+": os.path.join(ROOT, "sourceFonts/mplus-1m-regular.ttf"),
    "Yasashisa": os.path.join(ROOT, "sourceFonts/YasashisaGothicBold-V2_-30.ttf"),
    "v1.3.1": os.path.join(ROOT, "dist/v1.3.1/Utatane-Regular.ttf"),
    "Noto VF": os.path.join(ROOT, "dist/NotoSansMonoCJKjp-VF.ttf"),
    "M+Code": os.path.join(ROOT, "dist/MPLUS1Code-Regular.ttf"),
}


def open_fonts():
    opened = {}
    for name, path in FONTS.items():
        if not os.path.exists(path):
            print(f"✗ フォントが見つかりません: {name} -> {path}")
            sys.exit(2)
        try:
            opened[name] = fontforge.open(path)
            print(f"✓ {name} 読み込み: {path}")
        except Exception as e:
            print(f"✗ {name} の読み込みに失敗: {path}\n  {e}")
            sys.exit(3)
    return opened


def get_width(font, codepoint):
    try:
        if codepoint in font and font[codepoint].isWorthOutputting:
            return font[codepoint].width
    except Exception:
        return None
    return None


def fmt_char(codepoint):
    try:
        if 0 <= codepoint <= 0x10FFFF:
            return chr(codepoint) if codepoint <= 0xFFFF else f"[U+{codepoint:05X}]"
    except Exception:
        pass
    return "[?]"


def print_table(title, codepoints):
    print(f"\n### {title}")
    headers = ["Unicode", "文字"] + list(FONTS.keys())
    print("| " + " | ".join(headers) + " |")
    print("|" + "-|-".join(["-" for _ in headers]) + "|")
    for cp in codepoints:
        row = [f"U+{cp:04X}", fmt_char(cp)]
        for name in FONTS.keys():
            w = get_width(FONTS_OPENED[name], cp)
            row.append("-" if w is None else str(w))
        print("| " + " | ".join(row) + " |")


def main():
    global FONTS_OPENED
    FONTS_OPENED = open_fonts()

    # 1) IPA拡張（14件）
    ipa = [
        0x025D, 0x026F, 0x0270, 0x0271, 0x0276, 0x0277, 0x028D,
        0x0298, 0x02A3, 0x02A4, 0x02A5, 0x02A6, 0x02A8, 0x02A9,
    ]

    # 2) ギリシャ記号・コプト文字（8件）
    greek = [0x03D2, 0x03D3, 0x03D4, 0x03D6, 0x03D8, 0x03DA, 0x03E0, 0x03E1]

    # 3) 制御図記号（37件）
    control_pictures = [
        0x2400, 0x2401, 0x2402, 0x2403, 0x2404, 0x2405, 0x2406, 0x2407,
        0x2408, 0x2409, 0x240A, 0x240B, 0x240C, 0x240D, 0x240E, 0x240F,
        0x2410, 0x2411, 0x2412, 0x2413, 0x2414, 0x2415, 0x2416, 0x2417,
        0x2418, 0x2419, 0x241A, 0x241B, 0x241C, 0x241D, 0x241E, 0x241F,
        0x2420, 0x2421, 0x2423, 0x2424, 0x2425,
    ]

    # 4) 通貨記号（7件）
    currency = [0x20A8, 0x20A9, 0x20AA, 0x20AF, 0x20B0, 0x20B2, 0x20B3]

    # 5) 数学演算子（3件）
    math_ops = [0x2225, 0x2226, 0x223C]

    # 6) 拡張ラテンB（26件）
    latin_ext_b = [
        0x1E3E, 0x1E3F, 0x1E40, 0x1E41, 0x1E42, 0x1E43,
        0x1E88, 0x1E89,
        0x1ECC, 0x1ECE, 0x1ED0, 0x1ED2, 0x1ED4, 0x1ED6, 0x1ED8,
        0x1EDA, 0x1EDC, 0x1EDE, 0x1EE0, 0x1EE2,
        0x1EE8, 0x1EEA, 0x1EEC, 0x1EEE, 0x1EF0,
        0x1EFA,
    ]

    # 7) その他の記号（11件）: テーブルの代表例が実際に全件
    others = [
        # 一般句読点 3件
        0x203F, 0x2040, 0x2053,  # ‿ ⁀ ⁓
        # 文字様記号 2件
        0x211E, 0x2127,         # ℞ ℧
        # アルファベット表示形 3件
        0xFB00, 0xFB03, 0xFB04, # ﬀ ﬃ ﬄ
        # その他技術記号 1件
        0x23CE,                 # ⏎
        # 不明グリフ 2件（仕様上存在しない可能性が高い）
        0x110150, 0x110151,     # [U+110150] [U+110151]
    ]

    print("\n===== 幅収集結果 (Markdown) =====\n")
    print_table("IPA拡張（14件）", ipa)
    print_table("ギリシャ記号・コプト文字（8件）", greek)
    print_table("制御図記号（37件）", control_pictures)
    print_table("通貨記号（7件）", currency)
    print_table("数学演算子（3件）", math_ops)
    print_table("拡張ラテンB（26件）", latin_ext_b)
    print_table("その他の記号（11件）", others)

    # 後始末
    for f in FONTS_OPENED.values():
        try:
            f.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
