#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import fontforge

def check_overflow(ttfpath):
    f = fontforge.open(ttfpath)
    for g in f.glyphs():
        if g.isWorthOutputting():
            bb = g.boundingBox()
            overflowX = bb[2] - bb[0]
            overflowY = bb[3] - bb[1]
            if overflowX > 1024 or overflowY > 1024:
                return False
    return True



class TestGlyphs(unittest.TestCase):
    """test glyph
    """

    def test_regular(self):
        """check_overflow for regular
        """
        actual = check_overflow('./dist/Cica-Regular.ttf')
        self.assertEqual(True, actual)

    def test_regular_italic(self):
        """check_overflow for regular
        """
        actual = check_overflow('./dist/Cica-RegularItalic.ttf')
        self.assertEqual(True, actual)

    def test_bold(self):
        """check_overflow for bold
        """
        actual = check_overflow('./dist/Cica-Bold.ttf')
        self.assertEqual(True, actual)

    def test_bold_italic(self):
        """check_overflow for bold italic
        """
        actual = check_overflow('./dist/Cica-BoldItalic.ttf')
        self.assertEqual(True, actual)

if __name__ == "__main__":
    unittest.main()
