#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fontforge
import psMat
import os
import sys
import math
from logging import getLogger, StreamHandler, Formatter, DEBUG

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
formatter = Formatter('%(asctime)s [%(levelname)s] : %(message)s')
handler.setFormatter(formatter)
logger.setLevel(DEBUG)
logger.addHandler(handler)

# Ubuntu Mono
# 800 x 200 = 1000(Em)
# Win(Ascent, Descent)=(-170, -183)
# hhea(height, width)=(-170, 183)

# 01FLOPDESIGN
# 880 x 120 = 1000(Em)
# Win(Ascent, Descent)=(-3, -22)
# hhea(height, width)=(-3, 110)

WIDTH   = 1000
ASCENT  = 880
DESCENT = 200

SOURCE = './sourceFonts'
DIST = './dist'
LICENSE = open('./LICENSE.txt').read()
COPYRIGHT = open('./COPYRIGHT.txt').read()
VERSION = '1.0.0'

fonts = [
    {
         'family': 'Fusa',
         'name': 'Fusa',
         'filename': 'Fusa.ttf',
         'weight': 400,
         'weight_name': 'Regular',
         'style_name': 'Regular',
         'ubuntu_mono': 'UbuntuMono-R.ttf',
         'japanese': 'FLOPDesignFont.ttf',
         'ubuntu_weight_reduce': 0,
         'japanese_weight_add': 0,
         'italic': False,
    # boldは未対応
    # }, {
    #     'family': 'Fusa',
    #     'name': 'Fusa-Bold',
    #     'filename': 'Fusa-Bold.ttf',
    #     'weight': 700,
    #     'weight_name': 'Bold',
    #     'style_name': 'Bold',
    #     'ubuntu_mono': 'UbuntuMono-B.ttf',
    #     'japanese': '07YasashisaGothic-B.ttf',
    #     'ubuntu_weight_reduce': 0,
    #     'japanese_weight_add': 0,
    #     'italic': False,
    }
]

def log(str):
    logger.debug(str)

def remove_glyph_from_ubuntu(_font):
    u"""japaneseを採用したいグリフをUbuntuMonoから削除
    """
    log('remove_ambiguous() : %s' % _font.fontname)

    glyphs = [
            0x2026, # …
            ]

    for g in glyphs:
        _font.selection.select(g)
        _font.clear()

    return _font


def check_files():
    err = 0
    for f in fonts:
        if not os.path.isfile(SOURCE + '/%s' % f.get('ubuntu_mono')):
            logger.error('%s not exists.' % f)
            err = 1

        if not os.path.isfile(SOURCE + '/%s' % f.get('japanese')):
            logger.error('%s not exists.' % f)
            err = 1

    if err > 0:
        sys.exit(err)

def modify_usfont():
    pass

def modify_jpfont():
    pass

def set_os2_values(_font, _info):
    weight = _info.get('weight')
    _font.os2_weight = weight
    _font.os2_width = 5
    _font.os2_fstype = 0
    _font.os2_vendor = 'HSAI'
    _font.os2_version = 1
    _font.os2_winascent = ASCENT
    _font.os2_winascent_add = False
    _font.os2_windescent = DESCENT
    _font.os2_windescent_add = False
    _font.os2_typoascent = ASCENT
    _font.os2_typoascent_add = False
    _font.os2_typodescent = -DESCENT
    _font.os2_typodescent_add = False
    _font.os2_typolinegap = 0
    _font.hhea_ascent = ASCENT
    _font.hhea_ascent_add = False
    _font.hhea_descent = -DESCENT
    _font.hhea_descent_add = False
    _font.hhea_linegap = 0
    _font.os2_panose = (2, 11, weight/100, 9, 2, 2, 3, 2, 2, 7)
    return _font

def align_to_center(_g):
    width = 0

    if _g.width > 700:
        width = WIDTH
    else:
        width = WIDTH/2

    _g.width = width
    _g.left_side_bearing = _g.right_side_bearing = (_g.left_side_bearing + _g.right_side_bearing)/2
    _g.width = width

    return _g

def align_to_left(_g):
    width = _g.width
    _g.left_side_bearing = 0
    _g.width = width

def align_to_right(_g):
    width = _g.width
    bb = _g.boundingBox()
    left = width - (bb[2] - bb[0])
    _g.left_side_bearing = left
    _g.width = width

def vertical_line_to_broken_bar(_f):
    _f.selection.select(0x00a6)
    _f.copy()
    _f.selection.select(0x007c)
    _f.paste()
    return _f

