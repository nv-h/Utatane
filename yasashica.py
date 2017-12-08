#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import fontforge
import psMat
import os
import sys
import math

VERSION = '1.0.5'
FONTNAME = 'Yasashica'

# Ubuntu Mono
# 800 x 200 = 1000(Em)
# Win(Ascent, Descent)=(-170, -183)
# hhea(height, width)=(-170, 183)
LATIN_REGULAR_FONT = 'UbuntuMono-R.ttf'
LATIN_BOLD_FONT = 'UbuntuMono-B.ttf'

# 07やさしさゴシック
# 905 x 119 = 1024(Em)
# Win(Ascent, Descent)=(-24, 13)
# hhea(height, width)=(-24, 168)
JAPANESE_REGULAR_FONT = '07YasashisaGothic-R.ttf'
JAPANESE_BOLD_FONT = '07YasashisaGothic-B.ttf'

# 幅は日本語に合わせる(縮小より拡大のほうがきれいになりそうなので)
LATIN_WIDTH = 1000 # 未使用
JP_WIDTH = 1024
WIDTH = JP_WIDTH

# Ubuntu monoから拡大して、高さが1024になるようにしてみた(要は適当)
ASCENT = 819
DESCENT = 205
HEIGHT = ASCENT + DESCENT

LATIN_ASCENT = 800
LATIN_DESCENT = 200 # 未使用
JP_ASCENT = 905
JP_DESCENT = 119

# Italic時の傾き
SKEW_MAT = psMat.skew(0.25)
# 罫線(日本語の方を採用するやつ)
RULED_LINES = list(xrange(0x2500, 0x2600))

# 日本語フォントの縮小率
JP_A_RAT = (LATIN_ASCENT/JP_ASCENT) # 高さの比でいいはず
JP_REDUCTION_MAT = psMat.scale(JP_A_RAT, JP_A_RAT)
# descent位置がずれてもいいなら下記を使う。
JP_REDUCTION_FIX_MAT = psMat.translate(WIDTH*(1-JP_A_RAT)/2, -WIDTH*(1-JP_A_RAT)/2)
# descent位置が合わないと気持ち悪いので下記を使う。
JP_REDUCTION_FIX_MAT_NOHEIGHT = psMat.translate(WIDTH*(1-JP_A_RAT)/2, 0.0)

SOURCE = './sourceFonts'
DIST = './dist'
JP_TEMP = './tmp/jp_font.sfd'
EN_TEMP = './tmp/en_font.sfd'
LICENSE = open('./LICENSE.txt').read()
COPYRIGHT = open('./COPYRIGHT.txt').read()

# 出力をデコるときに使う文字
DECO_CHAR = '-'

DEBUG = True

fonts = [
    {
         'family': FONTNAME,
         'name': FONTNAME + '-Regular',
         'filename': FONTNAME + '-Regular.ttf',
         'weight': 400, # レギュラー体の標準値らしい
         'weight_name': 'Regular',
         'style_name': 'Regular',
         'latin': LATIN_REGULAR_FONT,
         'japanese': JAPANESE_REGULAR_FONT,
         'latin_weight_reduce': 0, # 0以外ではテストしていない
         'japanese_weight_add': 0, # 0以外では動かない
         'italic': False, # trueは変になる
    },
    {
        'family': FONTNAME,
        'name': FONTNAME + '-Bold',
        'filename': FONTNAME + '-Bold.ttf',
        'weight': 700, # ボールド体の標準値らしい
        'weight_name': 'Bold',
        'style_name': 'Bold',
        'latin': LATIN_BOLD_FONT,
        'japanese': JAPANESE_BOLD_FONT,
        'latin_weight_reduce': 0, # 0以外ではテストしていない
        'japanese_weight_add': 0, # 0以外では動かない
        'italic': False, # trueは変になる
    }
]

def deco_print(_str):
    print('')
    print(DECO_CHAR*len(_str))
    print(_str)
    print(DECO_CHAR*len(_str))


