#!/usr/bin/env python
"""生成済みフォント（dist/）のグリフを検査する。

FontForge の Python で実行する:
    fontforge -lang=py -script test/test_glyphs.py
"""

import unittest
from pathlib import Path

import fontforge

DIST = Path(__file__).resolve().parents[1] / "dist"
FONT_FILES = ("Utatane-Regular.ttf", "Utatane-Bold.ttf")
ALLOWED_ADVANCES = {0, 500, 1000}


def encoded_glyphs(font):
    return [g for g in font.glyphs() if g.unicode >= 0 and g.isWorthOutputting()]


def describe(glyph, detail):
    return f"U+{glyph.unicode:04X} {glyph.glyphname}: {detail}"


class TestGlyphs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fonts = {}
        for name in FONT_FILES:
            path = DIST / name
            if not path.is_file():
                raise unittest.SkipTest(
                    f"{path} がありません。先に utatane.py でフォントを生成してください"
                )
            cls.fonts[name] = fontforge.open(str(path))

    @classmethod
    def tearDownClass(cls):
        for font in cls.fonts.values():
            font.close()

    def test_advance_widths(self):
        """送り幅は 0（結合記号）・500（半角）・1000（全角）のいずれか"""
        for name, font in self.fonts.items():
            with self.subTest(font=name):
                wrong = [
                    describe(g, g.width)
                    for g in encoded_glyphs(font)
                    if g.width not in ALLOWED_ADVANCES
                ]
                self.assertEqual([], wrong)

    def test_within_win_metrics(self):
        """輪郭が usWinAscent / usWinDescent の範囲に収まる（Windows の GDI で欠けない）

        --no-fit-win-metrics で生成したフォントでは失敗する。
        """
        for name, font in self.fonts.items():
            with self.subTest(font=name):
                top, bottom = font.os2_winascent, font.os2_windescent
                outside = []
                for g in encoded_glyphs(font):
                    _, y_min, _, y_max = g.boundingBox()
                    if y_max > top or y_min < -bottom:
                        outside.append(describe(g, f"{y_min:.0f}〜{y_max:.0f}"))
                self.assertEqual([], outside)

    @unittest.expectedFailure
    def test_outline_within_two_cells(self):
        """輪郭の幅が全角（1000）に収まる

        既知の不具合として失敗する: ‱ ∭ ∰ ⨌ は幅が1000を超える。
        直したら expectedFailure を外す。
        """
        for name, font in self.fonts.items():
            with self.subTest(font=name):
                too_wide = []
                for g in encoded_glyphs(font):
                    x_min, _, x_max, _ = g.boundingBox()
                    if x_max - x_min > font.em:
                        too_wide.append(describe(g, f"{x_max - x_min:.0f}"))
                self.assertEqual([], too_wide)


if __name__ == "__main__":
    unittest.main()