def emdash_to_broken_dash(_f):
    _f.selection.select(0x006c)
    _f.copy()
    _f.selection.select(0x2014)
    _f.pasteInto()
    _f.intersect()
    return _f

def mathglyph_to_double(_f):
    pass

def zenkaku_space(_f):
    _f.selection.select(0x2610)
    _f.copy()
    _f.selection.select(0x3000)
    _f.paste()
    _f.selection.select(0x271a)
    _f.copy()
    _f.selection.select(0x3000)
    _f.pasteInto()
    _f.intersect()
    for g in _f.selection.byGlyphs:
        g = align_to_center(g)
    return _f

def add_smalltriangle(_f):
    _f.selection.select(0x25bc)
    _f.copy()
    _f.selection.select(0x25be)
    _f.paste()
    _f.transform(psMat.compose(psMat.scale(0.64), psMat.translate(0, 68)))
    _f.copy()
    _f.selection.select(0x25b8)
    _f.paste()
    _f.transform(psMat.rotate(math.radians(90)))

    for g in _f.glyphs():
        if g.encoding == 0x25be or g.encoding == 0x25b8:
            g.width = WIDTH/2
            g = align_to_center(g)

    return _f

def fix_box_drawings(_f):
    left = [
        0x2510, 0x2518, 0x2524, 0x2555, 0x2556, 0x2557, 0x255b, 0x255c, 0x255d,
        0x2561, 0x2562, 0x2563,
    ]
    right = [
        0x250c, 0x2514, 0x251c, 0x2552, 0x2553, 0x2554, 0x2558, 0x2559, 0x255a,
        0x255e, 0x255f, 0x2560,
    ]

    for g in _f.glyphs():
        if g.encoding < 0x2500 or g.encoding > 0x256c:
            continue
        if g.encoding in left:
            align_to_left(g)
        elif g.encoding in right:
            align_to_right(g)

    return _f