def indent_print(_str):
    print('')
    print('++ ' + _str)


def print_pdf(_font, _path):
    fontforge.printSetup('pdf-file')
    _font.printSample('fontdisplay', 20, '', _path)


def check_files():
    err = 0
    for f in fonts:
        if not os.path.isfile(SOURCE + '/{}'.format(f.get('latin'))):
            print('{} not exists.'.format(f))
            err = 1

        if not os.path.isfile(SOURCE + '/{}'.format(f.get('japanese'))):
            print('{} not exists.'.format(f))
            err = 1

    if err > 0:
        sys.exit(err)

def set_os2_values(_font, _info):
    _font.os2_weight = _info.get('weight')
    _font.os2_width = 5
    _font.os2_fstype = 0
    _font.os2_vendor = 'HSAI' # 好きな4文字
    _font.os2_version = 4
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

    """ panose definitions
    refer: [The 'OS/2' table](https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6OS2.html)

    * bFamilyType
        - 2:  Text and Display
    * bSerifStyle
        - 11: Normal Sans
    * bWeight
        - 5:  Book
        - 8:  Bold
    * bProportion
        - 9:  Monospaced
    * bContrast
        - 2:  None
    * bStrokeVariation
        - 2:  Gradual/Diagonal
    * bArmStyle
        - 3:  Straight Arms/Wedge
    * bLetterform
        - 2:  Normal/Contact
    * bMidline
        - 2:  Standard/Trimmed
    * bXHeight
        - 7:  Ducking/Large
    """
    style_name = _info.get('style_name')
    if style_name == 'Bold':
        _font.os2_panose = (2, 11, 8, 9, 2, 2, 3, 2, 2, 7)
    else:
        _font.os2_panose = (2, 11, 5, 9, 2, 2, 3, 2, 2, 7)

    return _font

def vertical_line_to_broken_bar(_font):
    _font.selection.select(0x00a6) # ¦ BROKEN BAR
    _font.copy()
    _font.selection.select(0x007c) # | VERTICAL LINE
    _font.paste()
    return _font

def emdash_to_broken_dash(_font):
    # FIXME: 点になる
    _font.selection.select(0x006c) # l LATIN SMALL LETTER L
    _font.copy()
    _font.selection.select(0x2014) # — EM DASH
    _font.pasteInto()
    _font.intersect()

    return _font

def zenkaku_space(_font):
    _font.selection.select(0x2610) # ☐ ballot box
    _font.copy()
    _font.selection.select(0x3000) # 　 IDEOGRAPHIC SPACE
    _font.paste()
    _font.selection.select(0x271a) # ✚ HEAVY GREEK CROSS
    _font.copy()
    _font.selection.select(0x3000) # 　 IDEOGRAPHIC SPACE
    _font.pasteInto()
    _font.intersect()

    return _font

def add_smalltriangle(_font):
    # FIXME: 動いてない？
    _font.selection.select(0x25bc) # ▼ BLACK DOWN-POINTING TRIANGLE
    _font.copy()
    _font.selection.select(0x25be) # ▾ BLACK DOWN-POINTING SMALL TRIANGLE
    _font.paste()
    _font.transform(psMat.compose(psMat.scale(0.64), psMat.translate(0, 68)))
    _font.copy()
    _font.selection.select(0x25b8) # ▸ BLACK RIGHT-POINTING SMALL TRIANGLE
    _font.paste()
    _font.transform(psMat.rotate(math.radians(90)))

    for g in _font.glyphs():
        if g.encoding == 0x25be or g.encoding == 0x25b8:
            g.width = WIDTH//2
            g.left_side_bearing = g.right_side_bearing = (g.left_side_bearing + g.right_side_bearing)/2
            g.width = WIDTH//2

    return _font


def set_height(_font):
    _font.selection.all()
    _font.em = HEIGHT
    _font.ascent = ASCENT
    _font.descent = DESCENT
    _font.selection.none()
    return _font


def post_process(_font):
    '''座標値などをいい感じに処理する。
    removeOverlap()を実行しないと文字が消えることがある。
    refer: http://www.rs.tus.ac.jp/yyusa/ricty/ricty_generator.sh
    '''
    indent_print('post processing ... (It takes a few minutes.)')

    _font.selection.all()
    _font.round()
    _font.removeOverlap()
    _font.round()
    _font.autoHint()
    _font.autoInstr()
    _font.selection.none()

    return _font


def modify_and_save_latin(_f, _savepath):
    deco_print('modify latin : {}'.format(_f.get('latin')))

    latin_font = fontforge.open(SOURCE + '/{}'.format(_f.get('latin')))
    latin_font = set_height(latin_font)

    for g in latin_font.glyphs():
        if not g.isWorthOutputting:
            # 不要っぽいやつは消しちゃう
            latin_font.selection.select(g)
            latin_font.clear()

        if _f.get('italic'):
            # FIXME: 動作確認未
            g.transform(SKEW_MAT)

        if _f.get('latin_weight_reduce') != 0:
            # FIXME: 動作確認未
            # g.changeWeight(_f.get('latin_weight_reduce'), 'auto', 0, 0, 'auto')
            g.stroke("circular", _f.get('latin_weight_reduce'), 'butt', 'round', 'removeexternal')

        if g.encoding in RULED_LINES:
            # 罫線とかは日本語のを使う
            latin_font.selection.select(g)
            latin_font.clear()
        elif g.encoding == 0x2026:
            # … HORIZONTAL ELLIPSIS (use jp font's)
            latin_font.selection.select(g)
            latin_font.clear()

    latin_font.save(_savepath)
    latin_font.close()


def modify_and_save_jp(_f, _savepath):
    deco_print('modify jp : {}'.format(_f.get('japanese')))

    jp_font = fontforge.open(SOURCE + '/{}'.format(_f.get('japanese')))

    # 日本語フォントをいじる処理は、マージ後に行うと機能しない
    # 設定が足りていないかもしれないが詳細不明。
    jp_font = zenkaku_space(jp_font)
    jp_font = add_smalltriangle(jp_font)

    jp_font = set_height(jp_font)

    for g in jp_font.glyphs():

        if _f.get('japanese_weight_add') != 0:
            '''
            FIXME: エラーになる(未調査)

            g.stroke("circular", _f.get('japanese_weight_add'), 'butt', 'round', 'removeinternal')
            -> TypeError: Bad stroke flag list, must consist of strings only

            g.stroke("circular", _f.get('japanese_weight_add'), 'butt', 'round', 'removeinternal')
            -> TypeError: Bad stroke flag list, must consist of strings only
            '''
            # g.changeWeight(_f.get('japanese_weight_add'), 'auto', 0, 0, 'auto')
            g.stroke("caligraphic", _f.get('japanese_weight_add'), _f.get('japanese_weight_add'), 45, 'removeinternal')
            # g.stroke("circular", _f.get('japanese_weight_add'), 'butt', 'round', 'removeinternal')

        # いい塩梅で縮小
        g.transform(JP_REDUCTION_MAT)
        # 縮小して左に寄った分と上に寄った分を復帰
        g.transform(JP_REDUCTION_FIX_MAT_NOHEIGHT)
        # 幅が等幅でないやつがいたら修正
        g.width = WIDTH if g.width > WIDTH//2 else WIDTH//2

        if _f.get('italic'):
            # FIXME: 動作確認未
            g.transform(SKEW_MAT)

    jp_font.save(_savepath)
    jp_font.close()