def build_font(_f):
    log('Generating %s ...' % _f.get('weight_name'))
    ubuntu = fontforge.open(SOURCE + '/%s' % _f.get('ubuntu_mono'))
    ubuntu = remove_glyph_from_ubuntu(ubuntu)
    cica = fontforge.open(SOURCE + '/%s' % _f.get('japanese'))
    # nerd = fontforge.open(SOURCE + '/nerd.ttf')

    for g in ubuntu.glyphs():
        if _f.get('ubuntu_weight_reduce') != 0:
            # g.changeWeight(_f.get('ubuntu_weight_reduce'), 'auto', 0, 0, 'auto')
            g.stroke("circular", _f.get('ubuntu_weight_reduce'), 'butt', 'round', 'removeexternal')
        g = align_to_center(g)


    alternate_expands = [
        0x306e,
    ]

    if _f.get('japanese_weight_add') != 0:
        for g in cica.glyphs():
            # g.changeWeight(_f.get('japanese_weight_add'), 'auto', 0, 0, 'auto')
            g.stroke("caligraphic", _f.get('japanese_weight_add'), _f.get('japanese_weight_add'), 45, 'removeinternal')
            # g.stroke("circular", _f.get('japanese_weight_add'), 'butt', 'round', 'removeinternal')


    ignoring_center = [
        0x3001, 0x3002, 0x3008, 0x3009, 0x300a, 0x300b, 0x300c, 0x300d,
        0x300e, 0x300f, 0x3010, 0x3011, 0x3014, 0x3015, 0x3016, 0x3017,
        0x3018, 0x3019, 0x301a, 0x301b, 0x301d, 0x301e, 0x3099, 0x309a,
        0x309b, 0x309c,
    ]
    for g in cica.glyphs():
        g.transform((0.91,0,0,0.91,0,0))
        if _f.get('italic'):
            g.transform(psMat.skew(0.25))
        if g.encoding in ignoring_center:
            pass
        else:
            g = align_to_center(g)

    for g in ubuntu.glyphs():
        if  g.isWorthOutputting:
            if _f.get('italic'):
                g.transform(psMat.skew(0.25))
            if g.encoding >= 0x2500 and g.encoding <= 0x25af:
                g.transform(psMat.compose(psMat.scale(1.024, 1.024), psMat.translate(0, -30)))
                g = align_to_center(g)
            ubuntu.selection.select(g.encoding)
            ubuntu.copy()
            try:
                cica.selection.select(g.encoding)
                cica.paste()
            except ValueError:
                print "ValueError!"

    cica = fix_box_drawings(cica)
    cica = zenkaku_space(cica)
    # cica = vertical_line_to_broken_bar(cica)
    cica = emdash_to_broken_dash(cica)
    # cica = add_notoemoji(cica)
    # cica = add_smalltriangle(cica)

    cica.ascent = ASCENT
    cica.descent = DESCENT
    cica.upos = 45
    cica.fontname = _f.get('family')
    cica.familyname = _f.get('family')
    cica.fullname = _f.get('name')
    cica.weight = _f.get('weight_name')
    cica = set_os2_values(cica, _f)
    cica.appendSFNTName(0x411,0, COPYRIGHT)
    cica.appendSFNTName(0x411,1, _f.get('family'))
    cica.appendSFNTName(0x411,2, _f.get('style_name'))
    # cica.appendSFNTName(0x411,3, "")
    cica.appendSFNTName(0x411,4, _f.get('name'))
    cica.appendSFNTName(0x411,5, "Version " + VERSION)
    cica.appendSFNTName(0x411,6, _f.get('family') + "-" + _f.get('weight_name'))
    # cica.appendSFNTName(0x411,7, "")
    # cica.appendSFNTName(0x411,8, "")
    # cica.appendSFNTName(0x411,9, "")
    # cica.appendSFNTName(0x411,10, "")
    # cica.appendSFNTName(0x411,11, "")
    # cica.appendSFNTName(0x411,12, "")
    cica.appendSFNTName(0x411,13, LICENSE)
    # cica.appendSFNTName(0x411,14, "")
    # cica.appendSFNTName(0x411,15, "")
    cica.appendSFNTName(0x411,16, _f.get('family'))
    cica.appendSFNTName(0x411,17, _f.get('style_name'))
    cica.appendSFNTName(0x409,0, COPYRIGHT)
    cica.appendSFNTName(0x409,1, _f.get('family'))
    cica.appendSFNTName(0x409,2, _f.get('style_name'))
    cica.appendSFNTName(0x409,3, VERSION + ";" + _f.get('family') + "-" + _f.get('style_name'))
    cica.appendSFNTName(0x409,4, _f.get('name'))
    cica.appendSFNTName(0x409,5, "Version " + VERSION)
    cica.appendSFNTName(0x409,6, _f.get('name'))
    # cica.appendSFNTName(0x409,7, "")
    # cica.appendSFNTName(0x409,8, "")
    # cica.appendSFNTName(0x409,9, "")
    # cica.appendSFNTName(0x409,10, "")
    # cica.appendSFNTName(0x409,11, "")
    # cica.appendSFNTName(0x409,12, "")
    cica.appendSFNTName(0x409,13, LICENSE)
    # cica.appendSFNTName(0x409,14, "")
    # cica.appendSFNTName(0x409,15, "")
    cica.appendSFNTName(0x409,16, _f.get('family'))
    cica.appendSFNTName(0x409,17, _f.get('style_name'))
    fontpath = DIST + '/%s' % _f.get('filename')
    cica.generate(fontpath)

    cica.close()
    ubuntu.close()
    # nerd.close()


def add_notoemoji(_f):
    notoemoji = fontforge.open(SOURCE + '/NotoEmoji-Regular.ttf')
    for g in notoemoji.glyphs():
        if g.isWorthOutputting and g.encoding > 0x04f9:
            g.transform((0.42,0,0,0.42,0,0))
            g = align_to_center(g)
            notoemoji.selection.select(g.encoding)
            notoemoji.copy()
            _f.selection.select(g.encoding)
            _f.paste()
    notoemoji.close()
    return _f

def add_devicons(_f):
    devicon = fontforge.open(SOURCE + '/devicon.ttf')
    current = 0xE160
    for g in devicon.glyphs():
        if g.isWorthOutputting:
            g.transform(psMat.compose(psMat.scale(0.8, 0.8), psMat.translate(0, -55)))
            g = align_to_center(g)
            devicon.selection.select(g.encoding)
            devicon.copy()
            _f.selection.select(current)
            _f.paste()
            current = current + 1
    devicon.close()
    gopher = fontforge.open(SOURCE + '/gopher.sfd')
    for g in gopher.glyphs():
        if g.isWorthOutputting:
            gopher.selection.select(0x40)
            gopher.copy()
            _f.selection.select(0xE160)
            _f.paste()
            g.transform(psMat.compose(psMat.scale(-1, 1), psMat.translate(g.width, 0)))
            gopher.copy()
            _f.selection.select(0xE161)
            _f.paste()
    gopher.close()
    return _f

def main():
    print('')
    print('### Generating Fusa started. ###')
    check_files()

    for _f in fonts:
        build_font(_f)

    print('### Succeeded ###')


if __name__ == '__main__':
    main()