def appendAllSFNTName(_font, _lang_code, _f):
    _font.appendSFNTName(_lang_code, 0, COPYRIGHT)
    _font.appendSFNTName(_lang_code, 1, _f.get('family'))
    _font.appendSFNTName(_lang_code, 2, _f.get('style_name'))
    _font.appendSFNTName(_lang_code, 4, _f.get('name'))
    _font.appendSFNTName(_lang_code, 5, "Version " + VERSION)
    _font.appendSFNTName(_lang_code, 6, _f.get('family') + "-" + _f.get('weight_name'))
    _font.appendSFNTName(_lang_code, 13, LICENSE)
    _font.appendSFNTName(_lang_code, 16, _f.get('family'))
    _font.appendSFNTName(_lang_code, 17, _f.get('style_name'))

    return _font


def fix_AvgCharWidth(_src_ttf, _dst_ttf):
    '''AvgCharWidthがおかしくなるので、元のフォントの値に書き換える
    require: `sudo apt install fonttools`

    refer: https://ja.osdn.net/projects/mplus-fonts/lists/archive/dev/2011-July/000619.html
    '''
    import xml.etree.ElementTree as ET

    deco_print('fix AvgCharWidth: {} to {}'.format(_src_ttf, _dst_ttf))

    # 元のフォントからxAvgCharWidth読み出し
    src_root, _ = os.path.splitext(_src_ttf)
    os.system('ttx -t OS/2 ' + _src_ttf)
    src_tree = ET.parse(src_root + '.ttx')
    src_AvgCharWidth = src_tree.find('OS_2').find('xAvgCharWidth').get('value')

    # 作成したフォントへxAvgCharWidthを設定
    dst_root, _ = os.path.splitext(_dst_ttf)
    os.system('ttx -t OS/2 ' + _dst_ttf)
    dst_tree = ET.parse(dst_root + '.ttx')
    dst_tree.find('OS_2').find('xAvgCharWidth').set('value', '{}'.format(src_AvgCharWidth))
    dst_tree.write(dst_root + '.ttx', 'utf-8', True)

    # 変更したやつを反映
    os.system('ttx -m ' + _dst_ttf + ' ' + dst_root + '.ttx') # 同じフォント名があると#1が付加される

    # 後片付け
    os.remove(_dst_ttf)
    os.rename(dst_root + '#1.ttf', _dst_ttf)
    os.remove(src_root + '.ttx')
    os.remove(dst_root + '.ttx')


def build_font(_f):

    modify_and_save_latin(_f, EN_TEMP)
    modify_and_save_jp(_f, JP_TEMP)

    deco_print('merge modified {} and modified {}'.format(_f.get('latin'), _f.get('japanese')))

    target_font = fontforge.font()
    target_font = set_height(target_font)

    target_font.upos = 45
    target_font.fontname = _f.get('family')
    target_font.familyname = _f.get('family')
    target_font.fullname = _f.get('name')
    target_font.weight = _f.get('weight_name')

    target_font = set_os2_values(target_font, _f)

    target_font = appendAllSFNTName(target_font, 0x411, _f) # 0x411は日本語
    target_font = appendAllSFNTName(target_font, 0x409, _f) # 0x409は英語

    target_font.mergeFonts(EN_TEMP)
    if not DEBUG: os.remove(EN_TEMP)
    target_font.mergeFonts(JP_TEMP)
    if not DEBUG: os.remove(JP_TEMP)

    target_font = vertical_line_to_broken_bar(target_font)
    # target_font = emdash_to_broken_dash(target_font) # あまり必要性を感じないので削除
    # 全角をいじるのはマージ前に行う

    target_font = post_process(target_font)

    fontpath = DIST + '/{}'.format(_f.get('filename'))
    if DEBUG: print_pdf(target_font, fontpath + '.pdf')

    target_font.generate(fontpath)
    target_font.close()

    fix_AvgCharWidth(SOURCE + '/{}'.format(_f.get('japanese')), fontpath)

    deco_print('Generate {} completed.'.format(_f.get('name')))


def main():
    check_files()
    deco_print('Generating ' + FONTNAME + ' started.')

    for _f in fonts:
        build_font(_f)

    deco_print('Succeeded!!')


if __name__ == '__main__':
    main()
